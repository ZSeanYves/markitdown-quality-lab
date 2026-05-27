#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import random
import time
import urllib.request
from urllib.error import HTTPError, URLError
import zipfile
from collections import Counter, defaultdict
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
MODEL_ROOT = SCRIPT_DIR.parent
DEFAULT_OUTPUT_ROOT = MODEL_ROOT / "local_only" / "datasets" / "doclaynet"
DEFAULT_MAPPING = MODEL_ROOT / "adapters" / "doclaynet_mapping.tsv"
CORE_URL = "https://codait-cos-dax.s3.us.cloud-object-storage.appdomain.cloud/dax-doclaynet/1.0.0/DocLayNet_core.zip"
EXTRA_URL = "https://codait-cos-dax.s3.us.cloud-object-storage.appdomain.cloud/dax-doclaynet/1.0.0/DocLayNet_extra.zip"
LICENSE_NAME = "CDLA-Permissive-1.0"

MAPPING_FIELDS = [
    "source_label",
    "source_label_description",
    "target_task",
    "target_label",
    "mapping_confidence",
    "use_for_training",
    "notes",
]

SUBSET_MANIFEST_FIELDS = [
    "subset_id",
    "official_split",
    "local_split",
    "selected_pages",
    "selected_annotations",
    "doc_categories",
    "target_labels",
    "annotations_json_path",
    "annotations_json_sha256",
    "text_cells_root",
    "text_cells_json_count",
    "core_url",
    "extra_url",
    "license",
    "notes",
]


class DownloadError(RuntimeError):
    pass


def urlopen_with_retry(
    request: urllib.request.Request,
    *,
    timeout: int,
    attempts: int = 5,
    backoff_seconds: float = 1.5,
):
    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return urllib.request.urlopen(request, timeout=timeout)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            last_exc = exc
            if attempt >= attempts:
                break
            sleep_seconds = backoff_seconds * attempt
            print(
                f"retrying urlopen attempt={attempt}/{attempts} "
                f"sleep={sleep_seconds:.1f}s url={request.full_url} error={exc}"
            )
            time.sleep(sleep_seconds)
    raise DownloadError(f"failed to open {request.full_url}: {last_exc}") from last_exc


class HTTPRangeReader(io.RawIOBase):
    def __init__(self, url: str) -> None:
        self.url = url
        self.pos = 0
        req = urllib.request.Request(url, method="HEAD")
        with urlopen_with_retry(req, timeout=60) as resp:
            self.length = int(resp.headers["Content-Length"])

    def seekable(self) -> bool:
        return True

    def readable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.pos

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        if whence == io.SEEK_SET:
            self.pos = offset
        elif whence == io.SEEK_CUR:
            self.pos += offset
        elif whence == io.SEEK_END:
            self.pos = self.length + offset
        else:
            raise ValueError(f"unsupported whence: {whence}")
        return self.pos

    def read(self, size: int = -1) -> bytes:
        if self.pos >= self.length:
            return b""
        if size is None or size < 0:
            end = self.length - 1
        else:
            end = min(self.length - 1, self.pos + size - 1)
        req = urllib.request.Request(
            self.url,
            headers={"Range": f"bytes={self.pos}-{end}"},
        )
        with urlopen_with_retry(req, timeout=120) as resp:
            data = resp.read()
        self.pos += len(data)
        return data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download a local-only DocLayNet subset without fetching the full dataset."
    )
    parser.add_argument("--subset-id", default="smoke50_v1")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--mapping", default=str(DEFAULT_MAPPING))
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--train-pages", type=int, default=30)
    parser.add_argument("--dev-pages", type=int, default=10)
    parser.add_argument("--heldout-pages", type=int, default=10)
    parser.add_argument("--core-url", default=CORE_URL)
    parser.add_argument("--extra-url", default=EXTRA_URL)
    parser.add_argument(
        "--skip-text-cells",
        action="store_true",
        help="Only extract subset COCO JSONs; skip extra JSON text cells.",
    )
    parser.add_argument(
        "--resume-existing",
        action="store_true",
        help="Reuse already extracted extra JSON files when rerunning the same subset_id.",
    )
    return parser.parse_args()


