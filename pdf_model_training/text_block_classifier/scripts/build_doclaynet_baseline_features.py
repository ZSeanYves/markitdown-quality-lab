#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
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

BASE_OUTPUT_FIELDS = [
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

V2_EXTRA_FIELDS = [
    "feature_set",
    "token_count",
    "starts_with_alpha_marker",
    "no_terminal_period",
    "has_terminal_period",
    "title_case_short",
    "all_caps_short",
    "section_number_prefix",
    "contains_table_delimiters",
    "left_indent_bucket",
    "relative_x_bucket",
    "relative_width_bucket",
    "y_position_bucket",
    "short_line_with_marker",
    "continuation_indent_like",
    "list_marker_type",
    "prev_gap_norm",
    "next_gap_norm",
    "prev_same_left_band",
    "next_same_left_band",
    "prev_width_ratio",
    "next_width_ratio",
    "prev_text_len_norm",
    "next_text_len_norm",
    "prev_ends_period",
    "next_starts_marker",
]

V3_EXTRA_FIELDS = [
    "rich_list_marker_type",
    "starts_with_roman_marker",
    "starts_with_paren_marker",
    "starts_with_section_word",
    "section_prefix_depth",
    "marker_prefix_len_bucket",
    "indent_bucket_fine",
    "relative_height_bucket",
    "area_bucket",
    "width_height_ratio_bucket",
    "short_marker_line",
    "marker_followed_by_upper",
    "continuation_after_marker_prev",
    "continuation_before_marker_next",
    "heading_like_short",
    "heading_like_gap_before",
    "heading_like_gap_after",
    "isolated_heading_like",
    "page_position_bucket_fine",
    "right_edge_bucket",
    "text_density_bucket",
    "starts_with_caption_cue",
    "starts_with_table_cue",
    "starts_with_figure_cue",
    "caption_like_short",
    "prev_has_table_cue",
    "next_has_table_cue",
    "prev_has_figure_cue",
    "next_has_figure_cue",
    "caption_near_prev_wide",
    "caption_near_next_wide",
    "prev_gap_bucket",
    "next_gap_bucket",
    "prev_x_delta_bucket",
    "next_x_delta_bucket",
    "prev_center_delta_bucket",
    "next_center_delta_bucket",
    "prev_overlap_ratio_bucket",
    "next_overlap_ratio_bucket",
    "prev_height_ratio",
    "next_height_ratio",
]

URL_RE = re.compile(r"https?://|www\.")
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
NUMBERED_RE = re.compile(r"^\s*(\(?\d+[\).]|[A-Za-z][\).])\s+")
BULLET_RE = re.compile(r"^\s*([\-*•]|[0-9]+\.)\s+")
ALPHA_MARKER_RE = re.compile(r"^\s*[A-Za-z][\).]\s+")
SECTION_PREFIX_RE = re.compile(r"^\s*((\d+(\.\d+)+)|(\d+\.)|([A-Z]\.)|([IVXLC]+\.)|(\([A-Za-z0-9]+\)))\s+")
ROMAN_MARKER_RE = re.compile(r"^\s*(\(?[IVXLCMivxlcm]{1,8}[\).]|[IVXLCMivxlcm]{1,8}\.)\s+")
PAREN_MARKER_RE = re.compile(r"^\s*\([A-Za-z0-9IVXLCMivxlcm]{1,8}\)\s+")
SECTION_WORD_RE = re.compile(r"^\s*(section|article|chapter|part|annex|appendix|schedule)\b", re.I)
MARKER_PREFIX_RE = re.compile(
    r"^\s*([\-*•]|\(?\d+[\).]|[A-Za-z][\).]|\(?[IVXLCMivxlcm]{1,8}[\).]|\([A-Za-z0-9IVXLCMivxlcm]{1,8}\))\s+"
)
CAPTION_START_RE = re.compile(
    r"^\s*(fig(?:ure)?|fig\.|table|plate|chart|diagram|photo|image|illustration)\b[\s.:#-]*",
    re.I,
)
TABLE_START_RE = re.compile(r"^\s*table\b[\s.:#-]*", re.I)
FIGURE_START_RE = re.compile(
    r"^\s*(fig(?:ure)?|fig\.|plate|chart|diagram|photo|image|illustration)\b[\s.:#-]*",
    re.I,
)
WORD_RE = re.compile(r"[A-Za-z0-9]+")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build baseline numeric/text features from DocLayNet adapter rows."
    )
    parser.add_argument("--input", required=True, help="Adapter TSV path.")
    parser.add_argument("--output", required=True, help="Feature TSV path.")
    parser.add_argument(
        "--feature-set",
        default="baseline_v1",
        choices=["baseline_v1", "baseline_v2", "baseline_v3"],
        help="Feature set version to emit.",
    )
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


