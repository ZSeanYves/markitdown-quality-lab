#!/usr/bin/env python3

"""Local-only PubTables specialist adapter.

This adapter is intentionally narrow. It emits specialist rows for `table_like`
and optional weak caption probes without claiming page-wide gold semantics.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET


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


class AdapterError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert local-only PubTables specialist annotations into Task A TSV."
    )
    parser.add_argument(
        "--annotations",
        required=True,
        help="Path to local-only PubTables-style annotations JSON.",
    )
    parser.add_argument(
        "--words-json",
        help="Optional external words JSON. Current smoke path keeps words embedded in annotations.",
    )
    parser.add_argument(
        "--mapping",
        default=str(Path(__file__).with_name("pubtables_mapping.tsv")),
        help="Path to pubtables_mapping.tsv.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output TSV path. Prefer .tmp or local-only paths.",
    )
    parser.add_argument(
        "--split",
        default="unknown",
        help="Split label to write into the output rows.",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        help="Optional emitted-row limit.",
    )
    parser.add_argument(
        "--emit-caption-weak-probes",
        action="store_true",
        help="Emit weak caption probe rows when candidate annotations are available.",
    )
    parser.add_argument(
        "--source-id",
        default="pubtables_1m",
        help="Logical source identifier to record in output rows.",
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


def read_text_file(path: Path) -> str:
    if not path.is_file():
        raise AdapterError(f"missing file: {path}")
    return path.read_text(encoding="utf-8")


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


def format_number(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return f"{value:.6f}".rstrip("0").rstrip(".")


def normalize_bbox(raw: Any) -> tuple[float, float, float, float]:
    if not isinstance(raw, list) or len(raw) != 4:
        raise AdapterError(f"invalid bbox: {raw!r}")
    try:
        values = tuple(float(value) for value in raw)
    except (TypeError, ValueError) as exc:
        raise AdapterError(f"invalid bbox values: {raw!r}") from exc
    return values


def parse_xml_bbox(node: ET.Element) -> tuple[float, float, float, float]:
    xmin = float(node.findtext("xmin", default="0"))
    ymin = float(node.findtext("ymin", default="0"))
    xmax = float(node.findtext("xmax", default="0"))
    ymax = float(node.findtext("ymax", default="0"))
    return (xmin, ymin, xmax - xmin, ymax - ymin)


def bbox_to_string(bbox: tuple[float, float, float, float]) -> str:
    return ",".join(format_number(value) for value in bbox)


def join_table_words(table_obj: dict[str, Any]) -> str:
    words = table_obj.get("words", [])
    texts: list[str] = []
    if isinstance(words, list):
        for word in words:
            if isinstance(word, dict):
                text = word.get("text")
                if isinstance(text, str) and text.strip():
                    texts.append(text.strip())
    return " ".join(texts)


def row_from_mapping(
    *,
    sample_id: str,
    source_dataset: str,
    source_page_id: str,
    source_region_id: str,
    page_no: str,
    bbox: tuple[float, float, float, float],
    source_label: str,
    split: str,
    text: str,
    mapping_row: dict[str, str],
    extra_notes: list[str],
) -> dict[str, str]:
    notes = [mapping_row["notes"]] if mapping_row["notes"] else []
    notes.extend(extra_notes)
    return {
        "sample_id": sample_id,
        "source_dataset": source_dataset,
        "source_page_id": source_page_id,
        "source_region_id": source_region_id,
        "page_no": page_no,
        "bbox": bbox_to_string(bbox),
        "source_label": source_label,
        "target_label": mapping_row["target_label"],
        "target_task": mapping_row["target_task"],
        "text": text,
        "confidence": "1.0" if mapping_row["mapping_confidence"] == "high" else "0.35",
        "split": split,
        "notes": ";".join(notes),
    }


def build_rows(args: argparse.Namespace) -> list[dict[str, str]]:
    payload = read_json(Path(args.annotations))
    mapping = load_mapping(Path(args.mapping))
    if (
        isinstance(payload, dict)
        and payload.get("dataset") == "bsmock/pubtables-1m"
        and isinstance(payload.get("rows"), list)
    ):
        return build_rows_from_preview(payload, mapping, args)
    if not isinstance(payload, dict):
        raise AdapterError("annotations root must be an object")

    source_dataset = str(payload.get("source_dataset") or args.source_id)
    page_id = str(payload.get("page_id") or "unknown_page")
    page_no = str(payload.get("page_no") or "")
    tables = payload.get("tables")
    if not isinstance(tables, list) or not tables:
        raise AdapterError("annotations JSON must contain a non-empty 'tables' list")

    rows: list[dict[str, str]] = []
    for table in tables:
        if not isinstance(table, dict):
            continue
        table_id = str(table.get("id") or f"table_{len(rows)+1}")
        bbox = normalize_bbox(table.get("bbox"))
        table_text = join_table_words(table)
        rows.append(
            row_from_mapping(
                sample_id=f"{source_dataset}_{args.split}_{table_id}",
                source_dataset=source_dataset,
                source_page_id=page_id,
                source_region_id=table_id,
                page_no=page_no,
                bbox=bbox,
                source_label="table",
                split=args.split,
                text=table_text,
                mapping_row=mapping["table"],
                extra_notes=[
                    "source_role=specialist",
                    "never_gold_eval=true",
                    "specialist_scope=table_like",
                ],
            )
        )
        if args.max_rows is not None and len(rows) >= args.max_rows:
            return rows

        if args.emit_caption_weak_probes:
            for candidate in table.get("caption_candidates", []):
                if not isinstance(candidate, dict):
                    continue
                caption_id = str(candidate.get("id") or f"{table_id}_caption_probe")
                caption_text = str(candidate.get("text") or "").strip()
                if not caption_text:
                    continue
                caption_bbox = normalize_bbox(candidate.get("bbox"))
                rows.append(
                    row_from_mapping(
                        sample_id=f"{source_dataset}_{args.split}_{caption_id}",
                        source_dataset=source_dataset,
                        source_page_id=page_id,
                        source_region_id=caption_id,
                        page_no=page_no,
                        bbox=caption_bbox,
                        source_label="table_caption_probe",
                        split=args.split,
                        text=caption_text,
                        mapping_row=mapping["table_caption_probe"],
                        extra_notes=[
                            "source_role=specialist",
                            "weak_probe=true",
                            "never_gold_eval=true",
                            f"attached_table={table_id}",
                        ],
                    )
                )
                if args.max_rows is not None and len(rows) >= args.max_rows:
                    return rows

    if not rows:
        raise AdapterError("no rows emitted")
    return rows


def build_rows_from_preview(
    payload: dict[str, Any],
    mapping: dict[str, dict[str, str]],
    args: argparse.Namespace,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    preview_rows = payload.get("rows", [])
    for preview_item in preview_rows:
        if not isinstance(preview_item, dict):
            continue
        preview_row = preview_item.get("row")
        if not isinstance(preview_row, dict):
            continue
        page_key = str(preview_row.get("__key__") or "unknown_page")
        xml_blob = preview_row.get("xml")
        if not isinstance(xml_blob, list):
            continue
        xml_text = bytes(xml_blob).decode("utf-8", errors="replace")
        root = ET.fromstring(xml_text)
        for idx, obj in enumerate(root.findall("object"), start=1):
            source_label = (obj.findtext("name") or "").strip()
            if source_label != "table":
                continue
            bbox_node = obj.find("bndbox")
            if bbox_node is None:
                continue
            bbox = parse_xml_bbox(bbox_node)
            rows.append(
                row_from_mapping(
                    sample_id=f"{args.source_id}_{args.split}_{page_key}_{idx}",
                    source_dataset=args.source_id,
                    source_page_id=page_key,
                    source_region_id=f"{page_key}_table_{idx}",
                    page_no="",
                    bbox=bbox,
                    source_label="table",
                    split=args.split,
                    text="",
                    mapping_row=mapping["table"],
                    extra_notes=[
                        "source_role=specialist",
                        "tracked_preview_only=true",
                        "never_gold_eval=true",
                        "preview_origin=first_rows_train_json",
                    ],
                )
            )
            if args.max_rows is not None and len(rows) >= args.max_rows:
                return rows
    if not rows:
        raise AdapterError("no preview table rows emitted")
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
