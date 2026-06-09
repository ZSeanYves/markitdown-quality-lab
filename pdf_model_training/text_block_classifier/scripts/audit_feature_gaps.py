#!/usr/bin/env python3
"""Audit text_block_classifier feature coverage for known error buckets.

This is a report-only script. It reads an existing feature TSV header and rows,
classifies feature columns into coarse families, and writes compact inventory
and gap reports for iteration 3 planning. It never writes a full feature dump.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


META_COLUMNS = {
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
    "feature_set",
}

INVENTORY_FIELDS = [
    "column",
    "column_group",
    "role",
    "availability",
    "non_empty_count",
    "non_zero_count",
    "example_values",
]

GAP_FIELDS = [
    "error_bucket",
    "desired_feature",
    "status",
    "available_columns",
    "derived_from_columns",
    "requires",
    "priority",
    "notes",
]


@dataclass(frozen=True)
class FeatureNeed:
    error_bucket: str
    desired_feature: str
    exact_columns: tuple[str, ...]
    weak_columns: tuple[str, ...]
    derived_from_columns: tuple[str, ...]
    missing_status: str
    requires: str
    priority: str
    notes: str


FEATURE_NEEDS = [
    FeatureNeed(
        "caption",
        "near_image_or_table_region",
        (),
        ("caption_near_prev_wide", "caption_near_next_wide", "prev_has_table_cue", "next_has_table_cue", "prev_has_figure_cue", "next_has_figure_cue"),
        (),
        "requires_parser_export",
        "parser visual/table/figure region geometry",
        "P0",
        "Current proxies only inspect neighboring text cues and wide boxes; they do not measure real visual-region proximity.",
    ),
    FeatureNeed(
        "caption",
        "distance_to_previous_visual_region",
        (),
        ("prev_gap_norm", "prev_gap_bucket", "caption_near_prev_wide"),
        (),
        "requires_parser_export",
        "parser visual/table/figure region geometry",
        "P0",
        "Gap to previous text block exists, but gap to previous visual/table region does not.",
    ),
    FeatureNeed(
        "caption",
        "distance_to_next_visual_region",
        (),
        ("next_gap_norm", "next_gap_bucket", "caption_near_next_wide"),
        (),
        "requires_parser_export",
        "parser visual/table/figure region geometry",
        "P1",
        "Gap to next text block exists, but gap to next visual/table region does not.",
    ),
    FeatureNeed(
        "caption",
        "caption_prefix_pattern",
        ("starts_with_caption_cue",),
        (),
        ("text",),
        "derived_from_existing_features",
        "text",
        "P0",
        "Existing cue column is available; an iter3 builder can expose a clearer pattern enum.",
    ),
    FeatureNeed(
        "caption",
        "short_text_with_caption_keywords",
        ("caption_like_short",),
        ("starts_with_caption_cue", "short_text", "very_short_text"),
        ("text", "token_count"),
        "derived_from_existing_features",
        "text/token_count",
        "P1",
        "Already represented by a binary cue, but can be made easier to audit.",
    ),
    FeatureNeed(
        "caption",
        "same_page_visual_density",
        (),
        (),
        (),
        "requires_parser_export",
        "parser page visual inventory",
        "P1",
        "No same-page image/table/figure count or density feature exists.",
    ),
    FeatureNeed(
        "caption",
        "below_image_or_table",
        (),
        ("caption_near_prev_wide", "prev_has_table_cue", "prev_has_figure_cue"),
        (),
        "requires_parser_export",
        "parser visual/table/figure region geometry",
        "P0",
        "Neighbor-text proxies cannot prove below/above relation to a visual object.",
    ),
    FeatureNeed(
        "caption",
        "above_table_or_figure",
        (),
        ("caption_near_next_wide", "next_has_table_cue", "next_has_figure_cue"),
        (),
        "requires_parser_export",
        "parser visual/table/figure region geometry",
        "P1",
        "Needs region-level geometry for actual table/figure positions.",
    ),
    FeatureNeed(
        "caption",
        "near_figure_region",
        (),
        ("prev_has_figure_cue", "next_has_figure_cue", "starts_with_figure_cue"),
        (),
        "requires_parser_export",
        "parser figure/image region geometry",
        "P0",
        "Text cue proxies exist; real figure/image region proximity is missing.",
    ),
    FeatureNeed(
        "caption",
        "near_table_region",
        (),
        ("prev_has_table_cue", "next_has_table_cue", "starts_with_table_cue"),
        (),
        "requires_parser_export",
        "parser table region geometry",
        "P0",
        "Text cue proxies exist; real table region proximity is missing.",
    ),
    FeatureNeed(
        "caption",
        "caption_keyword_score",
        (),
        ("starts_with_caption_cue", "contains_figure_hint", "contains_table_hint"),
        ("text",),
        "derived_from_existing_features",
        "text",
        "P2",
        "Can be derived now, but should not substitute for visual association.",
    ),
    FeatureNeed(
        "list_item_vs_paragraph",
        "bullet_or_number_prefix",
        ("starts_bullet", "starts_numbered", "list_marker_type", "rich_list_marker_type"),
        (),
        ("text",),
        "derived_from_existing_features",
        "text",
        "P0",
        "Basic and rich marker features are already present.",
    ),
    FeatureNeed(
        "list_item_vs_paragraph",
        "starts_with_enumeration_pattern",
        ("starts_with_alpha_marker", "starts_with_roman_marker", "starts_with_paren_marker"),
        ("rich_list_marker_type",),
        ("text",),
        "derived_from_existing_features",
        "text",
        "P0",
        "Existing marker signals can be collapsed into a clearer audit feature.",
    ),
    FeatureNeed(
        "list_item_vs_paragraph",
        "left_indent_bucket",
        ("left_indent_bucket", "indent_bucket_fine"),
        (),
        (),
        "not_available_yet",
        "",
        "P0",
        "Indent buckets are already available.",
    ),
    FeatureNeed(
        "list_item_vs_paragraph",
        "hanging_indent_score",
        (),
        ("continuation_indent_like", "continuation_after_marker_prev", "continuation_before_marker_next", "prev_same_left_band", "next_same_left_band"),
        (),
        "requires_parser_export",
        "parser line-level indent and wrapped-line structure",
        "P0",
        "Only weak block-neighbor proxies exist; true hanging indent needs line-level export.",
    ),
    FeatureNeed(
        "list_item_vs_paragraph",
        "continuation_line_count",
        (),
        ("continuation_after_marker_prev", "continuation_before_marker_next"),
        (),
        "requires_parser_export",
        "parser line grouping",
        "P0",
        "Current features identify neighbor continuation candidates, not line counts within a block.",
    ),
    FeatureNeed(
        "list_item_vs_paragraph",
        "sibling_indent_similarity",
        (),
        ("prev_same_left_band", "next_same_left_band", "prev_x_delta_bucket", "next_x_delta_bucket"),
        (),
        "requires_parser_export",
        "parser ordered sibling block/line context",
        "P1",
        "Neighbor x-delta proxies exist, but no sibling-set similarity feature exists.",
    ),
    FeatureNeed(
        "list_item_vs_paragraph",
        "wrapped_line_candidate",
        (),
        ("continuation_indent_like", "continuation_after_marker_prev", "continuation_before_marker_next"),
        (),
        "requires_parser_export",
        "parser line grouping",
        "P0",
        "Current weak proxies need actual line-break/merge evidence.",
    ),
    FeatureNeed(
        "list_item_vs_paragraph",
        "line_start_pattern",
        (),
        ("starts_bullet", "starts_numbered", "starts_with_alpha_marker", "starts_with_roman_marker", "starts_with_paren_marker"),
        ("text",),
        "derived_from_existing_features",
        "text",
        "P1",
        "Can be emitted as a compact enum for audit and retraining.",
    ),
    FeatureNeed(
        "list_item_vs_paragraph",
        "numbering_prefix_kind",
        ("rich_list_marker_type", "list_marker_type"),
        (),
        ("text",),
        "derived_from_existing_features",
        "text",
        "P0",
        "Present as numeric marker type; iter3 preview can expose a named enum.",
    ),
    FeatureNeed(
        "paragraph_list_item_vs_heading",
        "font_size_delta_to_page_median",
        (),
        (),
        (),
        "requires_parser_export",
        "parser font/span style export",
        "P0",
        "No font size columns exist in baseline_v3.",
    ),
    FeatureNeed(
        "paragraph_list_item_vs_heading",
        "font_size_delta_to_neighbor_body",
        (),
        (),
        (),
        "requires_parser_export",
        "parser font/span style plus neighbor body density",
        "P0",
        "No font columns and no body-density guard are available.",
    ),
    FeatureNeed(
        "paragraph_list_item_vs_heading",
        "short_text_score",
        ("short_text", "very_short_text", "token_count"),
        (),
        ("text", "token_count"),
        "derived_from_existing_features",
        "text/token_count",
        "P1",
        "Binary short flags exist; a score can make thresholding/audit easier.",
    ),
    FeatureNeed(
        "paragraph_list_item_vs_heading",
        "titlecase_ratio",
        ("title_token_ratio",),
        (),
        ("text",),
        "derived_from_existing_features",
        "text",
        "P1",
        "Existing title_token_ratio covers this.",
    ),
    FeatureNeed(
        "paragraph_list_item_vs_heading",
        "uppercase_ratio",
        ("upper_ratio", "all_caps_ratio"),
        (),
        ("text",),
        "derived_from_existing_features",
        "text",
        "P1",
        "Existing upper/all-caps ratios cover this.",
    ),
    FeatureNeed(
        "paragraph_list_item_vs_heading",
        "ends_with_period",
        ("ends_period", "has_terminal_period"),
        (),
        ("text",),
        "derived_from_existing_features",
        "text",
        "P1",
        "Existing period flags cover this.",
    ),
    FeatureNeed(
        "paragraph_list_item_vs_heading",
        "body_density_after",
        (),
        ("next_text_len_norm", "text_density_bucket", "next_overlap_ratio_bucket"),
        (),
        "requires_parser_export",
        "parser line/block density around candidate",
        "P0",
        "Current text-density proxy is local, not a robust body-density-after guard.",
    ),
    FeatureNeed(
        "paragraph_list_item_vs_heading",
        "section_number_prefix",
        ("section_number_prefix", "section_prefix_depth"),
        (),
        ("text",),
        "derived_from_existing_features",
        "text",
        "P1",
        "Available as binary and depth features.",
    ),
    FeatureNeed(
        "paragraph_list_item_vs_heading",
        "neighbor_body_density",
        (),
        ("prev_text_len_norm", "next_text_len_norm", "prev_width_ratio", "next_width_ratio"),
        (),
        "requires_parser_export",
        "parser neighbor paragraph density features",
        "P0",
        "Do not use predicted paragraph labels as input; derive density from parser text/geometry only.",
    ),
    FeatureNeed(
        "paragraph_list_item_vs_heading",
        "heading_shape_guard",
        (),
        ("heading_like_short", "heading_like_gap_before", "heading_like_gap_after", "isolated_heading_like"),
        ("text", "prev_gap_norm", "next_gap_norm"),
        "requires_parser_export",
        "font/style and body-density signals",
        "P0",
        "Current shape proxy lacks font delta and neighbor body-density checks.",
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit baseline feature coverage for iteration 3 planning."
    )
    parser.add_argument("--features", required=True, help="Existing feature TSV path.")
    parser.add_argument("--output-dir", required=True, help="Small report output directory.")
    parser.add_argument("--split", default="", help="Optional split filter for row statistics.")
    return parser.parse_args()


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = list(reader.fieldnames or [])
        return fieldnames, list(reader)


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


def column_group(column: str) -> str:
    if column in {"sample_id", "source_dataset", "source_page_id", "source_region_id", "source_label", "target_label", "split", "notes", "feature_set"}:
        return "provenance/source"
    if column == "text" or column.startswith(("text_", "word_", "token_", "avg_word", "digit_", "upper_", "lower_", "punct_", "space_", "alpha_", "title_", "all_caps", "short_text", "very_short_text", "long_text", "has_", "contains_", "ends_", "no_terminal", "has_terminal")):
        return "text shape"
    if column.startswith(("bbox_", "relative_", "area_", "width_height", "right_edge")):
        return "bbox geometry"
    if column.startswith(("near_", "page_", "center_band", "y_position")):
        return "page position"
    if "gap" in column or "indent" in column or "x_delta" in column or "center_delta" in column or "overlap" in column or "height_ratio" in column or "same_left" in column or "width_ratio" in column:
        return "spacing/indent"
    if column.startswith(("prev_", "next_", "continuation_")):
        return "neighbor context"
    if "caption" in column or "figure" in column or "table" in column:
        return "caption association"
    if "marker" in column or "bullet" in column or "number" in column or "paren" in column or "roman" in column:
        return "list pattern"
    if "heading" in column or "section" in column or "title" in column or "caps" in column:
        return "heading shape"
    if "font" in column or "style" in column:
        return "font/style"
    if "layout_recovery" in column or column.startswith("layout_"):
        return "layout_recovery hints"
    return "other"


def is_zeroish(raw: str) -> bool:
    if raw == "" or raw is None:
        return True
    try:
        return float(raw) == 0.0
    except ValueError:
        return raw.strip() in {"", "0", "false", "False", "none", "None"}


def example_values(rows: list[dict[str, str]], column: str, limit: int = 3) -> str:
    values: list[str] = []
    seen: set[str] = set()
    for row in rows:
        value = row.get(column, "")
        if value == "" or value in seen:
            continue
        seen.add(value)
        if len(value) > 40:
            value = value[:37] + "..."
        values.append(value)
        if len(values) >= limit:
            break
    return "|".join(values)


def build_inventory(fieldnames: list[str], rows: list[dict[str, str]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for column in fieldnames:
        group = column_group(column)
        role = "metadata" if column in META_COLUMNS else "model_feature"
        non_empty = sum(1 for row in rows if row.get(column, "") != "")
        non_zero = sum(1 for row in rows if not is_zeroish(row.get(column, "")))
        availability = "present" if non_empty else "empty"
        out.append(
            {
                "column": column,
                "column_group": group,
                "role": role,
                "availability": availability,
                "non_empty_count": non_empty,
                "non_zero_count": non_zero,
                "example_values": example_values(rows, column),
            }
        )
    return out


def present_columns(columns: set[str], candidates: tuple[str, ...]) -> list[str]:
    return [column for column in candidates if column in columns]


def gap_row(need: FeatureNeed, columns: set[str]) -> dict[str, object]:
    exact = present_columns(columns, need.exact_columns)
    weak = present_columns(columns, need.weak_columns)
    derived = present_columns(columns, need.derived_from_columns)
    if exact:
        status = "already_available"
        available = exact
        requires = ""
    elif weak:
        status = "weak"
        available = weak
        requires = need.requires
    elif derived:
        status = "derived_from_existing_features"
        available = []
        requires = need.requires
    else:
        status = need.missing_status
        available = []
        requires = need.requires
    return {
        "error_bucket": need.error_bucket,
        "desired_feature": need.desired_feature,
        "status": status,
        "available_columns": ",".join(available),
        "derived_from_columns": ",".join(derived),
        "requires": requires,
        "priority": need.priority,
        "notes": need.notes,
    }


def label_counts(rows: list[dict[str, str]], column: str) -> Counter[str]:
    return Counter(row.get(column, "") for row in rows if row.get(column, ""))


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(lines)


def write_report(
    path: Path,
    *,
    feature_path: Path,
    rows: list[dict[str, str]],
    fieldnames: list[str],
    inventory: list[dict[str, object]],
    gaps: list[dict[str, object]],
    split: str,
) -> None:
    group_counts = Counter(str(row["column_group"]) for row in inventory if row["role"] == "model_feature")
    status_counts = Counter(str(row["status"]) for row in gaps)
    source_counts = label_counts(rows, "source_label")
    target_counts = label_counts(rows, "target_label")
    lines: list[str] = []
    lines.append("# Feature Gap Report")
    lines.append("")
    lines.append("## Inputs")
    lines.append("")
    lines.append(f"- features: `{feature_path}`")
    lines.append(f"- split_filter: `{split or 'all'}`")
    lines.append(f"- rows_read: `{len(rows)}`")
    lines.append(f"- total_columns: `{len(fieldnames)}`")
    lines.append(f"- model_feature_columns: `{sum(1 for row in inventory if row['role'] == 'model_feature')}`")
    lines.append("")
    lines.append("## Feature Families")
    lines.append("")
    lines.append(
        markdown_table(
            ["feature_family", "columns"],
            [[group, count] for group, count in sorted(group_counts.items())],
        )
    )
    lines.append("")
    lines.append("## Gap Status")
    lines.append("")
    lines.append(
        markdown_table(
            ["status", "count"],
            [[status, count] for status, count in sorted(status_counts.items())],
        )
    )
    lines.append("")
    lines.append("## Label Distributions")
    lines.append("")
    lines.append("Source labels:")
    lines.append("")
    lines.append(
        markdown_table(
            ["source_label", "count"],
            [[label, count] for label, count in sorted(source_counts.items())],
        )
    )
    lines.append("")
    lines.append("Target labels:")
    lines.append("")
    lines.append(
        markdown_table(
            ["target_label", "count"],
            [[label, count] for label, count in sorted(target_counts.items())],
        )
    )
    lines.append("")
    lines.append("## Error Bucket Findings")
    lines.append("")
    for bucket in ["caption", "list_item_vs_paragraph", "paragraph_list_item_vs_heading"]:
        bucket_rows = [row for row in gaps if row["error_bucket"] == bucket]
        lines.append(f"### {bucket}")
        lines.append("")
        lines.append(
            markdown_table(
                ["feature", "status", "available", "requires", "priority"],
                [
                    [
                        row["desired_feature"],
                        row["status"],
                        row["available_columns"] or row["derived_from_columns"] or "",
                        row["requires"],
                        row["priority"],
                    ]
                    for row in bucket_rows
                ],
            )
        )
        lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("- Caption has text-cue and neighbor-text proxies, but no true image/table/figure proximity or visual density features.")
    lines.append("- List-item vs paragraph has marker and indent features, but still lacks reliable line-level continuation and hanging-indent counts.")
    lines.append("- Heading has text-shape and gap proxies, but no font-size delta or body-density guard.")
    lines.append("- No feature may consume convert/Markdown/IR output labels as input; next features must come from parser geometry/text/style or classifier probability only.")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_blocker(output_dir: Path, feature_path: Path, reason: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_tsv(
        output_dir / "feature_inventory.tsv",
        INVENTORY_FIELDS,
        [
            {
                "column": "",
                "column_group": "",
                "role": "",
                "availability": "blocked",
                "non_empty_count": 0,
                "non_zero_count": 0,
                "example_values": reason,
            }
        ],
    )
    write_tsv(
        output_dir / "feature_gap_matrix.tsv",
        GAP_FIELDS,
        [
            {
                "error_bucket": "all",
                "desired_feature": "",
                "status": "blocked",
                "available_columns": "",
                "derived_from_columns": "",
                "requires": str(feature_path),
                "priority": "P0",
                "notes": reason,
            }
        ],
    )
    (output_dir / "feature_gap_report.md").write_text(
        "# Feature Gap Report\n\n"
        "## Blocker\n\n"
        f"- features: `{feature_path}`\n"
        f"- reason: {reason}\n",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    feature_path = Path(args.features)
    output_dir = Path(args.output_dir)
    if not feature_path.is_file():
        write_blocker(output_dir, feature_path, "feature TSV not found")
        print(f"feature audit blocked: missing {feature_path}")
        return 0

    fieldnames, rows = read_rows(feature_path)
    if args.split:
        rows = [row for row in rows if row.get("split") == args.split]
    if not fieldnames:
        write_blocker(output_dir, feature_path, "feature TSV has no header")
        print(f"feature audit blocked: empty header {feature_path}")
        return 0
    if not rows:
        write_blocker(output_dir, feature_path, "feature TSV has no rows after split filter")
        print(f"feature audit blocked: no rows for split={args.split!r}")
        return 0

    inventory = build_inventory(fieldnames, rows)
    columns = set(fieldnames)
    gaps = [gap_row(need, columns) for need in FEATURE_NEEDS]
    output_dir.mkdir(parents=True, exist_ok=True)
    write_tsv(output_dir / "feature_inventory.tsv", INVENTORY_FIELDS, inventory)
    write_tsv(output_dir / "feature_gap_matrix.tsv", GAP_FIELDS, gaps)
    write_report(
        output_dir / "feature_gap_report.md",
        feature_path=feature_path,
        rows=rows,
        fieldnames=fieldnames,
        inventory=inventory,
        gaps=gaps,
        split=args.split,
    )
    print(
        "feature audit complete: "
        f"rows={len(rows)} columns={len(fieldnames)} output_dir={output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