def parse_page_no(raw: str) -> float:
    try:
        return float(raw or 0)
    except ValueError:
        return 0.0


def list_marker_type(text: str) -> float:
    stripped = text.lstrip()
    if not stripped:
        return 0.0
    if re.match(r"^[-*•]\s+", stripped):
        return 1.0
    if re.match(r"^\(?\d+[\).]\s+", stripped):
        return 2.0
    if re.match(r"^[A-Za-z][\).]\s+", stripped):
        return 3.0
    return 0.0


def rich_list_marker_type(text: str) -> float:
    stripped = text.lstrip()
    if not stripped:
        return 0.0
    if re.match(r"^[-*•]\s+", stripped):
        return 1.0
    if re.match(r"^\(?\d+[\).]\s+", stripped):
        return 2.0
    if re.match(r"^[A-Za-z][\).]\s+", stripped):
        return 3.0
    if ROMAN_MARKER_RE.search(text):
        return 4.0
    if PAREN_MARKER_RE.search(text):
        return 5.0
    return 0.0


def bucket(value: float, thresholds: list[float]) -> float:
    for index, threshold in enumerate(thresholds):
        if value <= threshold:
            return float(index)
    return float(len(thresholds))


def region_sort_key(row: dict[str, str]) -> tuple[float, float, float]:
    x, y, _, _ = parse_bbox(row["bbox"])
    return (parse_page_no(row["page_no"]), y, x)


def page_neighbors(
    rows: list[dict[str, str]],
    index: int,
) -> tuple[dict[str, str] | None, dict[str, str] | None]:
    row = rows[index]
    prev_row = rows[index - 1] if index > 0 and rows[index - 1]["source_page_id"] == row["source_page_id"] else None
    next_row = rows[index + 1] if index + 1 < len(rows) and rows[index + 1]["source_page_id"] == row["source_page_id"] else None
    return prev_row, next_row


def text_has_table_cue(text: str) -> bool:
    return bool(
        re.search(r"\b(table|column|columns|row|rows|subtotal|total)\b", text, re.I)
        or "|" in text
        or "\t" in text
        or "  " in text
    )


def text_has_figure_cue(text: str) -> bool:
    return bool(re.search(r"\b(fig(?:ure)?|plate|diagram|chart|photo|image|illustration)\b", text, re.I))


def section_prefix_depth(text: str) -> float:
    match = SECTION_PREFIX_RE.search(text)
    if not match:
        return 0.0
    prefix = (match.group(1) or "").strip()
    if not prefix:
        return 0.0
    if prefix.startswith("(") and prefix.endswith(")"):
        return 1.0
    trimmed = prefix.rstrip(".")
    if not trimmed:
        return 1.0
    return float(trimmed.count(".") + 1)


def marker_prefix_len_bucket(text: str) -> float:
    match = MARKER_PREFIX_RE.search(text)
    if not match:
        return 0.0
    return bucket(float(len(match.group(1))), [1.0, 2.0, 4.0, 6.0, 8.0])


def marker_followed_by_upper(text: str) -> float:
    match = MARKER_PREFIX_RE.search(text)
    if not match:
        return 0.0
    rest = text[match.end() :].lstrip()
    return 1.0 if rest[:1].isupper() else 0.0


