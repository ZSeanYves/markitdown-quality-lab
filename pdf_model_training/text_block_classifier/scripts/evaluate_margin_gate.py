#!/usr/bin/env python3
"""Evaluate confidence, margin, and combined abstain gates.

The script is intentionally report-only. It can read an existing prediction TSV
with top1 confidence, optionally enrich the selected split with top1/top2
probabilities from either probability columns or a local model + feature TSV,
and writes only compact review artifacts.
"""

from __future__ import annotations

import argparse
import csv
import json
import pickle
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support


META_COLUMNS = {
    "sample_id",
    "source_dataset",
    "source_page_id",
    "source_region_id",
    "page_no",
    "feature_set",
    "source_label",
    "target_label",
    "split",
    "text",
    "notes",
}

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

SWEEP_FIELDS = [
    "split",
    "gate_type",
    "confidence_threshold",
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
    "accepted_accuracy",
    "accepted_macro_f1",
    "all_accepted_count",
    "report_only_accepted_count",
    "margin_available",
    "meets_target_precision",
]

PER_LABEL_FIELDS = [
    "split",
    "label",
    "label_group",
    "gate_type",
    "confidence_threshold",
    "margin_threshold",
    "total_gold_count",
    "predicted_label_count",
    "emitted_count",
    "correct_emitted_count",
    "high_conf_precision",
    "recall_on_gold",
    "prediction_coverage",
    "abstain_or_block_count",
    "accepted_macro_f1",
    "meets_target_precision",
]

SUMMARY_FIELDS = [
    "summary_type",
    "split",
    "gate_type",
    "label",
    "confidence_threshold",
    "margin_threshold",
    "precision",
    "coverage",
    "abstain_rate",
    "accepted_macro_f1",
    "emitted_count",
    "correct_count",
    "meets_target_precision",
    "notes",
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

CONFUSION_FIELDS = [
    "rank",
    "split",
    "gold_label",
    "predicted_label",
    "count",
    "avg_confidence",
    "avg_margin",
    "max_confidence",
    "max_margin",
    "accepted_error_count_at_selected_gate",
    "predicted_label_group",
]

ERROR_BUCKET_FIELDS = [
    "rank",
    "split",
    "gold_label",
    "predicted_label",
    "confidence_bucket",
    "margin_bucket",
    "count",
    "avg_confidence",
    "avg_margin",
    "max_confidence",
    "max_margin",
    "predicted_label_group",
    "accepted_error_count_at_selected_gate",
    "recommended_next_action",
]


class GateEvalError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate confidence and margin abstain gates from prediction rows."
    )
    parser.add_argument("--predictions", required=True, help="Prediction TSV path.")
    parser.add_argument("--output-dir", required=True, help="Output report directory.")
    parser.add_argument("--split", default="heldout", help="Split to evaluate.")
    parser.add_argument(
        "--metrics-json",
        default="",
        help="Optional metrics JSON with feature columns and run metadata.",
    )
    parser.add_argument(
        "--features",
        default="",
        help="Optional feature TSV used with --model to export probabilities in memory.",
    )
    parser.add_argument(
        "--model",
        default="",
        help="Optional local sklearn model.pkl used to export probabilities in memory.",
    )
    parser.add_argument(
        "--iteration1-summary",
        default="",
        help="Optional iteration 1 high_confidence_summary.tsv for comparison.",
    )
    parser.add_argument(
        "--run-id",
        default="",
        help="Optional run identifier. Defaults to metrics_json run_id when present.",
    )
    parser.add_argument(
        "--target-precision",
        type=float,
        default=0.90,
        help="Target runtime high-confidence precision.",
    )
    parser.add_argument("--confidence-start", type=float, default=0.50)
    parser.add_argument("--confidence-stop", type=float, default=0.95)
    parser.add_argument("--confidence-step", type=float, default=0.05)
    parser.add_argument("--margin-start", type=float, default=0.00)
    parser.add_argument("--margin-stop", type=float, default=0.50)
    parser.add_argument("--margin-step", type=float, default=0.05)
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


