#!/usr/bin/env python3
"""Build a small iter3 derived-feature schema and preview.

This script does not emit a full training feature TSV. It reads the existing
feature TSV, derives a compact set of candidate feature values from existing
text/shape columns, and writes only a schema plus a bounded preview for review.
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path


SCHEMA_FIELDS = [
    "feature_name",
    "status",
    "source_columns",
    "derivation",
    "notes",
]

PREVIEW_FIELDS = [
    "sample_id",
    "split",
    "source_label",
    "target_label",
    "text_preview",
    "caption_prefix_pattern",
    "text_length_bucket",
    "starts_with_enumeration_pattern",
    "enumeration_prefix_kind",
    "titlecase_ratio",
    "uppercase_ratio",
    "ends_with_period",
    "section_number_prefix",
    "short_text_score",
]

WORD_RE = re.compile(r"[A-Za-z0-9]+")
CAPTION_RE = re.compile(
    r"^\s*(fig(?:ure)?|fig\.|table|plate|chart|diagram|photo|image|illustration)\b[\s.:#-]*",
    re.I,
)
TABLE_RE = re.compile(r"^\s*table\b[\s.:#-]*", re.I)
FIGURE_RE = re.compile(
    r"^\s*(fig(?:ure)?|fig\.|plate|chart|diagram|photo|image|illustration)\b[\s.:#-]*",
    re.I,
)
BULLET_RE = re.compile(r"^\s*[-*•]\s+")
DECIMAL_RE = re.compile(r"^\s*\(?\d+[\).]\s+")
ALPHA_RE = re.compile(r"^\s*[A-Za-z][\).]\s+")
ROMAN_RE = re.compile(r"^\s*\(?[IVXLCMivxlcm]{1,8}[\).]\s+")
PAREN_RE = re.compile(r"^\s*\([A-Za-z0-9IVXLCMivxlcm]{1,8}\)\s+")
SECTION_PREFIX_RE = re.compile(
    r"^\s*((\d+(\.\d+)+)|(\d+\.)|([A-Z]\.)|([IVXLC]+\.)|(\([A-Za-z0-9]+\)))\s+"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write bounded iter3 derived-feature schema and preview."
    )
    parser.add_argument("--features", required=True, help="Existing feature TSV path.")
    parser.add_argument("--output-dir", required=True, help="Small report output directory.")
    parser.add_argument("--split", default="heldout", help="Split to preview; empty means all.")
    parser.add_argument("--max-preview", type=int, default=200)
    return parser.parse_args()


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or []), list(reader)


def write_tsv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def floatish(raw: str, default: float = 0.0) -> float:
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


def ratio_titlecase(tokens: list[str]) -> float:
    if not tokens:
        return 0.0
    title_like = 0
    for token in tokens:
        if token[:1].isupper() and token[1:].islower():
            title_like += 1
    return title_like / len(tokens)


def ratio_upper(text: str) -> float:
    alpha = [ch for ch in text if ch.isalpha()]
    if not alpha:
        return 0.0
    return sum(1 for ch in alpha if ch.isupper()) / len(alpha)


def caption_prefix_pattern(text: str) -> str:
    if not CAPTION_RE.search(text):
        return "none"
    if TABLE_RE.search(text):
        return "table"
    if FIGURE_RE.search(text):
        return "figure_or_image"
    return "caption_keyword"


def text_length_bucket(token_count: int) -> str:
    if token_count <= 2:
        return "very_short"
    if token_count <= 6:
        return "short"
    if token_count <= 18:
        return "medium"
    if token_count <= 40:
        return "long"
    return "very_long"


def enumeration_prefix_kind(text: str) -> str:
    if BULLET_RE.search(text):
        return "bullet"
    if DECIMAL_RE.search(text):
        return "decimal"
    if ROMAN_RE.search(text):
        return "roman"
    if PAREN_RE.search(text):
        return "paren"
    if ALPHA_RE.search(text):
        return "alpha"
    return "none"


def short_text_score(token_count: int) -> float:
    if token_count <= 2:
        return 1.0
    if token_count <= 6:
        return 0.75
    if token_count <= 12:
        return 0.40
    return 0.0


def derive(row: dict[str, str]) -> dict[str, object]:
    text = row.get("text", "")
    tokens = WORD_RE.findall(text)
    token_count = int(floatish(row.get("token_count", ""), float(len(tokens))))
    enum_kind = enumeration_prefix_kind(text)
    title_ratio = row.get("title_token_ratio", "")
    if title_ratio == "":
        title_ratio = f"{ratio_titlecase(tokens):.4f}"
    upper_ratio = row.get("upper_ratio", "")
    if upper_ratio == "":
        upper_ratio = f"{ratio_upper(text):.4f}"
    ends_period = row.get("ends_period", "")
    if ends_period == "":
        ends_period = "1" if text.rstrip().endswith(".") else "0"
    section_prefix = row.get("section_number_prefix", "")
    if section_prefix == "":
        section_prefix = "1" if SECTION_PREFIX_RE.search(text) else "0"
    return {
        "sample_id": row.get("sample_id", ""),
        "split": row.get("split", ""),
        "source_label": row.get("source_label", ""),
        "target_label": row.get("target_label", ""),
        "text_preview": " ".join(text.split())[:160],
        "caption_prefix_pattern": caption_prefix_pattern(text),
        "text_length_bucket": text_length_bucket(token_count),
        "starts_with_enumeration_pattern": "1" if enum_kind != "none" else "0",
        "enumeration_prefix_kind": enum_kind,
        "titlecase_ratio": f"{floatish(title_ratio):.4f}",
        "uppercase_ratio": f"{floatish(upper_ratio):.4f}",
        "ends_with_period": ends_period,
        "section_number_prefix": section_prefix,
        "short_text_score": f"{short_text_score(token_count):.2f}",
    }


def schema_rows(fieldnames: list[str]) -> list[dict[str, object]]:
    available = set(fieldnames)

    def status(required: list[str]) -> str:
        return "available" if all(column in available for column in required) else "blocked"

    return [
        {
            "feature_name": "caption_prefix_pattern",
            "status": status(["text"]),
            "source_columns": "text",
            "derivation": "regex enum over figure/table/caption prefixes",
            "notes": "Derived from text only; does not replace visual-region proximity.",
        },
        {
            "feature_name": "text_length_bucket",
            "status": "available" if "text" in available or "token_count" in available else "blocked",
            "source_columns": "token_count,text",
            "derivation": "very_short/short/medium/long/very_long by token count",
            "notes": "Useful for caption and heading audit.",
        },
        {
            "feature_name": "starts_with_enumeration_pattern",
            "status": status(["text"]),
            "source_columns": "text",
            "derivation": "boolean over bullet/decimal/alpha/roman/paren prefixes",
            "notes": "Clarifies existing marker signals.",
        },
        {
            "feature_name": "enumeration_prefix_kind",
            "status": status(["text"]),
            "source_columns": "text",
            "derivation": "named enum for bullet/decimal/alpha/roman/paren/none",
            "notes": "Candidate replacement for opaque numeric marker type.",
        },
        {
            "feature_name": "titlecase_ratio",
            "status": "available" if "title_token_ratio" in available or "text" in available else "blocked",
            "source_columns": "title_token_ratio,text",
            "derivation": "reuse title_token_ratio or recompute from text",
            "notes": "Heading guard input.",
        },
        {
            "feature_name": "uppercase_ratio",
            "status": "available" if "upper_ratio" in available or "text" in available else "blocked",
            "source_columns": "upper_ratio,text",
            "derivation": "reuse upper_ratio or recompute from text",
            "notes": "Heading guard input.",
        },
        {
            "feature_name": "ends_with_period",
            "status": "available" if "ends_period" in available or "text" in available else "blocked",
            "source_columns": "ends_period,text",
            "derivation": "reuse ends_period or inspect stripped text suffix",
            "notes": "Heading false-positive guard.",
        },
        {
            "feature_name": "section_number_prefix",
            "status": "available" if "section_number_prefix" in available or "text" in available else "blocked",
            "source_columns": "section_number_prefix,text",
            "derivation": "reuse section_number_prefix or regex over text",
            "notes": "Heading/list ambiguity guard.",
        },
        {
            "feature_name": "short_text_score",
            "status": "available" if "token_count" in available or "text" in available else "blocked",
            "source_columns": "token_count,text",
            "derivation": "score from token-count buckets",
            "notes": "More gradated than short_text/very_short_text booleans.",
        },
    ]


def select_preview_rows(
    rows: list[dict[str, str]],
    *,
    split: str,
    max_preview: int,
) -> list[dict[str, str]]:
    filtered = [row for row in rows if not split or row.get("split") == split]
    priority_labels = ["caption", "list_item", "paragraph", "heading"]
    by_label: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in filtered:
        label = row.get("target_label", "")
        if label in priority_labels:
            by_label[label].append(row)

    selected: list[dict[str, str]] = []
    per_label_target = max(1, max_preview // len(priority_labels))
    for label in priority_labels:
        selected.extend(by_label[label][:per_label_target])
    if len(selected) < max_preview:
        seen = {row.get("sample_id", "") for row in selected}
        for row in filtered:
            if row.get("sample_id", "") in seen:
                continue
            selected.append(row)
            if len(selected) >= max_preview:
                break
    return selected[:max_preview]


def write_blocker(output_dir: Path, feature_path: Path, reason: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_tsv(
        output_dir / "derived_feature_schema.tsv",
        SCHEMA_FIELDS,
        [
            {
                "feature_name": "",
                "status": "blocked",
                "source_columns": "",
                "derivation": "",
                "notes": f"{reason}: {feature_path}",
            }
        ],
    )
    write_tsv(output_dir / "derived_feature_preview.tsv", PREVIEW_FIELDS, [])


def main() -> int:
    args = parse_args()
    feature_path = Path(args.features)
    output_dir = Path(args.output_dir)
    if not feature_path.is_file():
        write_blocker(output_dir, feature_path, "feature TSV not found")
        print(f"derived feature preview blocked: missing {feature_path}")
        return 0

    fieldnames, rows = read_rows(feature_path)
    if not fieldnames:
        write_blocker(output_dir, feature_path, "feature TSV has no header")
        print(f"derived feature preview blocked: empty header {feature_path}")
        return 0
    schema = schema_rows(fieldnames)
    blocking = [row for row in schema if row["status"] == "blocked"]
    output_dir.mkdir(parents=True, exist_ok=True)
    write_tsv(output_dir / "derived_feature_schema.tsv", SCHEMA_FIELDS, schema)
    if blocking:
        write_tsv(output_dir / "derived_feature_preview.tsv", PREVIEW_FIELDS, [])
        print(f"derived feature preview blocked: {len(blocking)} schema rows unavailable")
        return 0

    preview_source = select_preview_rows(
        rows,
        split=args.split,
        max_preview=args.max_preview,
    )
    preview = [derive(row) for row in preview_source]
    write_tsv(output_dir / "derived_feature_preview.tsv", PREVIEW_FIELDS, preview)
    print(
        "derived feature preview complete: "
        f"rows={len(preview)} output_dir={output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