def bbox_gap_norm(current_bbox: tuple[float, float, float, float], other_bbox: tuple[float, float, float, float] | None) -> float:
    if other_bbox is None:
        return 1.0
    _, cy, _, ch = current_bbox
    _, oy, _, oh = other_bbox
    if oy >= cy:
        gap = max(0.0, oy - (cy + ch))
    else:
        gap = max(0.0, cy - (oy + oh))
    return min(gap / 1025.0, 1.0)


def bbox_x_delta_norm(current_bbox: tuple[float, float, float, float], other_bbox: tuple[float, float, float, float] | None) -> float:
    if other_bbox is None:
        return 1.0
    cx, _, _, _ = current_bbox
    ox, _, _, _ = other_bbox
    return min(abs(ox - cx) / 1025.0, 1.0)


def bbox_center_delta_norm(current_bbox: tuple[float, float, float, float], other_bbox: tuple[float, float, float, float] | None) -> float:
    if other_bbox is None:
        return 1.0
    cx, _, cw, _ = current_bbox
    ox, _, ow, _ = other_bbox
    current_center = cx + (cw / 2.0)
    other_center = ox + (ow / 2.0)
    return min(abs(other_center - current_center) / 1025.0, 1.0)


def bbox_overlap_ratio_x(current_bbox: tuple[float, float, float, float], other_bbox: tuple[float, float, float, float] | None) -> float:
    if other_bbox is None:
        return 0.0
    cx, _, cw, _ = current_bbox
    ox, _, ow, _ = other_bbox
    if cw <= 0 or ow <= 0:
        return 0.0
    current_right = cx + cw
    other_right = ox + ow
    overlap = min(current_right, other_right) - max(cx, ox)
    if overlap <= 0:
        return 0.0
    return overlap / min(cw, ow)


def bbox_height_ratio(current_bbox: tuple[float, float, float, float], other_bbox: tuple[float, float, float, float] | None) -> float:
    if other_bbox is None or current_bbox[3] <= 0:
        return 0.0
    return min(other_bbox[3] / current_bbox[3], 4.0)


def v2_context(
    rows: list[dict[str, str]],
    index: int,
) -> dict[str, str]:
    row = rows[index]
    bbox_x, bbox_y, bbox_w, bbox_h = parse_bbox(row["bbox"])
    norm = 1025.0
    prev_row, next_row = page_neighbors(rows, index)

    def prev_next_gap(current, other):
        if other is None:
            return 1.0
        ox, oy, ow, oh = parse_bbox(other["bbox"])
        gap = max(0.0, oy - (bbox_y + bbox_h)) if oy >= bbox_y else max(0.0, bbox_y - (oy + oh))
        return min(gap / norm, 1.0)

    def width_ratio(other):
        if other is None or bbox_w <= 0:
            return 0.0
        _, _, ow, _ = parse_bbox(other["bbox"])
        return ow / bbox_w

    def text_len_norm(other):
        if other is None:
            return 0.0
        return min(len(other["text"]) / 200.0, 1.0)

    def same_left_band(other):
        if other is None:
            return 0.0
        ox, _, _, _ = parse_bbox(other["bbox"])
        return 1.0 if abs(ox - bbox_x) / norm <= 0.03 else 0.0

    def ends_period(other):
        if other is None:
            return 0.0
        return 1.0 if other["text"].rstrip().endswith(".") else 0.0

    def starts_marker(other):
        if other is None:
            return 0.0
        return 1.0 if (BULLET_RE.search(other["text"]) or NUMBERED_RE.search(other["text"]) or ALPHA_MARKER_RE.search(other["text"])) else 0.0

    return {
        "prev_gap_norm": f"{prev_next_gap(row, prev_row):.6f}",
        "next_gap_norm": f"{prev_next_gap(row, next_row):.6f}",
        "prev_same_left_band": f"{same_left_band(prev_row):.0f}",
        "next_same_left_band": f"{same_left_band(next_row):.0f}",
        "prev_width_ratio": f"{width_ratio(prev_row):.6f}",
        "next_width_ratio": f"{width_ratio(next_row):.6f}",
        "prev_text_len_norm": f"{text_len_norm(prev_row):.6f}",
        "next_text_len_norm": f"{text_len_norm(next_row):.6f}",
        "prev_ends_period": f"{ends_period(prev_row):.0f}",
        "next_starts_marker": f"{starts_marker(next_row):.0f}",
    }


