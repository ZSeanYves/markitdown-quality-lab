#!/usr/bin/env python3
"""Evaluate high-confidence abstain gates for text_block_classifier predictions.

This script does not train a model. It reads an existing prediction TSV,
filters to a split such as heldout, sweeps confidence thresholds, and writes
small review reports for runtime-eligible high-confidence hints.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

from sklearn.metrics import accuracy_score, precision_recall_fscore_support


RUNTIME_ELIGIBLE_LABELS = [
    "heading",
    "paragraph",
    "caption",
    "table_like",
    "list_item",
    "footer_header_noise",
    "page_number_noise",
    "keep_as_text",
    "uncertain",
]

REPORT_ONLY_LABELS = [
    "form_row",
    "link_text",
    "code_like",
    "separator",
    "footnote_like",
]

LABEL_ORDER = RUNTIME_ELIGIBLE_LABELS + REPORT_ONLY_LABELS

GATE_SWEEP_FIELDS = [
    "split",
    "threshold",
    "margin_threshold",
    "total_count",
    "overall_accuracy_no_abstain",
    "macro_f1_no_abstain",
    "runtime_emitted_count",
    "runtime_correct_count",
    "runtime_high_conf_precision",
    "runtime_high_conf_coverage",
    "runtime_abstain_count",
    "runtime_abstain_rate",
    "all_high_conf_count",
    "all_high_conf_accuracy",
    "low_confidence_count",
    "report_only_high_conf_count",
    "margin_available",
    "meets_target_precision",
]

PER_LABEL_FIELDS = [
    "split",
    "label",
    "label_group",
    "threshold",
    "total_gold_count",
    "predicted_label_count",
    "emitted_count",
    "correct_emitted_count",
    "high_conf_precision",
    "recall_on_gold",
    "prediction_coverage",
    "abstain_or_block_count",
    "meets_target_precision",
]

SUMMARY_FIELDS = [
    "summary_type",
    "split",
    "label",
    "threshold",
    "precision",
    "coverage",
    "abstain_rate",
    "emitted_count",
    "correct_count",
    "meets_target_precision",
    "notes",
]

CONFUSION_FIELDS = [
    "rank",
    "split",
    "gold_label",
    "predicted_label",
    "count",
    "avg_confidence",
    "max_confidence",
    "high_conf_error_count_at_selected_threshold",
    "predicted_label_group",
]

ERROR_BUCKET_FIELDS = [
    "rank",
    "split",
    "gold_label",
    "predicted_label",
    "confidence_bucket",
    "count",
    "avg_confidence",
    "max_confidence",
    "predicted_label_group",
    "recommended_next_action",
]

BASELINE_PER_LABEL_FIELDS = [
    "split",
    "label",
    "label_group",
    "support",
    "precision",
    "recall",
    "f1",
]


class GateEvalError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate high-confidence abstain gates from prediction TSV rows."
    )
    parser.add_argument("--predictions", required=True, help="Prediction TSV path.")
    parser.add_argument(
        "--metrics-json",
        default="",
        help="Optional baseline metrics JSON path for report metadata.",
    )
    parser.add_argument("--output-dir", required=True, help="Output report directory.")
    parser.add_argument("--split", default="heldout", help="Split to evaluate.")
    parser.add_argument(
        "--target-precision",
        type=float,
        default=0.90,
        help="Target runtime-eligible high-confidence precision.",
    )
    parser.add_argument("--threshold-start", type=float, default=0.50)
    parser.add_argument("--threshold-stop", type=float, default=0.95)
    parser.add_argument("--threshold-step", type=float, default=0.05)
    parser.add_argument(
        "--margin-threshold",
        type=float,
        default=None,
        help="Optional top1-top2 probability margin threshold when a margin column exists.",
    )
    parser.add_argument(
        "--runtime-labels",
        default=",".join(RUNTIME_ELIGIBLE_LABELS),
        help="Comma-separated labels eligible for runtime high-confidence stats.",
    )
    parser.add_argument(
        "--report-only-labels",
        default=",".join(REPORT_ONLY_LABELS),
        help="Comma-separated labels tracked as report-only.",
    )
    return parser.parse_args()


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise GateEvalError(f"missing TSV: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_json(path: Path | None) -> dict:
    if path is None or not str(path):
        return {}
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_tsv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def threshold_values(start: float, stop: float, step: float) -> list[float]:
    values: list[float] = []
    value = start
    while value <= stop + 1e-9:
        values.append(round(value, 2))
        value += step
    return values


def parse_label_list(raw: str) -> set[str]:
    return {item.strip() for item in raw.split(",") if item.strip()}


def confidence(row: dict[str, str]) -> float:
    raw = row.get("confidence", "")
    if raw == "":
        raise GateEvalError("prediction TSV is missing required confidence values")
    return float(raw)


def margin_available(rows: list[dict[str, str]]) -> bool:
    if not rows:
        return False
    return "margin" in rows[0] or "probability_margin" in rows[0]


def margin_value(row: dict[str, str]) -> float | None:
    raw = row.get("margin", row.get("probability_margin", ""))
    if raw == "":
        return None
    return float(raw)


def label_group(label: str, runtime_labels: set[str], report_only_labels: set[str]) -> str:
    if label in runtime_labels:
        return "runtime_eligible"
    if label in report_only_labels:
        return "report_only"
    return "unknown"


def observed_labels(rows: list[dict[str, str]]) -> list[str]:
    labels = {row["gold_label"] for row in rows}
    labels.update(row["predicted_label"] for row in rows)
    ordered = [label for label in LABEL_ORDER if label in labels]
    ordered.extend(sorted(labels - set(ordered)))
    return ordered


def base_metrics(rows: list[dict[str, str]], labels: list[str]) -> dict[str, object]:
    gold = [row["gold_label"] for row in rows]
    pred = [row["predicted_label"] for row in rows]
    precision, recall, f1, support = precision_recall_fscore_support(
        gold,
        pred,
        labels=labels,
        zero_division=0,
    )
    per_label = []
    for index, label in enumerate(labels):
        per_label.append(
            {
                "label": label,
                "support": int(support[index]),
                "precision": float(precision[index]),
                "recall": float(recall[index]),
                "f1": float(f1[index]),
            }
        )
    return {
        "accuracy": float(accuracy_score(gold, pred)) if rows else 0.0,
        "macro_f1": float(sum(f1) / len(f1)) if len(f1) else 0.0,
        "per_label": per_label,
    }


def baseline_per_label_rows(
    rows: list[dict[str, str]],
    split: str,
    labels: list[str],
    runtime_labels: set[str],
    report_only_labels: set[str],
) -> list[dict[str, object]]:
    metrics = base_metrics(rows, labels)
    out: list[dict[str, object]] = []
    for row in metrics["per_label"]:
        label = str(row["label"])
        out.append(
            {
                "split": split,
                "label": label,
                "label_group": label_group(label, runtime_labels, report_only_labels),
                "support": row["support"],
                "precision": format_float(row["precision"]),
                "recall": format_float(row["recall"]),
                "f1": format_float(row["f1"]),
            }
        )
    return out


def passes_gate(
    row: dict[str, str],
    threshold: float,
    requested_margin_threshold: float | None,
) -> bool:
    if confidence(row) < threshold:
        return False
    if requested_margin_threshold is None:
        return True
    margin = margin_value(row)
    if margin is None:
        return False
    return margin >= requested_margin_threshold


def evaluate_threshold(
    rows: list[dict[str, str]],
    split: str,
    threshold: float,
    requested_margin_threshold: float | None,
    runtime_labels: set[str],
    report_only_labels: set[str],
    baseline_accuracy: float,
    baseline_macro_f1: float,
    target_precision: float,
) -> dict[str, object]:
    total = len(rows)
    high_conf_rows = [
        row for row in rows if passes_gate(row, threshold, requested_margin_threshold)
    ]
    runtime_rows = [
        row for row in high_conf_rows if row["predicted_label"] in runtime_labels
    ]
    report_only_rows = [
        row for row in high_conf_rows if row["predicted_label"] in report_only_labels
    ]
    low_confidence_count = total - len(high_conf_rows)
    runtime_correct = sum(1 for row in runtime_rows if row["gold_label"] == row["predicted_label"])
    all_correct = sum(1 for row in high_conf_rows if row["gold_label"] == row["predicted_label"])
    runtime_precision = runtime_correct / len(runtime_rows) if runtime_rows else 0.0
    all_accuracy = all_correct / len(high_conf_rows) if high_conf_rows else 0.0
    coverage = len(runtime_rows) / total if total else 0.0
    abstain_count = total - len(runtime_rows)
    abstain_rate = abstain_count / total if total else 0.0
    margin_text = (
        "" if requested_margin_threshold is None else f"{requested_margin_threshold:.4f}"
    )
    return {
        "split": split,
        "threshold": f"{threshold:.2f}",
        "margin_threshold": margin_text,
        "total_count": total,
        "overall_accuracy_no_abstain": f"{baseline_accuracy:.4f}",
        "macro_f1_no_abstain": f"{baseline_macro_f1:.4f}",
        "runtime_emitted_count": len(runtime_rows),
        "runtime_correct_count": runtime_correct,
        "runtime_high_conf_precision": f"{runtime_precision:.4f}",
        "runtime_high_conf_coverage": f"{coverage:.4f}",
        "runtime_abstain_count": abstain_count,
        "runtime_abstain_rate": f"{abstain_rate:.4f}",
        "all_high_conf_count": len(high_conf_rows),
        "all_high_conf_accuracy": f"{all_accuracy:.4f}",
        "low_confidence_count": low_confidence_count,
        "report_only_high_conf_count": len(report_only_rows),
        "margin_available": str(margin_available(rows)).lower(),
        "meets_target_precision": str(runtime_precision >= target_precision).lower(),
        "_threshold_float": threshold,
        "_precision_float": runtime_precision,
        "_coverage_float": coverage,
        "_abstain_float": abstain_rate,
    }


def per_label_threshold_rows(
    rows: list[dict[str, str]],
    split: str,
    thresholds: Iterable[float],
    requested_margin_threshold: float | None,
    runtime_labels: set[str],
    report_only_labels: set[str],
    target_precision: float,
) -> list[dict[str, object]]:
    labels = [label for label in LABEL_ORDER if label in runtime_labels or label in report_only_labels]
    observed = {row["gold_label"] for row in rows} | {row["predicted_label"] for row in rows}
    labels.extend(sorted(observed - set(labels)))
    total_gold = Counter(row["gold_label"] for row in rows)
    total_predicted = Counter(row["predicted_label"] for row in rows)
    out: list[dict[str, object]] = []
    for label in labels:
        group = label_group(label, runtime_labels, report_only_labels)
        for threshold in thresholds:
            predicted_rows = [row for row in rows if row["predicted_label"] == label]
            emitted = [
                row
                for row in predicted_rows
                if passes_gate(row, threshold, requested_margin_threshold)
            ]
            correct = sum(1 for row in emitted if row["gold_label"] == label)
            precision = correct / len(emitted) if emitted else 0.0
            recall = correct / total_gold[label] if total_gold[label] else 0.0
            prediction_coverage = (
                len(emitted) / total_predicted[label] if total_predicted[label] else 0.0
            )
            out.append(
                {
                    "split": split,
                    "label": label,
                    "label_group": group,
                    "threshold": f"{threshold:.2f}",
                    "total_gold_count": total_gold[label],
                    "predicted_label_count": total_predicted[label],
                    "emitted_count": len(emitted),
                    "correct_emitted_count": correct,
                    "high_conf_precision": f"{precision:.4f}",
                    "recall_on_gold": f"{recall:.4f}",
                    "prediction_coverage": f"{prediction_coverage:.4f}",
                    "abstain_or_block_count": len(rows) - len(emitted),
                    "meets_target_precision": str(precision >= target_precision).lower(),
                    "_precision_float": precision,
                    "_coverage_float": recall,
                    "_threshold_float": threshold,
                }
            )
    return out


def select_global_threshold(
    sweep_rows: list[dict[str, object]],
    target_precision: float,
) -> dict[str, object]:
    meeting = [
        row
        for row in sweep_rows
        if float(row["_precision_float"]) >= target_precision
        and int(row["runtime_emitted_count"]) > 0
    ]
    if meeting:
        return max(meeting, key=lambda row: (float(row["_coverage_float"]), -float(row["_threshold_float"])))
    return max(
        sweep_rows,
        key=lambda row: (float(row["_precision_float"]), float(row["_coverage_float"])),
    )


def select_per_label_thresholds(
    rows: list[dict[str, object]],
    target_precision: float,
) -> list[dict[str, object]]:
    by_label: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        by_label[str(row["label"])].append(row)
    selected: list[dict[str, object]] = []
    for label, label_rows in by_label.items():
        non_empty = [row for row in label_rows if int(row["emitted_count"]) > 0]
        meeting = [
            row for row in non_empty if float(row["_precision_float"]) >= target_precision
        ]
        if meeting:
            chosen = max(meeting, key=lambda row: (float(row["_coverage_float"]), -float(row["_threshold_float"])))
            note = "meets target with max recall_on_gold"
        elif non_empty:
            chosen = max(non_empty, key=lambda row: (float(row["_precision_float"]), float(row["_coverage_float"])))
            note = "does not meet target; best available precision"
        else:
            chosen = label_rows[0]
            note = "no predictions for label"
        selected.append(
            {
                "summary_type": "per_label_selected_threshold",
                "split": chosen["split"],
                "label": label,
                "threshold": chosen["threshold"],
                "precision": chosen["high_conf_precision"],
                "coverage": chosen["recall_on_gold"],
                "abstain_rate": "",
                "emitted_count": chosen["emitted_count"],
                "correct_count": chosen["correct_emitted_count"],
                "meets_target_precision": chosen["meets_target_precision"],
                "notes": note,
            }
        )
    return selected


def confidence_bucket(value: float) -> str:
    if value < 0.50:
        return "<0.50"
    if value < 0.70:
        return "0.50-0.70"
    if value < 0.90:
        return "0.70-0.90"
    return ">=0.90"


def confusion_highlights(
    rows: list[dict[str, str]],
    split: str,
    selected_threshold: float,
    runtime_labels: set[str],
    report_only_labels: set[str],
    limit: int = 30,
) -> list[dict[str, object]]:
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row["gold_label"] != row["predicted_label"]:
            groups[(row["gold_label"], row["predicted_label"])].append(row)
    ranked = sorted(groups.items(), key=lambda item: len(item[1]), reverse=True)[:limit]
    out: list[dict[str, object]] = []
    for rank, ((gold, pred), group_rows) in enumerate(ranked, start=1):
        confidences = [confidence(row) for row in group_rows]
        high_conf_error_count = sum(1 for value in confidences if value >= selected_threshold)
        out.append(
            {
                "rank": rank,
                "split": split,
                "gold_label": gold,
                "predicted_label": pred,
                "count": len(group_rows),
                "avg_confidence": f"{sum(confidences) / len(confidences):.4f}",
                "max_confidence": f"{max(confidences):.4f}",
                "high_conf_error_count_at_selected_threshold": high_conf_error_count,
                "predicted_label_group": label_group(pred, runtime_labels, report_only_labels),
            }
        )
    return out


def recommended_action(gold: str, pred: str) -> str:
    pair = {gold, pred}
    if pair == {"paragraph", "list_item"}:
        return "feature: strengthen list markers, indentation, and continuation context"
    if pred == "heading" or gold == "heading":
        return "feature/data: add heading-shape guards and clean title-vs-body ambiguity"
    if pred == "caption" or gold == "caption":
        return "feature/data: add caption association and figure/table proximity review"
    if pred == "footer_header_noise" or gold == "footer_header_noise":
        return "gate: keep strict edge/repetition checks before runtime use"
    return "review: inspect label mapping and high-confidence examples"


def error_buckets(
    rows: list[dict[str, str]],
    split: str,
    runtime_labels: set[str],
    report_only_labels: set[str],
    limit: int = 50,
) -> list[dict[str, object]]:
    groups: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row["gold_label"] == row["predicted_label"]:
            continue
        groups[
            (
                row["gold_label"],
                row["predicted_label"],
                confidence_bucket(confidence(row)),
            )
        ].append(row)
    ranked = sorted(groups.items(), key=lambda item: len(item[1]), reverse=True)[:limit]
    out: list[dict[str, object]] = []
    for rank, ((gold, pred, bucket), group_rows) in enumerate(ranked, start=1):
        confidences = [confidence(row) for row in group_rows]
        out.append(
            {
                "rank": rank,
                "split": split,
                "gold_label": gold,
                "predicted_label": pred,
                "confidence_bucket": bucket,
                "count": len(group_rows),
                "avg_confidence": f"{sum(confidences) / len(confidences):.4f}",
                "max_confidence": f"{max(confidences):.4f}",
                "predicted_label_group": label_group(pred, runtime_labels, report_only_labels),
                "recommended_next_action": recommended_action(gold, pred),
            }
        )
    return out


def weakest_labels(per_label_metrics: list[dict[str, object]], limit: int = 5) -> list[dict[str, object]]:
    return sorted(per_label_metrics, key=lambda row: float(row["f1"]))[:limit]


def format_float(value: object) -> str:
    return f"{float(value):.4f}"


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(lines)


def write_markdown_report(
    path: Path,
    *,
    run_id: str,
    model_type: str,
    predictions_path: Path,
    metrics_path: Path | None,
    split: str,
    baseline: dict[str, object],
    sweep_rows: list[dict[str, object]],
    selected_global: dict[str, object],
    selected_per_label: list[dict[str, object]],
    confusions: list[dict[str, object]],
    buckets: list[dict[str, object]],
    runtime_labels: set[str],
    report_only_labels: set[str],
    target_precision: float,
    has_margin: bool,
) -> None:
    weakest = weakest_labels(list(baseline["per_label"]))
    selected_threshold = selected_global["threshold"]
    selected_precision = selected_global["runtime_high_conf_precision"]
    selected_coverage = selected_global["runtime_high_conf_coverage"]
    selected_abstain = selected_global["runtime_abstain_rate"]
    meets_target = selected_global["meets_target_precision"]

    per_label_by_name = {str(row["label"]): row for row in selected_per_label}
    unsuitable = []
    for label in sorted(runtime_labels):
        row = per_label_by_name.get(label)
        if row is None:
            continue
        if row["meets_target_precision"] != "true" or int(row["emitted_count"]) == 0:
            unsuitable.append(label)

    lines: list[str] = []
    lines.append("# Text Block Classifier Optimization Iteration 1")
    lines.append("")
    lines.append("## Inputs")
    lines.append("")
    lines.append(f"- run_id: `{run_id}`")
    lines.append(f"- model_type: `{model_type}`")
    lines.append(f"- split: `{split}`")
    lines.append(f"- predictions: `{predictions_path}`")
    if metrics_path is not None:
        lines.append(f"- metrics: `{metrics_path}`")
    lines.append(f"- margin_available: `{str(has_margin).lower()}`")
    lines.append("")
    lines.append("## Baseline Without Abstain")
    lines.append("")
    lines.append(f"- heldout accuracy: `{format_float(baseline['accuracy'])}`")
    lines.append(f"- heldout macro F1: `{format_float(baseline['macro_f1'])}`")
    lines.append("")
    lines.append("Weakest labels by no-abstain F1:")
    lines.append("")
    lines.append(
        markdown_table(
            ["label", "support", "precision", "recall", "f1"],
            [
                [
                    row["label"],
                    row["support"],
                    format_float(row["precision"]),
                    format_float(row["recall"]),
                    format_float(row["f1"]),
                ]
                for row in weakest
            ],
        )
    )
    lines.append("")
    lines.append("Full no-abstain per-label metrics:")
    lines.append("")
    lines.append(
        markdown_table(
            ["label", "support", "precision", "recall", "f1"],
            [
                [
                    row["label"],
                    row["support"],
                    format_float(row["precision"]),
                    format_float(row["recall"]),
                    format_float(row["f1"]),
                ]
                for row in baseline["per_label"]
            ],
        )
    )
    lines.append("")
    lines.append("Secondary target:")
    lines.append("")
    if float(baseline["macro_f1"]) >= 0.90:
        lines.append("* Heldout macro F1 target `>=0.90` is met.")
    else:
        lines.append("* Heldout macro F1 target `>=0.90` is not met.")
        lines.append("* Do not present this as a completed model-quality upgrade; use the gate as a safety filter and continue optimization.")
    lines.append("")
    lines.append("## Global High-Confidence Gate")
    lines.append("")
    lines.append(f"- target precision: `{target_precision:.2f}`")
    lines.append(f"- selected threshold: `{selected_threshold}`")
    lines.append(f"- runtime high-confidence precision: `{selected_precision}`")
    lines.append(f"- runtime high-confidence coverage: `{selected_coverage}`")
    lines.append(f"- runtime abstain rate: `{selected_abstain}`")
    lines.append(f"- meets target: `{meets_target}`")
    lines.append("")
    lines.append("Global sweep:")
    lines.append("")
    lines.append(
        markdown_table(
            ["threshold", "precision", "coverage", "abstain", "emitted"],
            [
                [
                    row["threshold"],
                    row["runtime_high_conf_precision"],
                    row["runtime_high_conf_coverage"],
                    row["runtime_abstain_rate"],
                    row["runtime_emitted_count"],
                ]
                for row in sweep_rows
            ],
        )
    )
    lines.append("")
    lines.append("Interpretation:")
    lines.append("")
    if meets_target == "true":
        lines.append(
            f"* The runtime-eligible high-confidence precision target is met at threshold `{selected_threshold}`."
        )
        lines.append(
            f"* Coverage at that target is `{selected_coverage}`, so low-confidence rows abstain instead of forcing labels."
        )
    else:
        lines.append("* The runtime-eligible high-confidence precision target is not met.")
        lines.append("* Keep the model report-only and prioritize error buckets before any runtime proposal.")
    if not has_margin:
        lines.append("* Margin thresholding was not evaluated because the prediction file has no top1/top2 margin column.")
    lines.append("")
    lines.append("## Label Gate Readiness")
    lines.append("")
    selected_runtime_rows = [
        row for row in selected_per_label if row["label"] in runtime_labels
    ]
    lines.append(
        markdown_table(
            ["label", "threshold", "precision", "recall_on_gold", "emitted", "meets_target"],
            [
                [
                    row["label"],
                    row["threshold"],
                    row["precision"],
                    row["coverage"],
                    row["emitted_count"],
                    row["meets_target_precision"],
                ]
                for row in selected_runtime_rows
            ],
        )
    )
    lines.append("")
    lines.append("Runtime labels not suitable for a runtime gate this round:")
    lines.append("")
    if unsuitable:
        for label in unsuitable:
            lines.append(f"* `{label}`")
    else:
        lines.append("* none by the selected per-label threshold criterion")
    lines.append("")
    lines.append("Labels that should continue as report-only:")
    lines.append("")
    for label in sorted(report_only_labels):
        lines.append(f"* `{label}`")
    lines.append("")
    lines.append("## Confusion Highlights")
    lines.append("")
    lines.append(
        markdown_table(
            ["rank", "gold", "predicted", "count", "avg_conf", "high_conf_errors"],
            [
                [
                    row["rank"],
                    row["gold_label"],
                    row["predicted_label"],
                    row["count"],
                    row["avg_confidence"],
                    row["high_conf_error_count_at_selected_threshold"],
                ]
                for row in confusions[:10]
            ],
        )
    )
    lines.append("")
    lines.append("## Error Buckets")
    lines.append("")
    lines.append(
        markdown_table(
            ["rank", "gold", "predicted", "bucket", "count", "next_action"],
            [
                [
                    row["rank"],
                    row["gold_label"],
                    row["predicted_label"],
                    row["confidence_bucket"],
                    row["count"],
                    row["recommended_next_action"],
                ]
                for row in buckets[:12]
            ],
        )
    )
    lines.append("")
    lines.append("## Next Optimization Direction")
    lines.append("")
    lines.append("* Start with threshold tuning and per-label abstain thresholds; they directly improve safety without retraining.")
    lines.append("* Add margin/probability output in the next prediction export so margin gating can be evaluated.")
    lines.append("* Improve features for list-vs-paragraph continuation, heading shape, and caption association.")
    lines.append("* Review label mapping and data cleaning for the weakest labels before changing class weighting.")
    lines.append("* Do not connect this teacher or its reports to runtime until a separate runtime contract is written.")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    predictions_path = Path(args.predictions)
    metrics_path = Path(args.metrics_json) if args.metrics_json else None
    output_dir = Path(args.output_dir)
    runtime_labels = parse_label_list(args.runtime_labels)
    report_only_labels = parse_label_list(args.report_only_labels)

    rows = read_tsv(predictions_path)
    required = {"split", "gold_label", "predicted_label", "confidence"}
    missing = required - set(rows[0].keys() if rows else [])
    if missing:
        raise GateEvalError(f"prediction TSV missing required columns: {sorted(missing)}")
    split_rows = [row for row in rows if row["split"] == args.split]
    if not split_rows:
        raise GateEvalError(f"no rows for split: {args.split}")

    labels = observed_labels(split_rows)
    baseline = base_metrics(split_rows, labels)
    metrics = read_json(metrics_path)
    run_id = metrics.get("run_id", predictions_path.parent.name)
    model_type = metrics.get("model_type", metrics.get("model_kind", "unknown"))

    thresholds = threshold_values(
        args.threshold_start,
        args.threshold_stop,
        args.threshold_step,
    )
    has_margin = margin_available(split_rows)
    sweep_rows = [
        evaluate_threshold(
            split_rows,
            args.split,
            threshold,
            args.margin_threshold,
            runtime_labels,
            report_only_labels,
            float(baseline["accuracy"]),
            float(baseline["macro_f1"]),
            args.target_precision,
        )
        for threshold in thresholds
    ]
    selected_global = select_global_threshold(sweep_rows, args.target_precision)
    per_label_rows = per_label_threshold_rows(
        split_rows,
        args.split,
        thresholds,
        args.margin_threshold,
        runtime_labels,
        report_only_labels,
        args.target_precision,
    )
    selected_per_label = select_per_label_thresholds(
        per_label_rows,
        args.target_precision,
    )
    selected_threshold = float(selected_global["_threshold_float"])
    confusions = confusion_highlights(
        split_rows,
        args.split,
        selected_threshold,
        runtime_labels,
        report_only_labels,
    )
    buckets = error_buckets(
        split_rows,
        args.split,
        runtime_labels,
        report_only_labels,
    )

    summary_rows: list[dict[str, object]] = [
        {
            "summary_type": "global_selected_threshold",
            "split": args.split,
            "label": "ALL_RUNTIME_ELIGIBLE",
            "threshold": selected_global["threshold"],
            "precision": selected_global["runtime_high_conf_precision"],
            "coverage": selected_global["runtime_high_conf_coverage"],
            "abstain_rate": selected_global["runtime_abstain_rate"],
            "emitted_count": selected_global["runtime_emitted_count"],
            "correct_count": selected_global["runtime_correct_count"],
            "meets_target_precision": selected_global["meets_target_precision"],
            "notes": "max coverage threshold meeting target, or best available precision if target is missed",
        }
    ]
    summary_rows.extend(selected_per_label)

    clean_sweep_rows = [
        {key: value for key, value in row.items() if not key.startswith("_")}
        for row in sweep_rows
    ]
    clean_per_label_rows = [
        {key: value for key, value in row.items() if not key.startswith("_")}
        for row in per_label_rows
    ]
    baseline_label_rows = baseline_per_label_rows(
        split_rows,
        args.split,
        labels,
        runtime_labels,
        report_only_labels,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    write_tsv(output_dir / "gate_sweep.tsv", GATE_SWEEP_FIELDS, clean_sweep_rows)
    write_tsv(
        output_dir / "baseline_per_label.tsv",
        BASELINE_PER_LABEL_FIELDS,
        baseline_label_rows,
    )
    write_tsv(
        output_dir / "per_label_thresholds.tsv",
        PER_LABEL_FIELDS,
        clean_per_label_rows,
    )
    write_tsv(
        output_dir / "high_confidence_summary.tsv",
        SUMMARY_FIELDS,
        summary_rows,
    )
    write_tsv(
        output_dir / "confusion_highlights.tsv",
        CONFUSION_FIELDS,
        confusions,
    )
    write_tsv(output_dir / "error_buckets.tsv", ERROR_BUCKET_FIELDS, buckets)
    write_markdown_report(
        output_dir / "optimization_iter1.md",
        run_id=str(run_id),
        model_type=str(model_type),
        predictions_path=predictions_path,
        metrics_path=metrics_path,
        split=args.split,
        baseline=baseline,
        sweep_rows=clean_sweep_rows,
        selected_global=selected_global,
        selected_per_label=summary_rows[1:],
        confusions=confusions,
        buckets=buckets,
        runtime_labels=runtime_labels,
        report_only_labels=report_only_labels,
        target_precision=args.target_precision,
        has_margin=has_margin,
    )


if __name__ == "__main__":
    main()
