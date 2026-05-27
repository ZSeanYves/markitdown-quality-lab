#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import math
import re
from collections import Counter
from pathlib import Path


INPUT_FIELDS = [
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

OUTPUT_FIELDS = [
    "sample_id",
    "source_dataset",
    "source_page_id",
    "source_region_id",
    "page_no",
    "source_label",
    "target_label",
    "split",
    "text",
    "notes",
    "bbox_x_norm",
    "bbox_y_norm",
    "bbox_w_norm",
    "bbox_h_norm",
    "bbox_area_norm",
    "bbox_aspect_ratio",
    "near_top",
    "near_bottom",
    "near_left",
    "near_right",
    "center_band",
    "page_no_norm",
    "text_missing",
    "text_len",
    "word_count",
    "avg_word_len",
    "digit_ratio",
    "upper_ratio",
    "lower_ratio",
    "punct_ratio",
    "space_ratio",
    "alpha_ratio",
    "title_token_ratio",
    "all_caps_ratio",
    "starts_bullet",
    "starts_numbered",
    "ends_colon",
    "ends_period",
    "contains_url",
    "contains_email",
    "contains_pipe",
    "contains_tabular_hint",
    "contains_figure_hint",
    "contains_table_hint",
    "contains_form_hint",
    "contains_page_hint",
    "has_long_token",
    "has_many_digits",
    "short_text",
    "very_short_text",
    "long_text",
]

URL_RE = re.compile(r"https?://|www\.")
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
NUMBERED_RE = re.compile(r"^\s*(\(?\d+[\).]|[A-Za-z][\).])\s+")
BULLET_RE = re.compile(r"^\s*([\-*•]|[0-9]+\.)\s+")
WORD_RE = re.compile(r"[A-Za-z0-9]+")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build baseline numeric/text features from DocLayNet adapter rows."
    )
    parser.add_argument("--input", required=True, help="Adapter TSV path.")
    parser.add_argument("--output", required=True, help="Feature TSV path.")
    return parser.parse_args()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != INPUT_FIELDS:
            raise SystemExit(f"unexpected adapter header in {path}: {reader.fieldnames!r}")
        return list(reader)


def parse_bbox(raw: str) -> tuple[float, float, float, float]:
    parts = [part.strip() for part in raw.split(",")]
    if len(parts) != 4:
        raise SystemExit(f"invalid bbox: {raw!r}")
    return tuple(float(part) for part in parts)  # type: ignore[return-value]


def safe_ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def title_token_ratio(tokens: list[str]) -> float:
    if not tokens:
        return 0.0
    title_like = 0
    for token in tokens:
        if token[:1].isupper() and token[1:].islower():
            title_like += 1
    return title_like / len(tokens)


def all_caps_ratio(tokens: list[str]) -> float:
    if not tokens:
        return 0.0
    caps = 0
    for token in tokens:
        alpha = "".join(ch for ch in token if ch.isalpha())
        if alpha and alpha.isupper():
            caps += 1
    return caps / len(tokens)


