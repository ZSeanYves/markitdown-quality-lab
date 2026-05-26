#!/usr/bin/env python3

"""Local-only DocLayNet -> Task A adapter.

This script converts a local DocLayNet COCO annotations JSON into a normalized
Task A TSV. It never downloads data and only works with files already present
on disk.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


OUTPUT_FIELDS = [
    "sample_id",
    "source_dataset",
    "source_page_id",
    "source_region_id",
    "page_no",
    "bbox",
    "source_label",
    "target_label",
    "target_task",
    "text",
    "confidence",
    "split",
    "notes",
]

MAPPING_FIELDS = [
    "source_label",
    "source_label_description",
    "target_task",
    "target_label",
    "mapping_confidence",
    "use_for_training",
    "notes",
]

TEXT_KEYS = ("text", "content", "token", "value")
BBOX_KEYS = ("bbox", "box", "rect", "bounding_box")


class AdapterError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert local DocLayNet COCO annotations into Task A TSV."
    )
    parser.add_argument(
        "--annotations",
        required=True,
        help="Path to a local DocLayNet COCO annotations JSON file.",
    )
    parser.add_argument(
        "--text-cells-root",
        help="Optional root containing DocLayNet extra page JSON text cells.",
    )
    parser.add_argument(
        "--mapping",
        default=str(Path(__file__).with_name("doclaynet_mapping.tsv")),
        help="Path to doclaynet_mapping.tsv.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to the output TSV. Prefer .tmp or other local-only paths.",
    )
    parser.add_argument(
        "--split",
        default="unknown",
        help="Split label to write into the output rows, e.g. train/heldout/test/unknown.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        help="Optional limit on the number of image/page records to read.",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        help="Optional limit on emitted output rows.",
    )
    parser.add_argument(
        "--include-ignored",
        action="store_true",
        help="Include rows whose mapping is marked as ignored/reviewed out by default.",
    )
    return parser.parse_args()


def read_json(path: Path) -> Any:
    if not path.is_file():
        raise AdapterError(f"missing file: {path}")
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise AdapterError(f"invalid JSON in {path}: {exc}") from exc


def load_mapping(path: Path) -> dict[str, dict[str, str]]:
    if not path.is_file():
        raise AdapterError(f"mapping missing: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != MAPPING_FIELDS:
            raise AdapterError(
                f"unexpected mapping header in {path}: {reader.fieldnames!r}"
            )
        mapping: dict[str, dict[str, str]] = {}
        for row in reader:
            label = row["source_label"].strip()
            if not label:
                raise AdapterError(f"blank source_label in mapping: {path}")
            mapping[label] = {key: value.strip() for key, value in row.items()}
    if not mapping:
        raise AdapterError(f"mapping has no rows: {path}")
    return mapping


def load_annotations(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[int, str]]:
    data = read_json(path)
    if not isinstance(data, dict):
        raise AdapterError(f"annotations root must be an object: {path}")

    images = data.get("images")
    categories = data.get("categories")
    annotations = data.get("annotations")

    if not isinstance(images, list):
        raise AdapterError(f"annotations JSON missing list field 'images': {path}")
    if not isinstance(categories, list):
        raise AdapterError(f"annotations JSON missing list field 'categories': {path}")
    if not isinstance(annotations, list):
        raise AdapterError(
            f"annotations JSON missing list field 'annotations': {path}"
        )

    category_lookup: dict[int, str] = {}
    for category in categories:
        if not isinstance(category, dict):
            continue
        category_id = category.get("id")
        category_name = category.get("name")
        if isinstance(category_id, int) and isinstance(category_name, str):
            category_lookup[category_id] = category_name

    if not category_lookup:
        raise AdapterError(f"no usable categories found in {path}")

    return images, annotations, category_lookup


def should_skip_row(mapping_row: dict[str, str], include_ignored: bool) -> bool:
    if include_ignored:
        return False
    target_label = mapping_row["target_label"].strip().lower()
    use_for_training = mapping_row["use_for_training"].strip().lower()
    if target_label in {"ignore", "ignored"}:
        return True
    if use_for_training == "no" and target_label in {"uncertain", "unknown"}:
        return True
    return False


def format_bbox(bbox: Any) -> str:
    if not isinstance(bbox, list) or len(bbox) != 4:
        raise AdapterError(f"invalid bbox: {bbox!r}")
    try:
        values = [float(value) for value in bbox]
    except (TypeError, ValueError) as exc:
        raise AdapterError(f"invalid bbox values: {bbox!r}") from exc
    return ",".join(format_number(value) for value in values)


def format_number(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return f"{value:.6f}".rstrip("0").rstrip(".")


def normalize_bbox(raw: Any) -> tuple[float, float, float, float] | None:
    if isinstance(raw, list) and len(raw) == 4:
        try:
            values = tuple(float(value) for value in raw)
        except (TypeError, ValueError):
            return None
        return values
    if isinstance(raw, dict):
        if all(key in raw for key in ("x0", "y0", "x1", "y1")):
            try:
                x0 = float(raw["x0"])
                y0 = float(raw["y0"])
                x1 = float(raw["x1"])
                y1 = float(raw["y1"])
            except (TypeError, ValueError):
                return None
            return (x0, y0, x1 - x0, y1 - y0)
        if all(key in raw for key in ("left", "top", "width", "height")):
            try:
                return (
                    float(raw["left"]),
                    float(raw["top"]),
                    float(raw["width"]),
                    float(raw["height"]),
                )
            except (TypeError, ValueError):
                return None
        if all(key in raw for key in ("x", "y", "w", "h")):
            try:
                return (
                    float(raw["x"]),
                    float(raw["y"]),
                    float(raw["w"]),
                    float(raw["h"]),
                )
            except (TypeError, ValueError):
                return None
    return None


def bbox_overlap_ratio(region: tuple[float, float, float, float], cell: tuple[float, float, float, float]) -> float:
    rx, ry, rw, rh = region
    cx, cy, cw, ch = cell
    if rw <= 0 or rh <= 0 or cw <= 0 or ch <= 0:
        return 0.0
    rx2 = rx + rw
    ry2 = ry + rh
    cx2 = cx + cw
    cy2 = cy + ch

    ix0 = max(rx, cx)
    iy0 = max(ry, cy)
    ix1 = min(rx2, cx2)
    iy1 = min(ry2, cy2)

    if ix1 <= ix0 or iy1 <= iy0:
        return 0.0

    intersection = (ix1 - ix0) * (iy1 - iy0)
    cell_area = cw * ch
    if cell_area <= 0:
        return 0.0
    return intersection / cell_area


def extract_text_from_object(obj: dict[str, Any]) -> str | None:
    for key in TEXT_KEYS:
        value = obj.get(key)
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                return stripped
    return None


def collect_text_cells(payload: Any) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            text = extract_text_from_object(node)
            bbox = None
            for key in BBOX_KEYS:
                if key in node:
                    bbox = normalize_bbox(node[key])
                    if bbox is not None:
                        break
            if bbox is None:
                bbox = normalize_bbox(node)
            if text and bbox is not None:
                cells.append({"text": text, "bbox": bbox})
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for item in node:
                visit(item)

    visit(payload)
    cells.sort(key=lambda item: (item["bbox"][1], item["bbox"][0], item["text"]))
    return cells


def resolve_text_cells_path(root: Path | None, image_info: dict[str, Any]) -> Path | None:
    if root is None:
        return None
    candidates: list[Path] = []
    file_name = image_info.get("file_name")
    if isinstance(file_name, str) and file_name.strip():
        stem = Path(file_name).stem
        candidates.append(root / f"{stem}.json")
        candidates.append(root / "JSON" / f"{stem}.json")
    doc_name = image_info.get("doc_name")
    page_no = image_info.get("page_no")
    if isinstance(doc_name, str) and doc_name.strip() and page_no not in (None, ""):
        doc_stem = Path(doc_name).stem
        candidates.append(root / f"{doc_stem}_{page_no}.json")
        candidates.append(root / "JSON" / f"{doc_stem}_{page_no}.json")
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def recover_text(
    region_bbox: tuple[float, float, float, float],
    image_info: dict[str, Any],
    text_cells_root: Path | None,
) -> tuple[str, str]:
    page_json_path = resolve_text_cells_path(text_cells_root, image_info)
    if page_json_path is None:
        return "", "missing_text_cells"

    try:
        payload = read_json(page_json_path)
    except AdapterError:
        return "", "invalid_text_cells_json"

    cells = collect_text_cells(payload)
    if not cells:
        return "", "text_cells_unparsed"

    matches: list[str] = []
    for cell in cells:
        overlap = bbox_overlap_ratio(region_bbox, cell["bbox"])
        if overlap >= 0.2:
            matches.append(cell["text"])

    if not matches:
        return "", "text_cells_no_overlap_todo_bbox_alignment"

    return " ".join(matches), "text_cells_overlap_v1"


def build_rows(args: argparse.Namespace) -> list[dict[str, str]]:
    mapping = load_mapping(Path(args.mapping))
    images, annotations, category_lookup = load_annotations(Path(args.annotations))

    annotations_by_image: dict[int, list[dict[str, Any]]] = {}
    for annotation in annotations:
        if not isinstance(annotation, dict):
            continue
        image_id = annotation.get("image_id")
        if not isinstance(image_id, int):
            continue
        annotations_by_image.setdefault(image_id, []).append(annotation)

    rows: list[dict[str, str]] = []
    text_cells_root = Path(args.text_cells_root) if args.text_cells_root else None

    for page_index, image_info in enumerate(images):
        if args.max_pages is not None and page_index >= args.max_pages:
            break
        if not isinstance(image_info, dict):
            continue
        image_id = image_info.get("id")
        if not isinstance(image_id, int):
            continue

        page_annotations = annotations_by_image.get(image_id, [])
        for annotation in page_annotations:
            annotation_id = annotation.get("id")
            category_id = annotation.get("category_id")
            if not isinstance(annotation_id, int):
                raise AdapterError(f"annotation missing integer id on image {image_id}")
            if not isinstance(category_id, int):
                raise AdapterError(
                    f"annotation {annotation_id} missing integer category_id"
                )

            source_label = category_lookup.get(category_id)
            if source_label is None:
                raise AdapterError(
                    f"unknown category_id {category_id} on annotation {annotation_id}"
                )
            mapping_row = mapping.get(source_label)
            if mapping_row is None:
                raise AdapterError(
                    f"mapping missing for source label {source_label!r}"
                )
            if should_skip_row(mapping_row, args.include_ignored):
                continue

            raw_bbox = annotation.get("bbox")
            bbox = normalize_bbox(raw_bbox)
            if bbox is None:
                raise AdapterError(
                    f"annotation {annotation_id} has invalid bbox: {raw_bbox!r}"
                )
            text, text_note = recover_text(bbox, image_info, text_cells_root)

            notes = ["human_annotation_mapped_by_adapter"]
            mapping_notes = mapping_row.get("notes", "")
            if mapping_notes:
                notes.append(mapping_notes)
            use_for_training = mapping_row.get("use_for_training", "")
            if use_for_training and use_for_training.lower() != "yes":
                notes.append(f"use_for_training={use_for_training}")
            notes.append(text_note)

            page_id = image_info.get("file_name")
            if not isinstance(page_id, str) or not page_id.strip():
                page_id = str(image_id)
            page_no = image_info.get("page_no", "")
            if page_no is None:
                page_no = ""

            row = {
                "sample_id": f"doclaynet_{args.split}_{image_id}_{annotation_id}",
                "source_dataset": "doclaynet",
                "source_page_id": str(page_id),
                "source_region_id": str(annotation_id),
                "page_no": str(page_no),
                "bbox": ",".join(format_number(value) for value in bbox),
                "source_label": source_label,
                "target_label": mapping_row["target_label"],
                "target_task": mapping_row["target_task"],
                "text": text,
                "confidence": "1.0",
                "split": args.split,
                "notes": ";".join(notes),
            }
            rows.append(row)
            if args.max_rows is not None and len(rows) >= args.max_rows:
                return rows

    if not rows:
        raise AdapterError("no rows emitted")
    return rows


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    try:
        rows = build_rows(args)
        write_rows(Path(args.output), rows)
    except AdapterError as exc:
        print(f"error: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