def parse_label_list(raw: str) -> set[str]:
    return {item.strip() for item in raw.split(",") if item.strip()}


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise GateEvalError(f"missing TSV: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_json(path: Path | None) -> dict[str, Any]:
    if path is None or not str(path):
        return {}
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


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


def threshold_values(start: float, stop: float, step: float) -> list[float]:
    values: list[float] = []
    value = start
    while value <= stop + 1e-9:
        values.append(round(value, 2))
        value += step
    return values


def label_group(label: str, runtime_labels: set[str], report_only_labels: set[str]) -> str:
    if label in runtime_labels:
        return "runtime_eligible"
    if label in report_only_labels:
        return "report_only"
    return "unknown"


def observed_labels(rows: list[dict[str, str]]) -> list[str]:
    labels = {row["gold_label"] for row in rows}
    labels.update(predicted_label(row) for row in rows)
    ordered = [label for label in LABEL_ORDER if label in labels]
    ordered.extend(sorted(labels - set(ordered)))
    return ordered


def format_float(value: object) -> str:
    return f"{float(value):.4f}"


def optional_float_text(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.2f}"


def safe_ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def prediction_probability_columns(rows: list[dict[str, str]]) -> list[str]:
    if not rows:
        return []
    return [name for name in rows[0].keys() if name.startswith("prob_")]


def prediction_has_top2(rows: list[dict[str, str]]) -> bool:
    if not rows:
        return False
    keys = set(rows[0].keys())
    return {
        "top1_label",
        "top1_probability",
        "top2_label",
        "top2_probability",
    }.issubset(keys)


def row_confidence(row: dict[str, str]) -> float:
    for key in ("top1_probability", "confidence"):
        raw = row.get(key, "")
        if raw != "":
            return float(raw)
    raise GateEvalError("prediction rows are missing confidence/top1_probability values")


def row_margin(row: dict[str, str]) -> float | None:
    raw = row.get("margin", row.get("probability_margin", ""))
    if raw == "":
        return None
    return float(raw)


def predicted_label(row: dict[str, str]) -> str:
    return row.get("top1_label") or row["predicted_label"]


def has_margin(rows: list[dict[str, str]]) -> bool:
    return bool(rows) and all(row_margin(row) is not None for row in rows)


def enrich_from_probability_columns(rows: list[dict[str, str]]) -> tuple[bool, list[str]]:
    warnings: list[str] = []
    if prediction_has_top2(rows):
        for row in rows:
            row["margin"] = f"{float(row['top1_probability']) - float(row['top2_probability']):.6f}"
        return True, warnings

    prob_columns = prediction_probability_columns(rows)
    if not prob_columns:
        warnings.append("prediction TSV has no full class probability matrix")
        return False, warnings

    for row in rows:
        scored = []
        for column in prob_columns:
            label = column.removeprefix("prob_")
            scored.append((float(row[column]), label))
        scored.sort(reverse=True)
        if len(scored) < 2:
            warnings.append("probability matrix has fewer than two classes")
            return False, warnings
        top1_prob, top1_label = scored[0]
        top2_prob, top2_label = scored[1]
        row["top1_label"] = top1_label
        row["top1_probability"] = f"{top1_prob:.6f}"
        row["top2_label"] = top2_label
        row["top2_probability"] = f"{top2_prob:.6f}"
        row["margin"] = f"{top1_prob - top2_prob:.6f}"
    return True, warnings


def feature_columns(feature_rows: list[dict[str, str]], metrics: dict[str, Any]) -> list[str]:
    columns = metrics.get("feature_columns")
    if isinstance(columns, list) and columns:
        return [str(column) for column in columns]
    if not feature_rows:
        return []
    return [name for name in feature_rows[0].keys() if name not in META_COLUMNS]


def rows_to_matrix(rows: list[dict[str, str]], columns: list[str]) -> np.ndarray:
    return np.array(
        [[float(row[column]) for column in columns] for row in rows],
        dtype=np.float64,
    )


def model_classes(model: Any) -> list[str]:
    classes = getattr(model, "classes_", None)
    if classes is not None:
        return [str(item) for item in classes]
    named_steps = getattr(model, "named_steps", None)
    if named_steps:
        clf = named_steps.get("clf")
        if clf is not None and hasattr(clf, "classes_"):
            return [str(item) for item in clf.classes_]
    raise GateEvalError("model does not expose classes_")


def enrich_from_model(
    rows: list[dict[str, str]],
    *,
    model_path: Path,
    features_path: Path,
    metrics: dict[str, Any],
    split: str,
) -> tuple[bool, list[str], dict[str, object]]:
    warnings: list[str] = []
    diagnostics: dict[str, object] = {}
    if not model_path.is_file():
        warnings.append(f"model path is not available: {model_path}")
        return False, warnings, diagnostics
    if not features_path.is_file():
        warnings.append(f"feature TSV is not available: {features_path}")
        return False, warnings, diagnostics

    feature_rows_all = read_tsv(features_path)
    feature_rows = [row for row in feature_rows_all if row.get("split") == split]
    by_sample_id = {row["sample_id"]: row for row in feature_rows}
    missing = [row["sample_id"] for row in rows if row["sample_id"] not in by_sample_id]
    if missing:
        warnings.append(f"features missing for {len(missing)} prediction rows")
        return False, warnings, diagnostics

    columns = feature_columns(feature_rows_all, metrics)
    if not columns:
        warnings.append("no feature columns available for model probability export")
        return False, warnings, diagnostics

    with model_path.open("rb") as handle:
        model = pickle.load(handle)
    if not hasattr(model, "predict_proba"):
        warnings.append("model does not support predict_proba")
        return False, warnings, diagnostics

    ordered_feature_rows = [by_sample_id[row["sample_id"]] for row in rows]
    matrix = rows_to_matrix(ordered_feature_rows, columns)
    probabilities = model.predict_proba(matrix)
    classes = model_classes(model)
    mismatch_count = 0

    for row, probs in zip(rows, probabilities):
        order = np.argsort(probs)[::-1]
        top1_index = int(order[0])
        top2_index = int(order[1])
        top1_label = classes[top1_index]
        top2_label = classes[top2_index]
        top1_prob = float(probs[top1_index])
        top2_prob = float(probs[top2_index])
        if row.get("predicted_label") and row["predicted_label"] != top1_label:
            mismatch_count += 1
        row["top1_label"] = top1_label
        row["top1_probability"] = f"{top1_prob:.6f}"
        row["top2_label"] = top2_label
        row["top2_probability"] = f"{top2_prob:.6f}"
        row["margin"] = f"{top1_prob - top2_prob:.6f}"

    diagnostics.update(
        {
            "probability_source": "local_model_predict_proba",
            "model_path": str(model_path),
            "features_path": str(features_path),
            "feature_columns": len(columns),
            "model_classes": ",".join(classes),
            "prediction_top1_mismatch_count": mismatch_count,
        }
    )
    if mismatch_count:
        warnings.append(
            f"model top1 label differs from prediction TSV for {mismatch_count} rows"
        )
    return True, warnings, diagnostics


def base_metrics(rows: list[dict[str, str]], labels: list[str]) -> dict[str, object]:
    gold = [row["gold_label"] for row in rows]
    pred = [predicted_label(row) for row in rows]
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
    confidence_threshold: float | None,
    margin_threshold: float | None,
) -> bool:
    if confidence_threshold is not None and row_confidence(row) < confidence_threshold:
        return False
    if margin_threshold is None:
        return True
    margin = row_margin(row)
    if margin is None:
        return False
    return margin >= margin_threshold