def build_feature_row(row: dict[str, str]) -> dict[str, str]:
    text = row["text"]
    text_chars = list(text)
    bbox_x, bbox_y, bbox_w, bbox_h = parse_bbox(row["bbox"])
    norm = 1025.0
    tokens = WORD_RE.findall(text)
    alpha_chars = sum(1 for ch in text_chars if ch.isalpha())
    digit_chars = sum(1 for ch in text_chars if ch.isdigit())
    upper_chars = sum(1 for ch in text_chars if ch.isupper())
    lower_chars = sum(1 for ch in text_chars if ch.islower())
    punct_chars = sum(1 for ch in text_chars if not ch.isalnum() and not ch.isspace())
    space_chars = sum(1 for ch in text_chars if ch.isspace())
    length = len(text_chars)
    avg_word_len = safe_ratio(sum(len(token) for token in tokens), len(tokens))
    bbox_area = (bbox_w * bbox_h) / (norm * norm)
    aspect = safe_ratio(bbox_w, bbox_h if bbox_h else 1.0)
    page_no = float(row["page_no"] or 0)

    return {
        "sample_id": row["sample_id"],
        "source_dataset": row["source_dataset"],
        "source_page_id": row["source_page_id"],
        "source_region_id": row["source_region_id"],
        "page_no": row["page_no"],
        "source_label": row["source_label"],
        "target_label": row["target_label"],
        "split": row["split"],
        "text": text,
        "notes": row["notes"],
        "bbox_x_norm": f"{bbox_x / norm:.6f}",
        "bbox_y_norm": f"{bbox_y / norm:.6f}",
        "bbox_w_norm": f"{bbox_w / norm:.6f}",
        "bbox_h_norm": f"{bbox_h / norm:.6f}",
        "bbox_area_norm": f"{bbox_area:.6f}",
        "bbox_aspect_ratio": f"{aspect:.6f}",
        "near_top": "1" if bbox_y / norm <= 0.15 else "0",
        "near_bottom": "1" if (bbox_y + bbox_h) / norm >= 0.85 else "0",
        "near_left": "1" if bbox_x / norm <= 0.12 else "0",
        "near_right": "1" if (bbox_x + bbox_w) / norm >= 0.88 else "0",
        "center_band": "1" if 0.2 <= (bbox_x + bbox_w / 2.0) / norm <= 0.8 else "0",
        "page_no_norm": f"{min(page_no / 50.0, 1.0):.6f}",
        "text_missing": "1" if not text.strip() else "0",
        "text_len": str(length),
        "word_count": str(len(tokens)),
        "avg_word_len": f"{avg_word_len:.6f}",
        "digit_ratio": f"{safe_ratio(digit_chars, length):.6f}",
        "upper_ratio": f"{safe_ratio(upper_chars, length):.6f}",
        "lower_ratio": f"{safe_ratio(lower_chars, length):.6f}",
        "punct_ratio": f"{safe_ratio(punct_chars, length):.6f}",
        "space_ratio": f"{safe_ratio(space_chars, length):.6f}",
        "alpha_ratio": f"{safe_ratio(alpha_chars, length):.6f}",
        "title_token_ratio": f"{title_token_ratio(tokens):.6f}",
        "all_caps_ratio": f"{all_caps_ratio(tokens):.6f}",
        "starts_bullet": "1" if BULLET_RE.search(text) else "0",
        "starts_numbered": "1" if NUMBERED_RE.search(text) else "0",
        "ends_colon": "1" if text.rstrip().endswith(":") else "0",
        "ends_period": "1" if text.rstrip().endswith(".") else "0",
        "contains_url": "1" if URL_RE.search(text) else "0",
        "contains_email": "1" if EMAIL_RE.search(text) else "0",
        "contains_pipe": "1" if "|" in text else "0",
        "contains_tabular_hint": "1" if ("\t" in text or "  " in text) else "0",
        "contains_figure_hint": "1" if re.search(r"\b(fig(ure)?|plate)\b", text, re.I) else "0",
        "contains_table_hint": "1" if re.search(r"\btable\b", text, re.I) else "0",
        "contains_form_hint": "1" if re.search(r"\b(name|date|address|phone|id|signature)\b", text, re.I) else "0",
        "contains_page_hint": "1" if re.search(r"\bpage\b", text, re.I) else "0",
        "has_long_token": "1" if any(len(token) >= 18 for token in tokens) else "0",
        "has_many_digits": "1" if digit_chars >= 6 else "0",
        "short_text": "1" if len(tokens) <= 4 else "0",
        "very_short_text": "1" if len(tokens) <= 2 else "0",
        "long_text": "1" if len(tokens) >= 30 else "0",
    }


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    rows = read_rows(Path(args.input))
    if not rows:
        raise SystemExit("adapter TSV has no rows")
    feature_rows = [build_feature_row(row) for row in rows]
    write_rows(Path(args.output), feature_rows)
    label_counts = Counter(row["target_label"] for row in feature_rows)
    print(
        f"feature build complete: rows={len(feature_rows)} "
        f"labels={dict(sorted(label_counts.items()))} output={args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