def v3_context(
    rows: list[dict[str, str]],
    index: int,
) -> dict[str, str]:
    row = rows[index]
    text = row["text"]
    tokens = WORD_RE.findall(text)
    bbox = parse_bbox(row["bbox"])
    bbox_x, bbox_y, bbox_w, bbox_h = bbox
    x_norm = bbox_x / 1025.0
    y_norm = bbox_y / 1025.0
    width_norm = bbox_w / 1025.0
    area_norm = (bbox_w * bbox_h) / (1025.0 * 1025.0)
    aspect = safe_ratio(bbox_w, bbox_h if bbox_h else 1.0)
    prev_row, next_row = page_neighbors(rows, index)
    prev_bbox = parse_bbox(prev_row["bbox"]) if prev_row is not None else None
    next_bbox = parse_bbox(next_row["bbox"]) if next_row is not None else None
    prev_gap = bbox_gap_norm(bbox, prev_bbox)
    next_gap = bbox_gap_norm(bbox, next_bbox)
    prev_width_ratio = safe_ratio(prev_bbox[2], bbox_w) if prev_bbox is not None and bbox_w > 0 else 0.0
    next_width_ratio = safe_ratio(next_bbox[2], bbox_w) if next_bbox is not None and bbox_w > 0 else 0.0
    rich_marker = rich_list_marker_type(text)
    current_starts_caption = 1.0 if CAPTION_START_RE.search(text) else 0.0
    current_starts_table = 1.0 if TABLE_START_RE.search(text) else 0.0
    current_starts_figure = 1.0 if FIGURE_START_RE.search(text) else 0.0
    prev_has_table_cue = 1.0 if prev_row is not None and text_has_table_cue(prev_row["text"]) else 0.0
    next_has_table_cue = 1.0 if next_row is not None and text_has_table_cue(next_row["text"]) else 0.0
    prev_has_figure_cue = 1.0 if prev_row is not None and text_has_figure_cue(prev_row["text"]) else 0.0
    next_has_figure_cue = 1.0 if next_row is not None and text_has_figure_cue(next_row["text"]) else 0.0
    current_short = len(tokens) <= 12
    no_terminal_period = text.strip() and not text.rstrip().endswith(".")
    heading_like_short = 1.0 if current_short and no_terminal_period and (float(title_token_ratio(tokens)) >= 0.5 or float(all_caps_ratio(tokens)) >= 0.5 or SECTION_WORD_RE.search(text) or SECTION_PREFIX_RE.search(text)) else 0.0
    continuation_after_marker_prev = 0.0
    if prev_row is not None and rich_list_marker_type(prev_row["text"]) > 0 and rich_marker == 0.0:
        prev_x = prev_bbox[0] / 1025.0 if prev_bbox is not None else 0.0
        if prev_gap <= 0.025 and x_norm >= max(prev_x - 0.01, 0.0):
            continuation_after_marker_prev = 1.0
    continuation_before_marker_next = 0.0
    if next_row is not None and rich_list_marker_type(next_row["text"]) > 0 and rich_marker == 0.0:
        next_x = next_bbox[0] / 1025.0 if next_bbox is not None else 0.0
        if next_gap <= 0.025 and x_norm <= next_x + 0.04:
            continuation_before_marker_next = 1.0

    # V3 still uses only text, geometry, and page order; no label-derived context.
    return {
        "rich_list_marker_type": f"{rich_marker:.0f}",
        "starts_with_roman_marker": "1" if ROMAN_MARKER_RE.search(text) else "0",
        "starts_with_paren_marker": "1" if PAREN_MARKER_RE.search(text) else "0",
        "starts_with_section_word": "1" if SECTION_WORD_RE.search(text) else "0",
        "section_prefix_depth": f"{section_prefix_depth(text):.0f}",
        "marker_prefix_len_bucket": f"{marker_prefix_len_bucket(text):.0f}",
        "indent_bucket_fine": f"{bucket(x_norm, [0.04, 0.08, 0.12, 0.18, 0.26, 0.36]):.0f}",
        "relative_height_bucket": f"{bucket(bbox_h / 1025.0, [0.015, 0.03, 0.05, 0.08, 0.12]):.0f}",
        "area_bucket": f"{bucket(area_norm, [0.003, 0.008, 0.015, 0.03, 0.06, 0.12]):.0f}",
        "width_height_ratio_bucket": f"{bucket(aspect, [1.5, 3.0, 6.0, 10.0, 16.0]):.0f}",
        "short_marker_line": "1" if len(tokens) <= 10 and rich_marker > 0 else "0",
        "marker_followed_by_upper": f"{marker_followed_by_upper(text):.0f}",
        "continuation_after_marker_prev": f"{continuation_after_marker_prev:.0f}",
        "continuation_before_marker_next": f"{continuation_before_marker_next:.0f}",
        "heading_like_short": f"{heading_like_short:.0f}",
        "heading_like_gap_before": "1" if prev_gap >= 0.012 else "0",
        "heading_like_gap_after": "1" if next_gap >= 0.012 else "0",
        "isolated_heading_like": "1" if heading_like_short and prev_gap >= 0.012 and next_gap >= 0.012 else "0",
        "page_position_bucket_fine": f"{bucket(y_norm, [0.05, 0.12, 0.22, 0.35, 0.50, 0.70, 0.88]):.0f}",
        "right_edge_bucket": f"{bucket((bbox_x + bbox_w) / 1025.0, [0.25, 0.45, 0.65, 0.82, 0.95]):.0f}",
        "text_density_bucket": f"{bucket(safe_ratio(len(tokens), max(width_norm, 0.05)), [2.0, 4.0, 6.0, 8.0, 12.0, 18.0]):.0f}",
        "starts_with_caption_cue": f"{current_starts_caption:.0f}",
        "starts_with_table_cue": f"{current_starts_table:.0f}",
        "starts_with_figure_cue": f"{current_starts_figure:.0f}",
        "caption_like_short": "1" if current_starts_caption and len(tokens) <= 18 else "0",
        "prev_has_table_cue": f"{prev_has_table_cue:.0f}",
        "next_has_table_cue": f"{next_has_table_cue:.0f}",
        "prev_has_figure_cue": f"{prev_has_figure_cue:.0f}",
        "next_has_figure_cue": f"{next_has_figure_cue:.0f}",
        "caption_near_prev_wide": "1" if prev_row is not None and prev_gap <= 0.03 and prev_width_ratio >= 1.1 and (current_starts_caption or prev_has_table_cue or prev_has_figure_cue) else "0",
        "caption_near_next_wide": "1" if next_row is not None and next_gap <= 0.03 and next_width_ratio >= 1.1 and (current_starts_caption or next_has_table_cue or next_has_figure_cue) else "0",
        "prev_gap_bucket": f"{bucket(prev_gap, [0.002, 0.006, 0.012, 0.025, 0.05, 0.10]):.0f}",
        "next_gap_bucket": f"{bucket(next_gap, [0.002, 0.006, 0.012, 0.025, 0.05, 0.10]):.0f}",
        "prev_x_delta_bucket": f"{bucket(bbox_x_delta_norm(bbox, prev_bbox), [0.005, 0.015, 0.03, 0.06, 0.12]):.0f}",
        "next_x_delta_bucket": f"{bucket(bbox_x_delta_norm(bbox, next_bbox), [0.005, 0.015, 0.03, 0.06, 0.12]):.0f}",
        "prev_center_delta_bucket": f"{bucket(bbox_center_delta_norm(bbox, prev_bbox), [0.01, 0.03, 0.06, 0.10, 0.16]):.0f}",
        "next_center_delta_bucket": f"{bucket(bbox_center_delta_norm(bbox, next_bbox), [0.01, 0.03, 0.06, 0.10, 0.16]):.0f}",
        "prev_overlap_ratio_bucket": f"{bucket(bbox_overlap_ratio_x(bbox, prev_bbox), [0.2, 0.4, 0.6, 0.8, 0.95]):.0f}",
        "next_overlap_ratio_bucket": f"{bucket(bbox_overlap_ratio_x(bbox, next_bbox), [0.2, 0.4, 0.6, 0.8, 0.95]):.0f}",
        "prev_height_ratio": f"{bbox_height_ratio(bbox, prev_bbox):.6f}",
        "next_height_ratio": f"{bbox_height_ratio(bbox, next_bbox):.6f}",
    }


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
    page_no = parse_page_no(row["page_no"])

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


