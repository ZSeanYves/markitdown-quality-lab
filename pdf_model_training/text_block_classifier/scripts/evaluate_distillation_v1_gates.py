#!/usr/bin/env python3
"""Evaluate report-only distillation v1 gates over v0 hint exports.

This script does not retrain a model and does not mutate product output.
It only filters existing v0 hints through narrower label-specific guards.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


OUTPUT_FIELDS = [
    "sample_id",
    "split",
    "source_page_id",
    "source_region_id",
    "page_no",
    "bbox",
    "text",
    "gold_label",
    "predicted_label",
    "confidence",
    "v0_hint_status",
    "v1_label",
    "v1_action",
    "v1_status",
    "v1_reason",
]


class V1GateError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate report-only distillation v1 gates from v0 hint TSVs."
    )
    parser.add_argument("--hints-tsv", required=True, help="v0 hints TSV path.")
    parser.add_argument("--features", required=True, help="Feature TSV path.")
    parser.add_argument(
        "--adapter-rows",
        required=True,
        help="Adapter task_a_rows.tsv path for bbox/text cross-check.",
    )
    parser.add_argument("--output-report", required=True, help="Markdown report path.")
    parser.add_argument("--output-tsv", required=True, help="Filtered v1 TSV path.")
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.95,
        help="v0 threshold slice to evaluate, defaults to 0.95.",
    )
    return parser.parse_args()


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise V1GateError(f"missing TSV: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def str_bool(row: dict[str, str], key: str) -> bool:
    return row.get(key, "") in {"1", "1.0", "true", "True"}


def str_float(row: dict[str, str], key: str, default: float = 0.0) -> float:
    raw = row.get(key, "")
    if raw == "":
        return default
    return float(raw)


def feature_lookup(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["sample_id"]: row for row in rows}


def adapter_lookup(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["sample_id"]: row for row in rows}


def allowed_v1_label(predicted: str) -> bool:
    return predicted in {"footer_header_noise", "heading", "keep_as_text"}


def is_table_like_conflict(row: dict[str, str]) -> bool:
    return any(
        [
            str_bool(row, "contains_table_hint"),
            str_bool(row, "contains_tabular_hint"),
            str_bool(row, "contains_table_delimiters"),
            str_bool(row, "caption_near_prev_wide"),
            str_bool(row, "caption_near_next_wide"),
        ]
    )


def is_caption_conflict(row: dict[str, str]) -> bool:
    return any(
        [
            str_bool(row, "contains_figure_hint"),
            str_bool(row, "contains_table_cue"),
            str_bool(row, "contains_figure_cue"),
            str_bool(row, "starts_with_caption_cue"),
            str_bool(row, "starts_with_table_cue"),
            str_bool(row, "starts_with_figure_cue"),
            str_bool(row, "caption_like_short"),
        ]
    )


def is_list_conflict(row: dict[str, str]) -> bool:
    return any(
        [
            str_bool(row, "starts_bullet"),
            str_bool(row, "starts_numbered"),
            str_bool(row, "starts_with_alpha_marker"),
            str_bool(row, "starts_with_roman_marker"),
            str_bool(row, "starts_with_paren_marker"),
            str_float(row, "rich_list_marker_type") > 0.0,
            str_float(row, "list_marker_type") > 0.0,
            str_bool(row, "short_line_with_marker"),
            str_bool(row, "short_marker_line"),
        ]
    )


def heading_shape_support(row: dict[str, str]) -> bool:
    return any(
        [
            str_bool(row, "heading_like_short"),
            str_bool(row, "heading_like_gap_before"),
            str_bool(row, "heading_like_gap_after"),
            str_bool(row, "isolated_heading_like"),
            str_bool(row, "section_number_prefix"),
            str_bool(row, "starts_with_section_word"),
            str_bool(row, "title_case_short"),
            str_bool(row, "all_caps_short"),
        ]
    )


def keep_as_text_support(row: dict[str, str]) -> bool:
    digit_ratio = str_float(row, "digit_ratio")
    punct_ratio = str_float(row, "punct_ratio")
    return any(
        [
            str_bool(row, "contains_form_hint"),
            str_bool(row, "contains_page_hint"),
            str_bool(row, "near_bottom"),
            str_bool(row, "very_short_text"),
            str_bool(row, "short_text") and not str_bool(row, "heading_like_short"),
            digit_ratio >= 0.12 and punct_ratio >= 0.08,
        ]
    )


def footer_header_support(row: dict[str, str]) -> bool:
    return any(
        [
            str_bool(row, "near_top"),
            str_bool(row, "near_bottom"),
            str_bool(row, "contains_page_hint"),
            row.get("page_position_bucket_fine", "") in {"0", "1", "6", "7"},
            row.get("y_position_bucket", "") in {"0", "4"},
        ]
    )


def footer_header_sanity(row: dict[str, str]) -> tuple[bool, str]:
    if not footer_header_support(row):
        return False, "missing_edge_support"
    if str_bool(row, "long_text") or str_float(row, "word_count") > 28:
        return False, "too_body_like"
    if any(
        [
            str_bool(row, "heading_like_short"),
            str_bool(row, "isolated_heading_like"),
            str_bool(row, "section_number_prefix"),
            str_bool(row, "title_case_short"),
            str_bool(row, "all_caps_short"),
        ]
    ):
        return False, "heading_like_conflict"
    return True, "edge_support_ok"


def heading_sanity(row: dict[str, str]) -> tuple[bool, str]:
    if not heading_shape_support(row):
        return False, "missing_heading_shape"
    if str_bool(row, "long_text") or str_float(row, "text_len") > 120:
        return False, "too_long_for_heading"
    if str_bool(row, "has_terminal_period") and not str_bool(row, "section_number_prefix"):
        return False, "terminal_period_conflict"
    return True, "heading_shape_ok"


def keep_as_text_sanity(row: dict[str, str]) -> tuple[bool, str]:
    if not keep_as_text_support(row):
        return False, "missing_keep_as_text_support"
    if str_bool(row, "heading_like_short"):
        return False, "heading_like_conflict"
    return True, "keep_as_text_support_ok"


def conflict_reason(predicted: str, row: dict[str, str]) -> str | None:
    if predicted == "footer_header_noise":
        if is_table_like_conflict(row):
            return "table_like_conflict"
        if is_caption_conflict(row):
            return "caption_conflict"
        if is_list_conflict(row):
            return "list_conflict"
        return None
    if predicted == "heading":
        if is_table_like_conflict(row):
            return "table_like_conflict"
        if is_caption_conflict(row):
            return "caption_conflict"
        if is_list_conflict(row):
            return "list_conflict"
        if str_bool(row, "contains_form_hint"):
            return "form_conflict"
        return None
    if predicted == "keep_as_text":
        if is_table_like_conflict(row):
            return "table_like_conflict"
        if is_caption_conflict(row):
            return "caption_conflict"
        if is_list_conflict(row):
            return "list_conflict"
        if heading_shape_support(row) and not str_bool(row, "near_bottom"):
            return "heading_conflict"
        return None
    return "label_not_allowed"


def evaluate_v1_row(
    hint_row: dict[str, str],
    feature_row: dict[str, str],
    adapter_row: dict[str, str],
    threshold: float,
) -> dict[str, str]:
    predicted = hint_row["predicted_label"]
    confidence = str_float(hint_row, "confidence")
    status = "no_override"
    action = "no_override"
    label = ""
    reason = "default_no_override"

    if not allowed_v1_label(predicted):
        status = "blocked_label_not_allowed"
        reason = f"label_not_allowed:{predicted}"
    elif confidence < threshold:
        status = "blocked_low_confidence"
        reason = f"confidence<{threshold:.2f}"
    else:
        if predicted == "footer_header_noise":
            ok, why = footer_header_sanity(feature_row)
        elif predicted == "heading":
            ok, why = heading_sanity(feature_row)
        elif predicted == "keep_as_text":
            ok, why = keep_as_text_sanity(feature_row)
        else:
            ok, why = False, "label_not_allowed"

        if not ok:
            status = "blocked_sanity_guard"
            reason = why
        else:
            conflict = conflict_reason(predicted, feature_row)
            if conflict is not None:
                status = "blocked_conflict"
                reason = conflict
            else:
                status = "emit"
                action = "suggest_block_label"
                label = predicted
                reason = f"emit:{predicted}"

    return {
        "sample_id": hint_row["sample_id"],
        "split": hint_row["split"],
        "source_page_id": hint_row["source_page_id"],
        "source_region_id": hint_row["source_region_id"],
        "page_no": hint_row["page_no"],
        "bbox": adapter_row.get("bbox", hint_row.get("bbox", "")),
        "text": adapter_row.get("text", hint_row.get("text", "")),
        "gold_label": hint_row["gold_label"],
        "predicted_label": predicted,
        "confidence": hint_row["confidence"],
        "v0_hint_status": hint_row["hint_status"],
        "v1_label": label,
        "v1_action": action,
        "v1_status": status,
        "v1_reason": reason,
    }


def per_label_stats(rows: list[dict[str, str]], total_by_gold: Counter[str]) -> list[dict[str, object]]:
    emitted = [row for row in rows if row["v1_status"] == "emit"]
    gold_labels = sorted(total_by_gold)
    stats: list[dict[str, object]] = []
    for label in gold_labels:
        tp = sum(1 for row in emitted if row["gold_label"] == label and row["predicted_label"] == label)
        fp = sum(1 for row in emitted if row["predicted_label"] == label and row["gold_label"] != label)
        fn = total_by_gold[label] - tp
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / total_by_gold[label] if total_by_gold[label] else 0.0
        f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
        emitted_support = sum(1 for row in emitted if row["predicted_label"] == label)
        coverage = emitted_support / total_by_gold[label] if total_by_gold[label] else 0.0
        stats.append(
            {
                "label": label,
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "emitted_support": emitted_support,
                "gold_total": total_by_gold[label],
                "coverage": coverage,
            }
        )
    return stats


def macro_f1_from_stats(stats: list[dict[str, object]]) -> float:
    if not stats:
        return 0.0
    return sum(float(item["f1"]) for item in stats) / len(stats)


def label_recommendation(label: str, precision: float, recall: float, coverage: float) -> str:
    if label not in {"footer_header_noise", "heading", "keep_as_text"}:
        return "deny_for_now"
    if precision >= 0.98 and recall >= 0.35 and coverage >= 0.35:
        return "ready_for_external_quality_dry_run"
    if precision >= 0.95 and recall >= 0.15:
        return "needs_more_guard"
    return "deny_for_now"


def write_report(
    *,
    path: Path,
    threshold: float,
    total_rows: int,
    v0_rows: int,
    rows: list[dict[str, str]],
    stats: list[dict[str, object]],
    blocked_counts: Counter[str],
    wrong_pairs: list[tuple[str, int]],
) -> None:
    emitted = [row for row in rows if row["v1_status"] == "emit"]
    emitted_correct = [row for row in emitted if row["predicted_label"] == row["gold_label"]]
    emitted_accuracy = len(emitted_correct) / len(emitted) if emitted else 0.0
    macro_f1 = macro_f1_from_stats(stats)
    coverage = len(emitted) / total_rows if total_rows else 0.0
    lines = [
        "# Distillation v1 Gated Eval",
        "",
        f"- threshold: `{threshold:.2f}`",
        f"- total heldout rows: `{total_rows}`",
        f"- v0 emitted rows: `{v0_rows}`",
        f"- v1 emitted rows: `{len(emitted)}`",
        f"- v1 coverage: `{coverage:.4f}`",
        f"- v1 emitted accuracy: `{emitted_accuracy:.4f}`",
        f"- v1 emitted macro F1: `{macro_f1:.4f}`",
        f"- wrong emitted count: `{len(emitted) - len(emitted_correct)}`",
        "",
        "## Per-label emitted precision/recall/F1/coverage",
    ]
    for item in stats:
        lines.append(
            f"- `{item['label']}` p=`{float(item['precision']):.4f}` "
            f"r=`{float(item['recall']):.4f}` f1=`{float(item['f1']):.4f}` "
            f"emitted_support=`{int(item['emitted_support'])}` total_gold=`{int(item['gold_total'])}` "
            f"coverage=`{float(item['coverage']):.4f}` recommendation=`{label_recommendation(str(item['label']), float(item['precision']), float(item['recall']), float(item['coverage']))}`"
        )
    lines.extend(["", "## Blocked counts by reason"])
    for reason, count in sorted(blocked_counts.items()):
        lines.append(f"- `{reason}` count=`{count}`")
    lines.extend(["", "## Top wrong emitted pairs"])
    if wrong_pairs:
        for pair, count in wrong_pairs[:10]:
            lines.append(f"- `{pair}` count=`{count}`")
    else:
        lines.append("- none")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    threshold_text = f"{args.threshold:.2f}"
    hint_rows = read_tsv(Path(args.hints_tsv))
    feature_rows = read_tsv(Path(args.features))
    adapter_rows = read_tsv(Path(args.adapter_rows))

    filtered_hint_rows = [
        row
        for row in hint_rows
        if row["split"] == "heldout" and row["threshold"] == threshold_text
    ]
    if not filtered_hint_rows:
        raise V1GateError(f"no hint rows for threshold={threshold_text}")

    feature_by_id = feature_lookup(feature_rows)
    adapter_by_id = adapter_lookup(adapter_rows)
    evaluated_rows: list[dict[str, str]] = []
    total_by_gold: Counter[str] = Counter()
    blocked_counts: Counter[str] = Counter()
    wrong_pair_counts: Counter[str] = Counter()

    for hint_row in filtered_hint_rows:
        sid = hint_row["sample_id"]
        feature_row = feature_by_id.get(sid)
        adapter_row = adapter_by_id.get(sid)
        if feature_row is None:
            raise V1GateError(f"missing feature row for sample_id={sid}")
        if adapter_row is None:
            raise V1GateError(f"missing adapter row for sample_id={sid}")
        total_by_gold[hint_row["gold_label"]] += 1
        out = evaluate_v1_row(hint_row, feature_row, adapter_row, args.threshold)
        evaluated_rows.append(out)
        if out["v1_status"] != "emit":
            blocked_counts[out["v1_status"]] += 1
            blocked_counts[f"reason:{out['v1_reason']}"] += 1
        elif out["gold_label"] != out["predicted_label"]:
            wrong_pair_counts[f"{out['gold_label']} -> {out['predicted_label']}"] += 1

    stats = per_label_stats(evaluated_rows, total_by_gold)
    wrong_pairs = sorted(wrong_pair_counts.items(), key=lambda item: (-item[1], item[0]))
    write_tsv(Path(args.output_tsv), evaluated_rows)
    write_report(
        path=Path(args.output_report),
        threshold=args.threshold,
        total_rows=len(filtered_hint_rows),
        v0_rows=sum(1 for row in filtered_hint_rows if row["hint_status"] in {"emit", "wrong_prediction"}),
        rows=evaluated_rows,
        stats=stats,
        blocked_counts=blocked_counts,
        wrong_pairs=wrong_pairs,
    )


if __name__ == "__main__":
    main()