def accepted_macro_f1(rows: list[dict[str, str]]) -> float:
    if not rows:
        return 0.0
    labels = observed_labels(rows)
    gold = [row["gold_label"] for row in rows]
    pred = [predicted_label(row) for row in rows]
    _, _, f1, _ = precision_recall_fscore_support(
        gold,
        pred,
        labels=labels,
        zero_division=0,
    )
    return float(sum(f1) / len(f1)) if len(f1) else 0.0


def evaluate_gate(
    rows: list[dict[str, str]],
    *,
    split: str,
    gate_type: str,
    confidence_threshold: float | None,
    margin_threshold: float | None,
    runtime_labels: set[str],
    report_only_labels: set[str],
    baseline_accuracy: float,
    baseline_macro_f1: float,
    target_precision: float,
    margin_is_available: bool,
) -> dict[str, object]:
    total = len(rows)
    accepted = [
        row for row in rows if passes_gate(row, confidence_threshold, margin_threshold)
    ]
    runtime_accepted = [
        row for row in accepted if predicted_label(row) in runtime_labels
    ]
    report_only_accepted = [
        row for row in accepted if predicted_label(row) in report_only_labels
    ]
    runtime_correct = sum(
        1 for row in runtime_accepted if row["gold_label"] == predicted_label(row)
    )
    all_correct = sum(1 for row in accepted if row["gold_label"] == predicted_label(row))
    runtime_precision = safe_ratio(runtime_correct, len(runtime_accepted))
    coverage = safe_ratio(len(runtime_accepted), total)
    abstain_count = total - len(runtime_accepted)
    accepted_accuracy = safe_ratio(all_correct, len(accepted))
    accepted_macro = accepted_macro_f1(accepted)
    return {
        "split": split,
        "gate_type": gate_type,
        "confidence_threshold": optional_float_text(confidence_threshold),
        "margin_threshold": optional_float_text(margin_threshold),
        "total_count": total,
        "overall_accuracy_no_abstain": format_float(baseline_accuracy),
        "macro_f1_no_abstain": format_float(baseline_macro_f1),
        "runtime_emitted_count": len(runtime_accepted),
        "runtime_correct_count": runtime_correct,
        "runtime_high_conf_precision": format_float(runtime_precision),
        "runtime_high_conf_coverage": format_float(coverage),
        "runtime_abstain_count": abstain_count,
        "runtime_abstain_rate": format_float(safe_ratio(abstain_count, total)),
        "accepted_accuracy": format_float(accepted_accuracy),
        "accepted_macro_f1": format_float(accepted_macro),
        "all_accepted_count": len(accepted),
        "report_only_accepted_count": len(report_only_accepted),
        "margin_available": str(margin_is_available).lower(),
        "meets_target_precision": str(runtime_precision >= target_precision).lower(),
        "_precision_float": runtime_precision,
        "_coverage_float": coverage,
        "_abstain_float": safe_ratio(abstain_count, total),
        "_accepted_macro_float": accepted_macro,
        "_confidence_float": -1.0 if confidence_threshold is None else confidence_threshold,
        "_margin_float": -1.0 if margin_threshold is None else margin_threshold,
    }


def select_best_gate(
    rows: list[dict[str, object]],
    target_precision: float,
) -> dict[str, object] | None:
    non_empty = [row for row in rows if int(row["runtime_emitted_count"]) > 0]
    if not non_empty:
        return None
    meeting = [
        row for row in non_empty if float(row["_precision_float"]) >= target_precision
    ]
    if meeting:
        return max(
            meeting,
            key=lambda row: (
                float(row["_coverage_float"]),
                float(row["_precision_float"]),
                float(row["_accepted_macro_float"]),
                -float(row["_confidence_float"]),
                -float(row["_margin_float"]),
            ),
        )
    return max(
        non_empty,
        key=lambda row: (
            float(row["_precision_float"]),
            float(row["_coverage_float"]),
            float(row["_accepted_macro_float"]),
        ),
    )