def build_feature_rows(rows: list[dict[str, str]], feature_set: str) -> list[dict[str, str]]:
    ordered_rows = sorted(rows, key=region_sort_key)
    output_rows: list[dict[str, str]] = []
    for index, row in enumerate(ordered_rows):
        out = build_feature_row(row)
        if feature_set in {"baseline_v2", "baseline_v3"}:
            text = row["text"]
            tokens = WORD_RE.findall(text)
            bbox_x, bbox_y, bbox_w, bbox_h = parse_bbox(row["bbox"])
            base_width = bbox_w / 1025.0
            x_norm = bbox_x / 1025.0
            y_norm = bbox_y / 1025.0
            marker_type = list_marker_type(text)
            short_text = len(tokens) <= 6
            out.update(
                {
                    "feature_set": feature_set,
                    "token_count": str(len(tokens)),
                    "starts_with_alpha_marker": "1" if ALPHA_MARKER_RE.search(text) else "0",
                    "no_terminal_period": "1" if text.strip() and not text.rstrip().endswith(".") else "0",
                    "has_terminal_period": "1" if text.rstrip().endswith(".") else "0",
                    "title_case_short": "1" if short_text and float(out["title_token_ratio"]) >= 0.6 else "0",
                    "all_caps_short": "1" if short_text and float(out["all_caps_ratio"]) >= 0.6 else "0",
                    "section_number_prefix": "1" if SECTION_PREFIX_RE.search(text) else "0",
                    "contains_table_delimiters": "1" if ("|" in text or "\t" in text or "  " in text) else "0",
                    "left_indent_bucket": f"{bucket(x_norm, [0.08, 0.16, 0.24, 0.32]):.0f}",
                    "relative_x_bucket": f"{bucket(x_norm, [0.15, 0.30, 0.45, 0.60, 0.75]):.0f}",
                    "relative_width_bucket": f"{bucket(base_width, [0.20, 0.35, 0.50, 0.70, 0.85]):.0f}",
                    "y_position_bucket": f"{bucket(y_norm, [0.10, 0.25, 0.50, 0.75, 0.90]):.0f}",
                    "short_line_with_marker": "1" if short_text and marker_type > 0 else "0",
                    "continuation_indent_like": "1" if marker_type == 0.0 and x_norm >= 0.12 and len(tokens) >= 4 else "0",
                    "list_marker_type": f"{marker_type:.0f}",
                }
            )
            out.update(v2_context(ordered_rows, index))
        if feature_set == "baseline_v3":
            out.update(v3_context(ordered_rows, index))
        output_rows.append(out)
    return output_rows


def write_rows(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    rows = read_rows(Path(args.input))
    if not rows:
        raise SystemExit("adapter TSV has no rows")
    feature_rows = build_feature_rows(rows, args.feature_set)
    fieldnames = list(BASE_OUTPUT_FIELDS)
    if args.feature_set in {"baseline_v2", "baseline_v3"}:
        fieldnames.extend(V2_EXTRA_FIELDS)
    if args.feature_set == "baseline_v3":
        fieldnames.extend(V3_EXTRA_FIELDS)
    write_rows(Path(args.output), feature_rows, fieldnames)
    label_counts = Counter(row["target_label"] for row in feature_rows)
    print(
        f"feature build complete: feature_set={args.feature_set} rows={len(feature_rows)} "
        f"cols={len(fieldnames)} labels={dict(sorted(label_counts.items()))} output={args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
