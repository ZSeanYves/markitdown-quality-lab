#!/usr/bin/env python3
"""Evaluate a report-only rule-model cooperative gate over v1 hint rows."""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
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
    "candidate_label",
    "rule_support_score",
    "context_sanity_score",
    "conflict_penalty_score",
    "label_risk_penalty",
    "cooperative_score",
    "cooperative_threshold",
    "gate_action",
    "gate_status",
    "gate_reason",
]


LABEL_RISK = {
    "footer_header_noise": 0.10,
    "heading": 0.45,
    "keep_as_text": 0.35,
}


PROFILES = {
    "conservative": {
        "footer_header_noise": {
            "weights": (0.35, 0.40, 0.20, 1.00, 0.05),
            "rule_min": 0.45,
            "context_min": 0.40,
        },
        "heading": {
            "weights": (0.30, 0.35, 0.25, 1.00, 0.10),
            "rule_min": 0.55,
            "context_min": 0.45,
        },
        "keep_as_text": {
            "weights": (0.35, 0.30, 0.25, 1.00, 0.10),
            "rule_min": 0.45,
            "context_min": 0.35,
        },
    },
    "balanced": {
        "footer_header_noise": {
            "weights": (0.40, 0.32, 0.18, 0.95, 0.05),
            "rule_min": 0.35,
            "context_min": 0.30,
        },
        "heading": {
            "weights": (0.38, 0.30, 0.20, 0.95, 0.12),
            "rule_min": 0.45,
            "context_min": 0.35,
        },
        "keep_as_text": {
            "weights": (0.40, 0.25, 0.20, 0.95, 0.12),
            "rule_min": 0.35,
            "context_min": 0.30,
        },
    },
    "model_heavy": {
        "footer_header_noise": {
            "weights": (0.55, 0.20, 0.10, 0.85, 0.05),
            "rule_min": 0.20,
            "context_min": 0.20,
        },
        "heading": {
            "weights": (0.52, 0.18, 0.15, 0.85, 0.15),
            "rule_min": 0.25,
            "context_min": 0.20,
        },
        "keep_as_text": {
            "weights": (0.55, 0.15, 0.10, 0.85, 0.15),
            "rule_min": 0.20,
            "context_min": 0.20,
        },
    },
}