def per_label_threshold_rows(
    rows: list[dict[str, str]],
    *,
    split: str,
    confidence_thresholds: Iterable[float],
    runtime_labels: set[str],
    report_only_labels: set[str],
    target_precision: float,
) -> list[dict[str, object]]:
    labels = [label for label in LABEL_ORDER if label in runtime_labels or label in report_only_labels]
    observed = {row["gold_label"] for row in rows} | {predicted_label(row) for row in rows}
    labels.extend(sorted(observed - set(labels)))
    total_gold = Counter(row["gold_label"] for row in rows)
    total_predicted = Counter(predicted_label(row) for row in rows)
    out: list[dict[str, object]] = []
    for label in labels:
        group = label_group(label, runtime_labels, report_only_labels)
        predicted_rows = [row for row in rows if predicted_label(row) == label]
        for threshold in confidence_thresholds:
            emitted = [
                row for row in predicted_rows if row_confidence(row) >= threshold
            ]
            correct = sum(1 for row in emitted if row["gold_label"] == label)
            precision = safe_ratio(correct, len(emitted))
            recall = safe_ratio(correct, total_gold[label])
            prediction_coverage = safe_ratio(len(emitted), total_predicted[label])
            out.append(
                {
                    "split": split,
                    "label": label,
                    "label_group": group,
                    "gate_type": "per_label_confidence",
                    "confidence_threshold": f"{threshold:.2f}",
                    "margin_threshold": "",
                    "total_gold_count": total_gold[label],
                    "predicted_label_count": total_predicted[label],
                    "emitted_count": len(emitted),
                    "correct_emitted_count": correct,
                    "high_conf_precision": format_float(precision),
                    "recall_on_gold": format_float(recall),
                    "prediction_coverage": format_float(prediction_coverage),
                    "abstain_or_block_count": len(rows) - len(emitted),
                    "accepted_macro_f1": format_float(accepted_macro_f1(emitted)),
                    "meets_target_precision": str(precision >= target_precision).lower(),
                    "_precision_float": precision,
                    "_coverage_float": recall,
                    "_threshold_float": threshold,
                }
            )
    return out


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
            chosen = max(
                meeting,
                key=lambda row: (
                    float(row["_coverage_float"]),
                    float(row["_precision_float"]),
                    -float(row["_threshold_float"]),
                ),
            )
            note = "meets target with max recall_on_gold"
        elif non_empty:
            chosen = max(
                non_empty,
                key=lambda row: (
                    float(row["_precision_float"]),
                    float(row["_coverage_float"]),
                ),
            )
            note = "does not meet target; best available precision"
        else:
            chosen = label_rows[0]
            note = "no predictions for label"
        selected.append(
            {
                "summary_type": "per_label_selected_threshold",
                "split": chosen["split"],
                "gate_type": chosen["gate_type"],
                "label": label,
                "confidence_threshold": chosen["confidence_threshold"],
                "margin_threshold": chosen["margin_threshold"],
                "precision": chosen["high_conf_precision"],
                "coverage": chosen["recall_on_gold"],
                "abstain_rate": "",
                "accepted_macro_f1": "",
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


def margin_bucket(value: float | None) -> str:
    if value is None:
        return "missing"
    if value < 0.05:
        return "<0.05"
    if value < 0.15:
        return "0.05-0.15"
    if value < 0.30:
        return "0.15-0.30"
    return ">=0.30"


def recommended_action(gold: str, pred: str) -> str:
    pair = {gold, pred}
    if pred == "caption" or gold == "caption":
        return "feature/data: add caption association and figure/table proximity review"
    if pair == {"paragraph", "list_item"}:
        return "feature: strengthen list markers, indentation, and continuation context"
    if pred == "heading" or gold == "heading":
        return "feature/data: add heading-shape guards and clean title-vs-body ambiguity"
    if pred == "footer_header_noise" or gold == "footer_header_noise":
        return "gate: keep strict edge/repetition checks before runtime use"
    return "review: inspect label mapping and high-confidence examples"


def confusion_highlights(
    rows: list[dict[str, str]],
    *,
    split: str,
    selected_gate: dict[str, object],
    runtime_labels: set[str],
    report_only_labels: set[str],
    limit: int = 30,
) -> list[dict[str, object]]:
    confidence_threshold = threshold_from_row(selected_gate, "confidence_threshold")
    margin_threshold = threshold_from_row(selected_gate, "margin_threshold")
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        pred = predicted_label(row)
        if row["gold_label"] != pred:
            groups[(row["gold_label"], pred)].append(row)
    ranked = sorted(groups.items(), key=lambda item: len(item[1]), reverse=True)[:limit]
    out: list[dict[str, object]] = []
    for rank, ((gold, pred), group_rows) in enumerate(ranked, start=1):
        confidences = [row_confidence(row) for row in group_rows]
        margins = [row_margin(row) for row in group_rows if row_margin(row) is not None]
        accepted_errors = sum(
            1
            for row in group_rows
            if passes_gate(row, confidence_threshold, margin_threshold)
            and predicted_label(row) in runtime_labels
        )
        out.append(
            {
                "rank": rank,
                "split": split,
                "gold_label": gold,
                "predicted_label": pred,
                "count": len(group_rows),
                "avg_confidence": format_float(sum(confidences) / len(confidences)),
                "avg_margin": format_float(sum(margins) / len(margins)) if margins else "",
                "max_confidence": format_float(max(confidences)),
                "max_margin": format_float(max(margins)) if margins else "",
                "accepted_error_count_at_selected_gate": accepted_errors,
                "predicted_label_group": label_group(pred, runtime_labels, report_only_labels),
            }
        )
    return out


def error_buckets(
    rows: list[dict[str, str]],
    *,
    split: str,
    selected_gate: dict[str, object],
    runtime_labels: set[str],
    report_only_labels: set[str],
    limit: int = 60,
) -> list[dict[str, object]]:
    confidence_threshold = threshold_from_row(selected_gate, "confidence_threshold")
    margin_threshold = threshold_from_row(selected_gate, "margin_threshold")
    groups: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        pred = predicted_label(row)
        if row["gold_label"] == pred:
            continue
        groups[
            (
                row["gold_label"],
                pred,
                confidence_bucket(row_confidence(row)),
                margin_bucket(row_margin(row)),
            )
        ].append(row)
    ranked = sorted(groups.items(), key=lambda item: len(item[1]), reverse=True)[:limit]
    out: list[dict[str, object]] = []
    for rank, ((gold, pred, conf_bucket, m_bucket), group_rows) in enumerate(ranked, start=1):
        confidences = [row_confidence(row) for row in group_rows]
        margins = [row_margin(row) for row in group_rows if row_margin(row) is not None]
        accepted_errors = sum(
            1
            for row in group_rows
            if passes_gate(row, confidence_threshold, margin_threshold)
            and predicted_label(row) in runtime_labels
        )
        out.append(
            {
                "rank": rank,
                "split": split,
                "gold_label": gold,
                "predicted_label": pred,
                "confidence_bucket": conf_bucket,
                "margin_bucket": m_bucket,
                "count": len(group_rows),
                "avg_confidence": format_float(sum(confidences) / len(confidences)),
                "avg_margin": format_float(sum(margins) / len(margins)) if margins else "",
                "max_confidence": format_float(max(confidences)),
                "max_margin": format_float(max(margins)) if margins else "",
                "predicted_label_group": label_group(pred, runtime_labels, report_only_labels),
                "accepted_error_count_at_selected_gate": accepted_errors,
                "recommended_next_action": recommended_action(gold, pred),
            }
        )
    return out


def threshold_from_row(row: dict[str, object], key: str) -> float | None:
    raw = str(row.get(key, ""))
    if raw == "":
        return None
    return float(raw)


def add_summary_row(
    rows: list[dict[str, object]],
    summary_type: str,
    selected: dict[str, object] | None,
    notes: str,
) -> None:
    if selected is None:
        rows.append(
            {
                "summary_type": summary_type,
                "split": "",
                "gate_type": "",
                "label": "ALL_RUNTIME_ELIGIBLE",
                "confidence_threshold": "",
                "margin_threshold": "",
                "precision": "",
                "coverage": "",
                "abstain_rate": "",
                "accepted_macro_f1": "",
                "emitted_count": 0,
                "correct_count": 0,
                "meets_target_precision": "false",
                "notes": notes,
            }
        )
        return
    rows.append(
        {
            "summary_type": summary_type,
            "split": selected["split"],
            "gate_type": selected["gate_type"],
            "label": "ALL_RUNTIME_ELIGIBLE",
            "confidence_threshold": selected["confidence_threshold"],
            "margin_threshold": selected["margin_threshold"],
            "precision": selected["runtime_high_conf_precision"],
            "coverage": selected["runtime_high_conf_coverage"],
            "abstain_rate": selected["runtime_abstain_rate"],
            "accepted_macro_f1": selected["accepted_macro_f1"],
            "emitted_count": selected["runtime_emitted_count"],
            "correct_count": selected["runtime_correct_count"],
            "meets_target_precision": selected["meets_target_precision"],
            "notes": notes,
        }
    )


def effective_selected_gate(
    confidence_selected: dict[str, object] | None,
    combined_selected: dict[str, object] | None,
) -> dict[str, object] | None:
    if combined_selected is None:
        return confidence_selected
    if confidence_selected is None:
        return combined_selected
    margin_threshold = threshold_from_row(combined_selected, "margin_threshold")
    if margin_threshold is not None and margin_threshold > 0:
        return combined_selected
    return confidence_selected


def parse_iteration1_summary(path: Path | None) -> dict[str, str]:
    if path is None or not str(path) or not path.is_file():
        return {}
    for row in read_tsv(path):
        if row.get("summary_type") == "global_selected_threshold":
            return row
    return {}


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(lines)


def write_error_analysis(
    path: Path,
    *,
    baseline: dict[str, object],
    confusions: list[dict[str, object]],
    buckets: list[dict[str, object]],
    selected_gate: dict[str, object],
) -> None:
    per_label = {str(row["label"]): row for row in baseline["per_label"]}
    caption = per_label.get("caption", {})
    lines: list[str] = []
    lines.append("# Text Block Classifier Error Analysis Iteration 2")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append("- split: `heldout`")
    lines.append(f"- selected_gate: `{selected_gate['gate_type']}`")
    lines.append(f"- confidence_threshold: `{selected_gate['confidence_threshold']}`")
    margin_text = selected_gate["margin_threshold"] or "none"
    lines.append(f"- margin_threshold: `{margin_text}`")
    lines.append("- model role: convert-layer soft hint with abstain gate")
    lines.append("")
    lines.append("## Caption Weakness")
    lines.append("")
    if caption:
        lines.append(
            f"- no-abstain caption F1 remains `{format_float(caption['f1'])}` "
            f"with support `{caption['support']}`."
        )
    lines.append("- DocLayNet `Caption` is useful but does not encode reliable association to the nearest figure/table/image.")
    lines.append("- The current baseline has cue features such as caption/table/figure text hints and neighbor cues, but it still lacks geometric association to nearby figures, tables, and images.")
    lines.append("- Caption-vs-paragraph errors are concentrated in short text and nearby-context ambiguity, so caption should keep a stricter runtime threshold until association features improve.")
    lines.append("")
    lines.append("## List Item vs Paragraph")
    lines.append("")
    lines.append("- The largest heldout confusion remains `list_item -> paragraph` and `paragraph -> list_item`.")
    lines.append("- Existing marker and indent features help, but wrapped-line continuation and hanging-indent context are still not strong enough.")
    lines.append("- The next feature pass should add more explicit line-start marker parsing, continuation detection, and parser block alignment diagnostics.")
    lines.append("")
    lines.append("## Paragraph/List Item vs Heading")
    lines.append("")
    lines.append("- `list_item -> heading` and `paragraph -> heading` remain high-volume errors.")
    lines.append("- The model likely over-promotes short or visually isolated body/list rows when font/shape signals look title-like.")
    lines.append("- Add heading-shape guards using nearby body density, upper/lowercase ratio, section-prefix depth, and gap patterns before retraining.")
    lines.append("")
    lines.append("## Top Confusions")
    lines.append("")
    lines.append(
        markdown_table(
            [
                "rank",
                "gold",
                "predicted",
                "count",
                "avg_conf",
                "avg_margin",
                "accepted_errors",
            ],
            [
                [
                    row["rank"],
                    row["gold_label"],
                    row["predicted_label"],
                    row["count"],
                    row["avg_confidence"],
                    row["avg_margin"],
                    row["accepted_error_count_at_selected_gate"],
                ]
                for row in confusions[:10]
            ],
        )
    )
    lines.append("")
    lines.append("## Failure Buckets")
    lines.append("")
    lines.append(
        markdown_table(
            [
                "rank",
                "gold",
                "predicted",
                "conf_bucket",
                "margin_bucket",
                "count",
                "action",
            ],
            [
                [
                    row["rank"],
                    row["gold_label"],
                    row["predicted_label"],
                    row["confidence_bucket"],
                    row["margin_bucket"],
                    row["count"],
                    row["recommended_next_action"],
                ]
                for row in buckets[:15]
            ],
        )
    )
    lines.append("")
    lines.append("## Runtime Label Decision")
    lines.append("")
    lines.append("- Keep `heading`, `paragraph`, `caption`, `table_like`, `list_item`, `footer_header_noise`, and `keep_as_text` as candidate hints only behind precision gates.")
    lines.append("- Keep `page_number_noise` and `uncertain` out of direct runtime action until dedicated evidence exists.")
    lines.append("- Keep `form_row`, `link_text`, `code_like`, `separator`, and `footnote_like` report-only.")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_optimization_report(
    path: Path,
    *,
    run_id: str,
    model_type: str,
    split: str,
    predictions_path: Path,
    metrics_path: Path | None,
    features_path: Path | None,
    model_path: Path | None,
    baseline: dict[str, object],
    iteration1: dict[str, str],
    confidence_selected: dict[str, object] | None,
    margin_selected: dict[str, object] | None,
    combined_selected: dict[str, object] | None,
    per_label_selected: list[dict[str, object]],
    confusions: list[dict[str, object]],
    margin_is_available: bool,
    diagnostics: dict[str, object],
    warnings: list[str],
    target_precision: float,
) -> None:
    selected_best = effective_selected_gate(confidence_selected, combined_selected)
    caption = next(
        (row for row in baseline["per_label"] if str(row["label"]) == "caption"),
        None,
    )
    lines: list[str] = []
    lines.append("# Text Block Classifier Optimization Iteration 2")
    lines.append("")
    lines.append("## Inputs")
    lines.append("")
    lines.append(f"- run_id: `{run_id}`")
    lines.append(f"- model_type: `{model_type}`")
    lines.append(f"- split: `{split}`")
    lines.append(f"- predictions: `{predictions_path}`")
    if metrics_path is not None:
        lines.append(f"- metrics: `{metrics_path}`")
    if features_path is not None:
        lines.append(f"- features: `{features_path}`")
    if model_path is not None:
        lines.append(f"- model: `{model_path}`")
    lines.append(f"- probability_source: `{diagnostics.get('probability_source', 'prediction_tsv_only')}`")
    lines.append(f"- margin_available: `{str(margin_is_available).lower()}`")
    if "prediction_top1_mismatch_count" in diagnostics:
        lines.append(
            f"- prediction_top1_mismatch_count: `{diagnostics['prediction_top1_mismatch_count']}`"
        )
    if warnings:
        lines.append("- warnings:")
        for warning in warnings:
            lines.append(f"  - {warning}")
    lines.append("")
    lines.append("## Iteration 1 Comparison")
    lines.append("")
    lines.append(f"- baseline heldout accuracy: `{format_float(baseline['accuracy'])}`")
    lines.append(f"- baseline heldout macro F1: `{format_float(baseline['macro_f1'])}`")
    if iteration1:
        lines.append(f"- iteration 1 global threshold: `{iteration1.get('threshold', '')}`")
        lines.append(f"- iteration 1 runtime precision: `{iteration1.get('precision', '')}`")
        lines.append(f"- iteration 1 runtime coverage: `{iteration1.get('coverage', '')}`")
        lines.append(f"- iteration 1 abstain rate: `{iteration1.get('abstain_rate', '')}`")
    else:
        lines.append("- iteration 1 summary: `not provided`")
    lines.append("")
    lines.append("## Gate Results")
    lines.append("")
    if confidence_selected is not None:
        lines.append(
            f"- confidence-only best: threshold `{confidence_selected['confidence_threshold']}`, "
            f"precision `{confidence_selected['runtime_high_conf_precision']}`, "
            f"coverage `{confidence_selected['runtime_high_conf_coverage']}`, "
            f"abstain `{confidence_selected['runtime_abstain_rate']}`, "
            f"accepted macro F1 `{confidence_selected['accepted_macro_f1']}`."
        )
    if margin_selected is not None:
        lines.append(
            f"- margin-only best: margin `{margin_selected['margin_threshold']}`, "
            f"precision `{margin_selected['runtime_high_conf_precision']}`, "
            f"coverage `{margin_selected['runtime_high_conf_coverage']}`, "
            f"abstain `{margin_selected['runtime_abstain_rate']}`, "
            f"accepted macro F1 `{margin_selected['accepted_macro_f1']}`."
        )
    else:
        lines.append("- margin-only best: `not available`")
    if combined_selected is not None:
        lines.append(
            f"- combined best: confidence `{combined_selected['confidence_threshold']}`, "
            f"margin `{combined_selected['margin_threshold']}`, "
            f"precision `{combined_selected['runtime_high_conf_precision']}`, "
            f"coverage `{combined_selected['runtime_high_conf_coverage']}`, "
            f"abstain `{combined_selected['runtime_abstain_rate']}`, "
            f"accepted macro F1 `{combined_selected['accepted_macro_f1']}`."
        )
        combined_margin = threshold_from_row(combined_selected, "margin_threshold")
        if combined_margin is not None and combined_margin == 0.0:
            lines.append("- combined sweep does not improve on confidence-only; the best pair uses margin `0.00`.")
    else:
        lines.append("- combined best: `not available`")
    if selected_best is not None:
        lines.append(
            f"- reached `runtime high-confidence precision >= {target_precision:.2f}`: "
            f"`{selected_best['meets_target_precision']}`."
        )
        if iteration1:
            iter1_cov = float(iteration1.get("coverage") or 0.0)
            cov_delta = float(selected_best["_coverage_float"]) - iter1_cov
            lines.append(f"- coverage delta vs iteration 1: `{cov_delta:+.4f}`.")
    if margin_selected is not None and confidence_selected is not None:
        if float(margin_selected["_coverage_float"]) < float(confidence_selected["_coverage_float"]):
            lines.append("- margin-only reaches the precision target, but only by reducing coverage below confidence-only.")
    lines.append("- macro F1 without abstain is unchanged because no model was retrained.")
    lines.append("")
    lines.append("## Per-Label Confidence Thresholds")
    lines.append("")
    runtime_rows = [
        row for row in per_label_selected if row["label"] in set(RUNTIME_ELIGIBLE_LABELS)
    ]
    lines.append(
        markdown_table(
            ["label", "threshold", "precision", "recall_on_gold", "emitted", "meets_target"],
            [
                [
                    row["label"],
                    row["confidence_threshold"],
                    row["precision"],
                    row["coverage"],
                    row["emitted_count"],
                    row["meets_target_precision"],
                ]
                for row in runtime_rows
            ],
        )
    )
    lines.append("")
    lines.append("## Error Analysis Summary")
    lines.append("")
    if caption is not None:
        lines.append(
            f"- caption remains the weakest label: F1 `{format_float(caption['f1'])}`, "
            f"support `{caption['support']}`."
        )
    lines.append("- list_item/paragraph/heading confusions remain the main blocker and require feature work, not just threshold tuning.")
    lines.append("- Margin gating is useful for audit, but it does not improve the best coverage-at-target gate in this sweep.")
    lines.append("")
    lines.append("Top heldout confusions at the selected gate:")
    lines.append("")
    lines.append(
        markdown_table(
            ["rank", "gold", "predicted", "count", "avg_conf", "avg_margin", "accepted_errors"],
            [
                [
                    row["rank"],
                    row["gold_label"],
                    row["predicted_label"],
                    row["count"],
                    row["avg_confidence"],
                    row["avg_margin"],
                    row["accepted_error_count_at_selected_gate"],
                ]
                for row in confusions[:10]
            ],
        )
    )
    lines.append("")
    lines.append("## Recommendation")
    lines.append("")
    lines.append("- Keep the current model as a gated soft-hint teacher; do not promote it to unconditional runtime behavior.")
    lines.append("- Keep confidence-only threshold `0.70` as the selected gate for this iteration.")
    lines.append("- Use stricter margin gates only as audit variants unless a runtime consumer explicitly prefers lower coverage for higher precision.")
    lines.append("- Retrain next with targeted features for caption association, list continuation/indentation, and heading-shape guards.")
    lines.append("- Do not retrain layout_recovery or connect this report to runtime in this iteration.")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    predictions_path = Path(args.predictions)
    metrics_path = Path(args.metrics_json) if args.metrics_json else None
    features_path = Path(args.features) if args.features else None
    model_path = Path(args.model) if args.model else None
    iteration1_path = Path(args.iteration1_summary) if args.iteration1_summary else None
    output_dir = Path(args.output_dir)

    runtime_labels = parse_label_list(args.runtime_labels)
    report_only_labels = parse_label_list(args.report_only_labels)
    metrics = read_json(metrics_path)
    prediction_rows = read_tsv(predictions_path)
    rows = [row for row in prediction_rows if row.get("split") == args.split]
    if not rows:
        raise GateEvalError(f"no rows found for split: {args.split}")

    warnings: list[str] = []
    diagnostics: dict[str, object] = {}
    matrix_available, matrix_warnings = enrich_from_probability_columns(rows)
    warnings.extend(matrix_warnings)
    if not matrix_available and features_path is not None and model_path is not None:
        model_available, model_warnings, model_diagnostics = enrich_from_model(
            rows,
            model_path=model_path,
            features_path=features_path,
            metrics=metrics,
            split=args.split,
        )
        matrix_available = model_available
        warnings.extend(model_warnings)
        diagnostics.update(model_diagnostics)

    margin_is_available = has_margin(rows)
    labels = observed_labels(rows)
    baseline = base_metrics(rows, labels)
    confidence_thresholds = threshold_values(
        args.confidence_start,
        args.confidence_stop,
        args.confidence_step,
    )
    margin_thresholds = threshold_values(
        args.margin_start,
        args.margin_stop,
        args.margin_step,
    )

    confidence_sweep = [
        evaluate_gate(
            rows,
            split=args.split,
            gate_type="confidence_only",
            confidence_threshold=threshold,
            margin_threshold=None,
            runtime_labels=runtime_labels,
            report_only_labels=report_only_labels,
            baseline_accuracy=float(baseline["accuracy"]),
            baseline_macro_f1=float(baseline["macro_f1"]),
            target_precision=args.target_precision,
            margin_is_available=margin_is_available,
        )
        for threshold in confidence_thresholds
    ]
    confidence_selected = select_best_gate(confidence_sweep, args.target_precision)

    margin_sweep: list[dict[str, object]] = []
    combined_sweep: list[dict[str, object]] = []
    margin_selected: dict[str, object] | None = None
    combined_selected: dict[str, object] | None = None
    if margin_is_available:
        margin_sweep = [
            evaluate_gate(
                rows,
                split=args.split,
                gate_type="margin_only",
                confidence_threshold=None,
                margin_threshold=threshold,
                runtime_labels=runtime_labels,
                report_only_labels=report_only_labels,
                baseline_accuracy=float(baseline["accuracy"]),
                baseline_macro_f1=float(baseline["macro_f1"]),
                target_precision=args.target_precision,
                margin_is_available=margin_is_available,
            )
            for threshold in margin_thresholds
        ]
        margin_selected = select_best_gate(margin_sweep, args.target_precision)

        for confidence_threshold in confidence_thresholds:
            for margin_threshold in margin_thresholds:
                combined_sweep.append(
                    evaluate_gate(
                        rows,
                        split=args.split,
                        gate_type="combined_confidence_margin",
                        confidence_threshold=confidence_threshold,
                        margin_threshold=margin_threshold,
                        runtime_labels=runtime_labels,
                        report_only_labels=report_only_labels,
                        baseline_accuracy=float(baseline["accuracy"]),
                        baseline_macro_f1=float(baseline["macro_f1"]),
                        target_precision=args.target_precision,
                        margin_is_available=margin_is_available,
                    )
                )
        combined_selected = select_best_gate(combined_sweep, args.target_precision)
    else:
        warnings.append("margin gate skipped because top1/top2 probabilities are unavailable")

    per_label_rows = per_label_threshold_rows(
        rows,
        split=args.split,
        confidence_thresholds=confidence_thresholds,
        runtime_labels=runtime_labels,
        report_only_labels=report_only_labels,
        target_precision=args.target_precision,
    )
    per_label_selected = select_per_label_thresholds(per_label_rows, args.target_precision)

    selected_for_errors = effective_selected_gate(confidence_selected, combined_selected)
    if selected_for_errors is None:
        raise GateEvalError("no selected gate available")
    confusions = confusion_highlights(
        rows,
        split=args.split,
        selected_gate=selected_for_errors,
        runtime_labels=runtime_labels,
        report_only_labels=report_only_labels,
    )
    buckets = error_buckets(
        rows,
        split=args.split,
        selected_gate=selected_for_errors,
        runtime_labels=runtime_labels,
        report_only_labels=report_only_labels,
    )

    summary_rows: list[dict[str, object]] = []
    add_summary_row(
        summary_rows,
        "confidence_only_selected_threshold",
        confidence_selected,
        "max coverage threshold meeting target, or best available precision if target is missed",
    )
    add_summary_row(
        summary_rows,
        "margin_only_selected_threshold",
        margin_selected,
        "max coverage margin meeting target, or unavailable when probabilities are missing",
    )
    add_summary_row(
        summary_rows,
        "combined_selected_threshold",
        combined_selected,
        "max coverage confidence+margin pair meeting target, or unavailable when probabilities are missing",
    )
    summary_rows.extend(per_label_selected)

    output_dir.mkdir(parents=True, exist_ok=True)
    write_tsv(output_dir / "gate_sweep.tsv", SWEEP_FIELDS, confidence_sweep)
    if margin_sweep:
        write_tsv(output_dir / "margin_gate_sweep.tsv", SWEEP_FIELDS, margin_sweep)
    if combined_sweep:
        write_tsv(output_dir / "combined_gate_sweep.tsv", SWEEP_FIELDS, combined_sweep)
    write_tsv(output_dir / "per_label_thresholds.tsv", PER_LABEL_FIELDS, per_label_rows)
    write_tsv(output_dir / "high_confidence_summary.tsv", SUMMARY_FIELDS, summary_rows)
    write_tsv(
        output_dir / "baseline_per_label.tsv",
        BASELINE_PER_LABEL_FIELDS,
        baseline_per_label_rows(rows, args.split, labels, runtime_labels, report_only_labels),
    )
    write_tsv(output_dir / "confusion_highlights.tsv", CONFUSION_FIELDS, confusions)
    write_tsv(output_dir / "error_buckets.tsv", ERROR_BUCKET_FIELDS, buckets)

    run_id = args.run_id or str(metrics.get("run_id", "unknown"))
    model_type = str(metrics.get("model_type", "unknown"))
    iteration1 = parse_iteration1_summary(iteration1_path)
    write_error_analysis(
        output_dir / "error_analysis.md",
        baseline=baseline,
        confusions=confusions,
        buckets=buckets,
        selected_gate=selected_for_errors,
    )
    write_optimization_report(
        output_dir / "optimization_iter2.md",
        run_id=run_id,
        model_type=model_type,
        split=args.split,
        predictions_path=predictions_path,
        metrics_path=metrics_path,
        features_path=features_path,
        model_path=model_path,
        baseline=baseline,
        iteration1=iteration1,
        confidence_selected=confidence_selected,
        margin_selected=margin_selected,
        combined_selected=combined_selected,
        per_label_selected=per_label_selected,
        confusions=confusions,
        margin_is_available=margin_is_available,
        diagnostics=diagnostics,
        warnings=warnings,
        target_precision=args.target_precision,
    )

    if warnings:
        for warning in warnings:
            print(f"warning: {warning}", file=sys.stderr)
    print(
        "gate evaluation complete: "
        f"split={args.split} margin_available={str(margin_is_available).lower()} "
        f"output_dir={output_dir}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GateEvalError as exc:
        raise SystemExit(f"error: {exc}") from exc