def read_json_bytes(payload: bytes, *, source: str) -> dict:
    try:
        data = json.loads(payload.decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise DownloadError(f"invalid JSON from {source}: {exc}") from exc
    if not isinstance(data, dict):
        raise DownloadError(f"expected JSON object from {source}")
    return data


def load_mapping(path: Path) -> dict[str, dict[str, str]]:
    if not path.is_file():
        raise DownloadError(f"missing mapping file: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != MAPPING_FIELDS:
            raise DownloadError(
                f"unexpected mapping header in {path}: {reader.fieldnames!r}"
            )
        out: dict[str, dict[str, str]] = {}
        for row in reader:
            out[row["source_label"]] = row
    if not out:
        raise DownloadError(f"mapping has no rows: {path}")
    return out


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def write_json(path: Path, payload: dict) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    path.write_bytes(raw + b"\n")
    return sha256_bytes(raw + b"\n")


def write_tsv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def mapped_labels_for_image(
    annotations: list[dict],
    category_lookup: dict[int, str],
    mapping: dict[str, dict[str, str]],
) -> set[str]:
    labels: set[str] = set()
    for annotation in annotations:
        category_id = annotation.get("category_id")
        if not isinstance(category_id, int):
            continue
        source_label = category_lookup.get(category_id)
        if source_label is None:
            continue
        mapping_row = mapping.get(source_label)
        if mapping_row is None:
            continue
        if mapping_row["use_for_training"].strip().lower() == "no":
            continue
        target_label = mapping_row["target_label"].strip()
        if not target_label:
            continue
        labels.add(target_label)
    return labels


def build_category_lookup(categories: list[dict]) -> dict[int, str]:
    out: dict[int, str] = {}
    for category in categories:
        if not isinstance(category, dict):
            continue
        category_id = category.get("id")
        name = category.get("name")
        if isinstance(category_id, int) and isinstance(name, str):
            out[category_id] = name
    if not out:
        raise DownloadError("no usable categories in DocLayNet JSON")
    return out


def select_images(
    images: list[dict],
    annotations_by_image: dict[int, list[dict]],
    category_lookup: dict[int, str],
    mapping: dict[str, dict[str, str]],
    count: int,
    seed: int,
) -> list[dict]:
    rng = random.Random(seed)
    candidates = [image for image in images if isinstance(image, dict) and isinstance(image.get("id"), int)]
    rng.shuffle(candidates)
    selected: list[dict] = []
    seen_ids: set[int] = set()
    label_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()

    while len(selected) < count and candidates:
        best_index = None
        best_score = None
        for index, image in enumerate(candidates):
            image_id = image["id"]
            if image_id in seen_ids:
                continue
            labels = mapped_labels_for_image(
                annotations_by_image.get(image_id, []),
                category_lookup,
                mapping,
            )
            if not labels:
                continue
            doc_category = str(image.get("doc_category", "unknown"))
            score = 0.0
            for label in sorted(labels):
                score += 1.0 / (1.0 + label_counts[label])
            score += 0.25 / (1.0 + category_counts[doc_category])
            score += min(len(annotations_by_image.get(image_id, [])), 25) * 0.001
            if best_score is None or score > best_score:
                best_score = score
                best_index = index
        if best_index is None:
            break
        image = candidates.pop(best_index)
        image_id = image["id"]
        selected.append(image)
        seen_ids.add(image_id)
        labels = mapped_labels_for_image(
            annotations_by_image.get(image_id, []),
            category_lookup,
            mapping,
        )
        label_counts.update(labels)
        category_counts[str(image.get("doc_category", "unknown"))] += 1

    return selected


def extract_subset_payload(
    split_name: str,
    split_payload: dict,
    selected_images: list[dict],
) -> tuple[dict, Counter[str], Counter[str], int]:
    image_ids = {image["id"] for image in selected_images}
    annotations = [
        annotation
        for annotation in split_payload["annotations"]
        if annotation.get("image_id") in image_ids
    ]
    doc_categories = Counter(str(image.get("doc_category", "unknown")) for image in selected_images)
    source_labels = Counter()
    category_lookup = build_category_lookup(split_payload["categories"])
    for annotation in annotations:
        category_id = annotation.get("category_id")
        if isinstance(category_id, int):
            source_labels[category_lookup.get(category_id, "unknown")] += 1
    subset_payload = {
        "images": selected_images,
        "annotations": annotations,
        "categories": split_payload["categories"],
        "licenses": split_payload.get("licenses", []),
        "info": split_payload.get("info", {}),
        "doclaynet_subset": {
            "split": split_name,
            "selected_pages": len(selected_images),
            "selected_annotations": len(annotations),
        },
    }
    return subset_payload, doc_categories, source_labels, len(annotations)


def open_remote_zip(url: str) -> zipfile.ZipFile:
    return zipfile.ZipFile(HTTPRangeReader(url))


def read_zip_entry(zf: zipfile.ZipFile, name: str) -> bytes:
    try:
        with zf.open(name, "r") as handle:
            return handle.read()
    except KeyError as exc:
        raise DownloadError(f"zip entry not found: {name}") from exc


def ensure_subset_root(root: Path, subset_id: str) -> Path:
    subset_root = root / subset_id
    subset_root.mkdir(parents=True, exist_ok=True)
    return subset_root


def main() -> int:
    args = parse_args()
    output_root = Path(args.output_root).expanduser()
    subset_root = ensure_subset_root(output_root, args.subset_id)
    mapping = load_mapping(Path(args.mapping))

    core_zip = open_remote_zip(args.core_url)
    extra_zip = None if args.skip_text_cells else open_remote_zip(args.extra_url)

    split_specs = [
        ("train", "train", args.train_pages),
        ("val", "dev", args.dev_pages),
        ("test", "heldout", args.heldout_pages),
    ]

    manifest_rows: list[dict[str, str]] = []
    selected_stems: set[str] = set()

    for official_split, local_split, page_limit in split_specs:
        if page_limit <= 0:
            continue
        entry_name = f"COCO/{official_split}.json"
        split_payload = read_json_bytes(
            read_zip_entry(core_zip, entry_name),
            source=entry_name,
        )
        images = split_payload.get("images")
        annotations = split_payload.get("annotations")
        categories = split_payload.get("categories")
        if not isinstance(images, list) or not isinstance(annotations, list) or not isinstance(categories, list):
            raise DownloadError(f"unexpected DocLayNet payload structure in {entry_name}")
        category_lookup = build_category_lookup(categories)
        annotations_by_image: dict[int, list[dict]] = defaultdict(list)
        for annotation in annotations:
            image_id = annotation.get("image_id")
            if isinstance(image_id, int):
                annotations_by_image[image_id].append(annotation)

        selected_images = select_images(
            images,
            annotations_by_image,
            category_lookup,
            mapping,
            page_limit,
            seed=args.seed + len(manifest_rows) * 17,
        )
        subset_payload, doc_categories, source_labels, annotation_count = extract_subset_payload(
            official_split,
            split_payload,
            selected_images,
        )
        output_json_path = subset_root / "core" / "COCO" / f"{official_split}.json"
        json_sha = write_json(output_json_path, subset_payload)
        print(
            f"selected split={official_split} local_split={local_split} "
            f"pages={len(selected_images)} annotations={annotation_count}"
        )

        for image in selected_images:
            file_name = image.get("file_name")
            if isinstance(file_name, str) and file_name.strip():
                selected_stems.add(Path(file_name).stem)

        manifest_rows.append(
            {
                "subset_id": args.subset_id,
                "official_split": official_split,
                "local_split": local_split,
                "selected_pages": str(len(selected_images)),
                "selected_annotations": str(annotation_count),
                "doc_categories": ";".join(
                    f"{name}:{doc_categories[name]}" for name in sorted(doc_categories)
                ),
                "target_labels": ";".join(
                    f"{name}:{source_labels[name]}" for name in sorted(source_labels)
                ),
                "annotations_json_path": str(output_json_path),
                "annotations_json_sha256": json_sha,
                "text_cells_root": str(subset_root / "extra" / "JSON"),
                "text_cells_json_count": "0",
                "core_url": args.core_url,
                "extra_url": args.extra_url,
                "license": LICENSE_NAME,
                "notes": "local-only DocLayNet subset extracted by range-aware zip reader",
            }
        )

    extracted_json_count = 0
    if extra_zip is not None and selected_stems:
        text_root = subset_root / "extra" / "JSON"
        text_root.mkdir(parents=True, exist_ok=True)
        for stem in sorted(selected_stems):
            entry_name = f"JSON/{stem}.json"
            target_path = text_root / f"{stem}.json"
            if args.resume_existing and target_path.is_file() and target_path.stat().st_size > 0:
                extracted_json_count += 1
            else:
                payload = read_zip_entry(extra_zip, entry_name)
                target_path.write_bytes(payload)
                extracted_json_count += 1
            if extracted_json_count % 25 == 0:
                print(
                    f"extracted text cells: {extracted_json_count}/{len(selected_stems)}"
                )
        for row in manifest_rows:
            row["text_cells_json_count"] = str(extracted_json_count)

    subset_manifest_path = output_root / "subset_manifest.tsv"
    write_tsv(subset_manifest_path, SUBSET_MANIFEST_FIELDS, manifest_rows)

    total_pages = sum(int(row["selected_pages"]) for row in manifest_rows)
    total_annotations = sum(int(row["selected_annotations"]) for row in manifest_rows)
    print(
        f"doclaynet subset ready: subset_id={args.subset_id} "
        f"pages={total_pages} annotations={total_annotations} "
        f"text_cells={extracted_json_count} root={subset_root}"
    )
    print(f"subset manifest: {subset_manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