class CooperativeGateError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate a report-only rule-model cooperative gate."
    )
    parser.add_argument("--v1-hints-tsv", required=True, help="v1 hints TSV path.")
    parser.add_argument("--features", required=True, help="Feature TSV path.")
    parser.add_argument(
        "--adapter-rows",
        required=True,
        help="Adapter task_a_rows.tsv path.",
    )
    parser.add_argument("--output-report", required=True, help="Markdown report path.")
    parser.add_argument("--output-tsv", required=True, help="Output TSV path.")
    parser.add_argument(
        "--labels",
        default="footer_header_noise,heading,keep_as_text",
        help="Comma-separated allowed labels.",
    )
    parser.add_argument(
        "--model-confidence-threshold",
        type=float,
        default=0.95,
        help="Minimum model confidence required before scoring.",
    )
    parser.add_argument(
        "--cooperative-thresholds",
        default="0.80,0.85,0.90",
        help="Comma-separated cooperative score thresholds.",
    )
    parser.add_argument(
        "--weight-profile",
        default="conservative",
        choices=sorted(PROFILES),
        help="Weight profile to evaluate.",
    )
    return parser.parse_args()


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise CooperativeGateError(f"missing TSV: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def parse_list(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def parse_thresholds(raw: str) -> list[float]:
    values: list[float] = []
    for item in parse_list(raw):
        values.append(float(item))
    if not values:
        raise CooperativeGateError("no cooperative thresholds provided")
    return values


def as_bool(row: dict[str, str], key: str) -> bool:
    return row.get(key, "") in {"1", "1.0", "true", "True"}


def as_float(row: dict[str, str], key: str, default: float = 0.0) -> float:
    raw = row.get(key, "")
    if raw == "":
        return default
    return float(raw)


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def average(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def feature_lookup(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["sample_id"]: row for row in rows}


def adapter_lookup(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["sample_id"]: row for row in rows}


def heading_shape_support(row: dict[str, str]) -> bool:
    return any(
        [
            as_bool(row, "heading_like_short"),
            as_bool(row, "heading_like_gap_before"),
            as_bool(row, "heading_like_gap_after"),
            as_bool(row, "isolated_heading_like"),
            as_bool(row, "section_number_prefix"),
            as_bool(row, "starts_with_section_word"),
            as_bool(row, "title_case_short"),
            as_bool(row, "all_caps_short"),
        ]
    )


def list_conflict(row: dict[str, str]) -> bool:
    return any(
        [
            as_bool(row, "starts_bullet"),
            as_bool(row, "starts_numbered"),
            as_bool(row, "starts_with_alpha_marker"),
            as_bool(row, "starts_with_roman_marker"),
            as_bool(row, "starts_with_paren_marker"),
            as_float(row, "rich_list_marker_type") > 0.0,
            as_float(row, "list_marker_type") > 0.0,
            as_bool(row, "short_line_with_marker"),
            as_bool(row, "short_marker_line"),
        ]
    )


def table_conflict(row: dict[str, str]) -> bool:
    return any(
        [
            as_bool(row, "contains_table_hint"),
            as_bool(row, "contains_tabular_hint"),
            as_bool(row, "contains_table_delimiters"),
            as_bool(row, "caption_near_prev_wide"),
            as_bool(row, "caption_near_next_wide"),
        ]
    )


def caption_conflict(row: dict[str, str]) -> bool:
    return any(
        [
            as_bool(row, "contains_figure_hint"),
            as_bool(row, "contains_table_cue"),
            as_bool(row, "contains_figure_cue"),
            as_bool(row, "starts_with_caption_cue"),
            as_bool(row, "starts_with_table_cue"),
            as_bool(row, "starts_with_figure_cue"),
            as_bool(row, "caption_like_short"),
        ]
    )


def edge_position(row: dict[str, str]) -> bool:
    return any(
        [
            as_bool(row, "near_top"),
            as_bool(row, "near_bottom"),
            row.get("page_position_bucket_fine", "") in {"0", "1", "6", "7"},
            row.get("y_position_bucket", "") in {"0", "4"},
        ]
    )


def sentence_like_conflict(row: dict[str, str]) -> bool:
    return as_bool(row, "has_terminal_period") and as_float(row, "word_count") >= 8


def long_paragraph_conflict(row: dict[str, str]) -> bool:
    return any(
        [
            as_bool(row, "long_text"),
            as_float(row, "text_len") > 120,
            as_float(row, "word_count") > 20,
        ]
    )


def central_body_conflict(row: dict[str, str]) -> bool:
    return (
        not edge_position(row)
        and (
            as_bool(row, "center_band")
            or row.get("page_position_bucket_fine", "") in {"2", "3", "4", "5"}
        )
        and as_float(row, "word_count") >= 10
    )


REFERENCE_RE = re.compile(
    r"(\bS\.I\.\b|\bSchedule\b|\bSection\b|\bRegulation\b|\bArt(?:icle)?\b|\([0-9A-Za-z/]+\)|\bc\.\s*\d+)",
    re.IGNORECASE,
)


def reference_like_text(text: str) -> bool:
    return bool(REFERENCE_RE.search(text))


def footer_header_noise_scores(row: dict[str, str], text: str) -> tuple[float, float, float, bool, list[str]]:
    reasons: list[str] = []
    word_count = as_float(row, "word_count")
    text_len = as_float(row, "text_len")
    bbox_h = as_float(row, "bbox_h_norm")
    compact_height = 1.0 if bbox_h <= 0.04 else 0.6 if bbox_h <= 0.06 else 0.0
    compact_text = 1.0 if word_count <= 8 else 0.6 if word_count <= 20 else 0.0
    edge = 1.0 if edge_position(row) else 0.0
    page_hint = 1.0 if as_bool(row, "contains_page_hint") else 0.0
    rule_support = average([edge, compact_height, max(page_hint, compact_text)])

    not_body = 1.0 if not long_paragraph_conflict(row) else 0.0
    not_central = 1.0 if not central_body_conflict(row) else 0.0
    edge_ctx = 1.0 if edge_position(row) else 0.0
    context = average([not_body, not_central, edge_ctx])

    soft_penalty = 0.0
    if as_bool(row, "has_terminal_period") and word_count > 8:
        soft_penalty += 0.15
    if text_len > 100:
        soft_penalty += 0.10
    if not as_bool(row, "short_text"):
        soft_penalty += 0.05
    soft_penalty = clamp01(soft_penalty)

    hard_conflict = False
    if table_conflict(row):
        reasons.append("table_conflict")
        hard_conflict = True
    if caption_conflict(row):
        reasons.append("caption_conflict")
        hard_conflict = True
    if list_conflict(row):
        reasons.append("list_conflict")
        hard_conflict = True
    if central_body_conflict(row):
        reasons.append("central_body_conflict")
        hard_conflict = True
    if any(
        [
            as_bool(row, "heading_like_short"),
            as_bool(row, "isolated_heading_like"),
            as_bool(row, "section_number_prefix"),
            as_bool(row, "title_case_short"),
            as_bool(row, "all_caps_short"),
        ]
    ):
        reasons.append("heading_shape_conflict")
        hard_conflict = True
    if sentence_like_conflict(row) and not as_bool(row, "contains_page_hint") and not edge_position(row):
        reasons.append("sentence_like_body_conflict")
        hard_conflict = True

    return rule_support, context, soft_penalty, hard_conflict, reasons


def heading_scores(row: dict[str, str], text: str) -> tuple[float, float, float, bool, list[str]]:
    reasons: list[str] = []
    shape = 1.0 if heading_shape_support(row) else 0.0
    lexical = 1.0 if any(
        [
            as_bool(row, "section_number_prefix"),
            as_bool(row, "starts_with_section_word"),
            as_bool(row, "title_case_short"),
            as_bool(row, "all_caps_short"),
        ]
    ) else 0.0
    separation = 1.0 if any(
        [
            as_bool(row, "heading_like_gap_before"),
            as_bool(row, "heading_like_gap_after"),
            as_bool(row, "isolated_heading_like"),
        ]
    ) else 0.0
    no_period = 1.0 if as_bool(row, "no_terminal_period") else 0.0
    rule_support = average([shape, max(lexical, no_period), separation])

    reasonable_height = 1.0 if as_float(row, "bbox_h_norm") <= 0.08 else 0.4
    not_bottom = 1.0 if not as_bool(row, "near_bottom") else 0.3
    not_long = 1.0 if not long_paragraph_conflict(row) else 0.0
    context = average([reasonable_height, not_bottom, not_long])

    soft_penalty = 0.0
    if as_float(row, "word_count") > 12:
        soft_penalty += 0.10
    if not as_bool(row, "isolated_heading_like") and not as_bool(row, "heading_like_gap_before"):
        soft_penalty += 0.10
    if as_bool(row, "near_bottom"):
        soft_penalty += 0.10
    soft_penalty = clamp01(soft_penalty)

    hard_conflict = False
    if table_conflict(row):
        reasons.append("table_conflict")
        hard_conflict = True
    if caption_conflict(row):
        reasons.append("caption_conflict")
        hard_conflict = True
    if list_conflict(row):
        reasons.append("list_conflict")
        hard_conflict = True
    if as_bool(row, "contains_form_hint"):
        reasons.append("form_conflict")
        hard_conflict = True
    if long_paragraph_conflict(row):
        reasons.append("long_paragraph_conflict")
        hard_conflict = True
    if sentence_like_conflict(row) and not as_bool(row, "section_number_prefix"):
        reasons.append("terminal_period_conflict")
        hard_conflict = True

    return rule_support, context, soft_penalty, hard_conflict, reasons


def keep_as_text_scores(row: dict[str, str], text: str) -> tuple[float, float, float, bool, list[str]]:
    reasons: list[str] = []
    reference_support = 1.0 if (
        reference_like_text(text)
        or (as_float(row, "digit_ratio") >= 0.12 and as_float(row, "punct_ratio") >= 0.08)
    ) else 0.0
    form_support = 1.0 if any(
        [
            as_bool(row, "contains_form_hint"),
            as_bool(row, "contains_page_hint"),
        ]
    ) else 0.0
    compact_support = 1.0 if any(
        [
            as_bool(row, "very_short_text"),
            as_bool(row, "short_text"),
            as_bool(row, "near_bottom"),
        ]
    ) else 0.0
    rule_support = average([max(reference_support, form_support), compact_support, 1.0 if not heading_shape_support(row) else 0.0])

    edgeish = 1.0 if edge_position(row) else 0.3
    compact_height = 1.0 if as_float(row, "bbox_h_norm") <= 0.08 else 0.4
    not_clear_paragraph = 1.0 if not (long_paragraph_conflict(row) and sentence_like_conflict(row)) else 0.0
    context = average([edgeish, compact_height, not_clear_paragraph])

    soft_penalty = 0.0
    if as_bool(row, "long_text"):
        soft_penalty += 0.10
    if not as_bool(row, "near_bottom") and not as_bool(row, "very_short_text"):
        soft_penalty += 0.10
    if heading_shape_support(row):
        soft_penalty += 0.10
    soft_penalty = clamp01(soft_penalty)

    hard_conflict = False
    if table_conflict(row):
        reasons.append("table_conflict")
        hard_conflict = True
    if caption_conflict(row):
        reasons.append("caption_conflict")
        hard_conflict = True
    if list_conflict(row):
        reasons.append("list_conflict")
        hard_conflict = True
    if heading_shape_support(row) and not as_bool(row, "near_bottom"):
        reasons.append("heading_conflict")
        hard_conflict = True
    if long_paragraph_conflict(row) and sentence_like_conflict(row) and not (
        reference_like_text(text) or as_bool(row, "contains_form_hint") or as_bool(row, "near_bottom")
    ):
        reasons.append("paragraph_like_long_sentence_conflict")
        hard_conflict = True

    return rule_support, context, soft_penalty, hard_conflict, reasons


def score_label(label: str, row: dict[str, str], text: str) -> tuple[float, float, float, bool, list[str]]:
    if label == "footer_header_noise":
        return footer_header_noise_scores(row, text)
    if label == "heading":
        return heading_scores(row, text)
    if label == "keep_as_text":
        return keep_as_text_scores(row, text)
    return 0.0, 0.0, 1.0, True, ["label_not_allowed"]


def cooperative_score_for_label(
    label: str,
    confidence: float,
    rule_support: float,
    context_sanity: float,
    conflict_penalty: float,
    profile: str,
) -> float:
    w_model, w_rule, w_context, w_conflict, w_label_risk = PROFILES[profile][label]["weights"]
    label_risk = LABEL_RISK[label]
    return (
        w_model * confidence
        + w_rule * rule_support
        + w_context * context_sanity
        - w_conflict * conflict_penalty
        - w_label_risk * label_risk
    )


def evaluate_row(
    *,
    hint_row: dict[str, str],
    feature_row: dict[str, str],
    adapter_row: dict[str, str],
    allowed_labels: set[str],
    model_confidence_threshold: float,
    cooperative_threshold: float,
    profile: str,
) -> dict[str, str]:
    predicted = hint_row["predicted_label"]
    candidate_label = predicted if predicted in allowed_labels else ""
    confidence = as_float(hint_row, "confidence")
    text = adapter_row.get("text", hint_row.get("text", ""))

    if candidate_label == "":
        return build_output_row(
            hint_row,
            adapter_row,
            candidate_label="",
            rule_support=0.0,
            context_sanity=0.0,
            conflict_penalty=1.0,
            cooperative_score=0.0,
            threshold=cooperative_threshold,
            action="no_override",
            status="label_not_allowed",
            reason=f"label_not_allowed:{predicted}",
        )

    if confidence < model_confidence_threshold:
        return build_output_row(
            hint_row,
            adapter_row,
            candidate_label=candidate_label,
            rule_support=0.0,
            context_sanity=0.0,
            conflict_penalty=0.0,
            cooperative_score=0.0,
            threshold=cooperative_threshold,
            action="no_override",
            status="blocked_model_confidence",
            reason=f"confidence<{model_confidence_threshold:.2f}",
        )

    rule_support, context_sanity, conflict_penalty, hard_conflict, conflict_reasons = score_label(
        candidate_label, feature_row, text
    )
    profile_cfg = PROFILES[profile][candidate_label]

    if hard_conflict:
        return build_output_row(
            hint_row,
            adapter_row,
            candidate_label=candidate_label,
            rule_support=rule_support,
            context_sanity=context_sanity,
            conflict_penalty=1.0,
            cooperative_score=0.0,
            threshold=cooperative_threshold,
            action="report_only_conflict",
            status="blocked_hard_conflict",
            reason=";".join(conflict_reasons),
        )

    if rule_support < profile_cfg["rule_min"]:
        return build_output_row(
            hint_row,
            adapter_row,
            candidate_label=candidate_label,
            rule_support=rule_support,
            context_sanity=context_sanity,
            conflict_penalty=conflict_penalty,
            cooperative_score=0.0,
            threshold=cooperative_threshold,
            action="no_override",
            status="blocked_rule_support",
            reason=f"rule_support<{profile_cfg['rule_min']:.2f}",
        )

    if context_sanity < profile_cfg["context_min"]:
        return build_output_row(
            hint_row,
            adapter_row,
            candidate_label=candidate_label,
            rule_support=rule_support,
            context_sanity=context_sanity,
            conflict_penalty=conflict_penalty,
            cooperative_score=0.0,
            threshold=cooperative_threshold,
            action="no_override",
            status="blocked_context_sanity",
            reason=f"context_sanity<{profile_cfg['context_min']:.2f}",
        )

    score = cooperative_score_for_label(
        candidate_label,
        confidence,
        rule_support,
        context_sanity,
        conflict_penalty,
        profile,
    )
    if score < cooperative_threshold:
        return build_output_row(
            hint_row,
            adapter_row,
            candidate_label=candidate_label,
            rule_support=rule_support,
            context_sanity=context_sanity,
            conflict_penalty=conflict_penalty,
            cooperative_score=score,
            threshold=cooperative_threshold,
            action="no_override",
            status="blocked_cooperative_score",
            reason=f"cooperative_score<{cooperative_threshold:.2f}",
        )

    return build_output_row(
        hint_row,
        adapter_row,
        candidate_label=candidate_label,
        rule_support=rule_support,
        context_sanity=context_sanity,
        conflict_penalty=conflict_penalty,
        cooperative_score=score,
        threshold=cooperative_threshold,
        action="emit_hint",
        status="emit",
        reason=f"emit:{profile}",
    )


def build_output_row(
    hint_row: dict[str, str],
    adapter_row: dict[str, str],
    *,
    candidate_label: str,
    rule_support: float,
    context_sanity: float,
    conflict_penalty: float,
    cooperative_score: float,
    threshold: float,
    action: str,
    status: str,
    reason: str,
) -> dict[str, str]:
    predicted = hint_row["predicted_label"]
    label_risk = LABEL_RISK.get(predicted, 1.0)
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
        "candidate_label": candidate_label,
        "rule_support_score": f"{rule_support:.4f}",
        "context_sanity_score": f"{context_sanity:.4f}",
        "conflict_penalty_score": f"{conflict_penalty:.4f}",
        "label_risk_penalty": f"{label_risk:.4f}",
        "cooperative_score": f"{cooperative_score:.4f}",
        "cooperative_threshold": f"{threshold:.2f}",
        "gate_action": action,
        "gate_status": status,
        "gate_reason": reason,
    }


def macro_f1(per_label: list[dict[str, object]]) -> float:
    if not per_label:
        return 0.0
    return sum(float(item["f1"]) for item in per_label) / len(per_label)


def label_recommendation(label: str, precision: float, recall: float, coverage: float) -> str:
    if label == "footer_header_noise" and precision >= 0.99 and recall >= 0.45:
        return "ready_for_external_quality_dry_run"
    if label in {"heading", "keep_as_text"} and precision >= 0.97 and recall >= 0.25:
        return "needs_more_guard"
    return "deny_for_now"


def evaluate_threshold(rows: list[dict[str, str]]) -> dict[str, object]:
    total = len(rows)
    emitted = [row for row in rows if row["gate_status"] == "emit"]
    accuracy = (
        sum(1 for row in emitted if row["gold_label"] == row["predicted_label"]) / len(emitted)
        if emitted
        else 0.0
    )
    gold_totals: Counter[str] = Counter(row["gold_label"] for row in rows)
    predicted_labels = sorted(gold_totals)
    per_label = []
    for label in predicted_labels:
        tp = sum(1 for row in emitted if row["predicted_label"] == label and row["gold_label"] == label)
        fp = sum(1 for row in emitted if row["predicted_label"] == label and row["gold_label"] != label)
        fn = gold_totals[label] - tp
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / gold_totals[label] if gold_totals[label] else 0.0
        f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
        emitted_support = sum(1 for row in emitted if row["predicted_label"] == label)
        coverage = emitted_support / gold_totals[label] if gold_totals[label] else 0.0
        per_label.append(
            {
                "label": label,
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "coverage": coverage,
                "emitted_support": emitted_support,
                "gold_total": gold_totals[label],
                "recommendation": label_recommendation(label, precision, recall, coverage),
            }
        )
    blocked_counts: Counter[str] = Counter(row["gate_status"] for row in rows if row["gate_status"] != "emit")
    blocked_counts.update(
        Counter(f"reason:{row['gate_reason']}" for row in rows if row["gate_status"] != "emit")
    )
    wrong_pairs = Counter(
        f"{row['gold_label']} -> {row['predicted_label']}"
        for row in emitted
        if row["gold_label"] != row["predicted_label"]
    )
    return {
        "total_rows": total,
        "emitted_rows": len(emitted),
        "coverage": len(emitted) / total if total else 0.0,
        "accuracy": accuracy,
        "macro_f1": macro_f1(per_label),
        "per_label": per_label,
        "blocked_counts": blocked_counts,
        "wrong_pairs": sorted(wrong_pairs.items(), key=lambda item: (-item[1], item[0])),
        "wrong_emitted": sum(wrong_pairs.values()),
    }


def write_report(
    path: Path,
    *,
    profile: str,
    model_confidence_threshold: float,
    thresholds: list[float],
    results: dict[float, dict[str, object]],
) -> None:
    lines = [
        "# Cooperative Gate Eval",
        "",
        f"- profile: `{profile}`",
        f"- model confidence threshold: `{model_confidence_threshold:.2f}`",
        "",
    ]
    for threshold in thresholds:
        result = results[threshold]
        lines.extend(
            [
                f"## cooperative threshold >= {threshold:.2f}",
                f"- total rows: `{result['total_rows']}`",
                f"- emitted rows: `{result['emitted_rows']}`",
                f"- coverage: `{result['coverage']:.4f}`",
                f"- emitted accuracy: `{result['accuracy']:.4f}`",
                f"- emitted macro F1: `{result['macro_f1']:.4f}`",
                f"- wrong emitted count: `{result['wrong_emitted']}`",
                "- per-label emitted precision/recall/F1/coverage:",
            ]
        )
        for item in result["per_label"]:
            lines.append(
                f"  - `{item['label']}` p=`{float(item['precision']):.4f}` "
                f"r=`{float(item['recall']):.4f}` f1=`{float(item['f1']):.4f}` "
                f"emitted_support=`{int(item['emitted_support'])}` total_gold=`{int(item['gold_total'])}` "
                f"coverage=`{float(item['coverage']):.4f}` recommendation=`{item['recommendation']}`"
            )
        lines.append("- blocked counts:")
        for reason, count in sorted(result["blocked_counts"].items()):
            lines.append(f"  - `{reason}` count=`{count}`")
        lines.append("- top wrong emitted pairs:")
        if result["wrong_pairs"]:
            for pair, count in result["wrong_pairs"][:10]:
                lines.append(f"  - `{pair}` count=`{count}`")
        else:
            lines.append("  - none")
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    allowed_labels = set(parse_list(args.labels))
    thresholds = parse_thresholds(args.cooperative_thresholds)

    hint_rows = read_tsv(Path(args.v1_hints_tsv))
    feature_rows = read_tsv(Path(args.features))
    adapter_rows = read_tsv(Path(args.adapter_rows))
    feature_by_id = feature_lookup(feature_rows)
    adapter_by_id = adapter_lookup(adapter_rows)

    evaluated_rows: list[dict[str, str]] = []
    for hint_row in hint_rows:
        sid = hint_row["sample_id"]
        feature_row = feature_by_id.get(sid)
        adapter_row = adapter_by_id.get(sid)
        if feature_row is None:
            raise CooperativeGateError(f"missing feature row for sample_id={sid}")
        if adapter_row is None:
            raise CooperativeGateError(f"missing adapter row for sample_id={sid}")
        for threshold in thresholds:
            evaluated_rows.append(
                evaluate_row(
                    hint_row=hint_row,
                    feature_row=feature_row,
                    adapter_row=adapter_row,
                    allowed_labels=allowed_labels,
                    model_confidence_threshold=args.model_confidence_threshold,
                    cooperative_threshold=threshold,
                    profile=args.weight_profile,
                )
            )

    write_tsv(Path(args.output_tsv), evaluated_rows)
    results = {
        threshold: evaluate_threshold(
            [row for row in evaluated_rows if row["cooperative_threshold"] == f"{threshold:.2f}"]
        )
        for threshold in thresholds
    }
    write_report(
        Path(args.output_report),
        profile=args.weight_profile,
        model_confidence_threshold=args.model_confidence_threshold,
        thresholds=thresholds,
        results=results,
    )


if __name__ == "__main__":
    main()
