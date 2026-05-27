#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
import pickle
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


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

PER_LABEL_FIELDS = [
    "split",
    "label",
    "support",
    "precision",
    "recall",
    "f1",
    "zero_recall",
]

CONFUSION_FIELDS = [
    "split",
    "gold_label",
    "predicted_label",
    "count",
]

PREDICTION_FIELDS = [
    "split",
    "sample_id",
    "source_page_id",
    "source_region_id",
    "gold_label",
    "predicted_label",
    "text_missing",
    "confidence",
    "text",
    "notes",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train a local-only DocLayNet text block baseline from feature TSV rows."
    )
    parser.add_argument("--features", required=True, help="Feature TSV path.")
    parser.add_argument("--run-id", required=True, help="Local run identifier.")
    parser.add_argument(
        "--output-root",
        required=True,
        help="Local-only root for models/reports, e.g. text_block_classifier/local_only.",
    )
    parser.add_argument(
        "--feature-set-name",
        default="baseline_v1",
        help="Feature set label to record in reports.",
    )
    return parser.parse_args()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def truncate_text(raw: str, limit: int = 140) -> str:
    collapsed = " ".join(raw.split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 3] + "..."


def feature_columns(rows: list[dict[str, str]]) -> list[str]:
    if not rows:
        return []
    return [name for name in rows[0].keys() if name not in META_COLUMNS]


def rows_to_matrix(rows: list[dict[str, str]], columns: list[str]) -> np.ndarray:
    return np.array(
        [[float(row[column]) for column in columns] for row in rows],
        dtype=np.float64,
    )


def split_rows(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    out: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        out[row["split"]].append(row)
    return out


def evaluate_split(
    split_name: str,
    model: Pipeline,
    rows: list[dict[str, str]],
    columns: list[str],
    labels: list[str],
) -> tuple[dict, list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    x = rows_to_matrix(rows, columns)
    gold = [row["target_label"] for row in rows]
    predicted = list(model.predict(x))
    probabilities = model.predict_proba(x)
    probability_by_label = {label: index for index, label in enumerate(model.classes_)}

    precision, recall, f1, support = precision_recall_fscore_support(
        gold,
        predicted,
        labels=labels,
        zero_division=0,
    )
    per_label_rows: list[dict[str, str]] = []
    zero_recall_labels: list[str] = []
    low_support_labels: list[str] = []
    for index, label in enumerate(labels):
        if recall[index] == 0.0 and support[index] > 0:
            zero_recall_labels.append(label)
        if support[index] < 5 and support[index] > 0:
            low_support_labels.append(label)
        per_label_rows.append(
            {
                "split": split_name,
                "label": label,
                "support": str(int(support[index])),
                "precision": f"{precision[index]:.4f}",
                "recall": f"{recall[index]:.4f}",
                "f1": f"{f1[index]:.4f}",
                "zero_recall": "true" if recall[index] == 0.0 and support[index] > 0 else "false",
            }
        )

    confusion = confusion_matrix(gold, predicted, labels=labels)
    confusion_rows: list[dict[str, str]] = []
    top_confusions: list[tuple[str, str, int]] = []
    for gold_index, gold_label in enumerate(labels):
        for pred_index, pred_label in enumerate(labels):
            count = int(confusion[gold_index, pred_index])
            if count <= 0:
                continue
            confusion_rows.append(
                {
                    "split": split_name,
                    "gold_label": gold_label,
                    "predicted_label": pred_label,
                    "count": str(count),
                }
            )
            if gold_label != pred_label:
                top_confusions.append((gold_label, pred_label, count))
    top_confusions.sort(key=lambda item: (-item[2], item[0], item[1]))

    prediction_rows: list[dict[str, str]] = []
    for row, pred, probs in zip(rows, predicted, probabilities):
        confidence = probs[probability_by_label[pred]]
        prediction_rows.append(
            {
                "split": split_name,
                "sample_id": row["sample_id"],
                "source_page_id": row["source_page_id"],
                "source_region_id": row["source_region_id"],
                "gold_label": row["target_label"],
                "predicted_label": pred,
                "text_missing": row["text_missing"],
                "confidence": f"{confidence:.6f}",
                "text": row["text"],
                "notes": row["notes"],
            }
        )

    macro_f1 = float(np.mean(f1)) if len(f1) else 0.0
    accuracy = safe_ratio(sum(1 for g, p in zip(gold, predicted) if g == p), len(gold))
    missing_rows = [row for row in rows if row["text_missing"] == "1"]
    non_missing_rows = [row for row in rows if row["text_missing"] != "1"]

    return (
        {
            "split": split_name,
            "row_count": len(rows),
            "label_distribution": dict(sorted(Counter(gold).items())),
            "macro_f1": macro_f1,
            "accuracy": accuracy,
            "low_support_labels": low_support_labels,
            "zero_recall_labels": zero_recall_labels,
            "top_confusions": [
                {"gold_label": gold_label, "predicted_label": pred_label, "count": count}
                for gold_label, pred_label, count in top_confusions[:10]
            ],
            "text_missing_rows": len(missing_rows),
            "text_non_empty_rows": len(non_missing_rows),
        },
        per_label_rows,
        confusion_rows,
        prediction_rows,
    )


def safe_ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def write_error_analysis(
    path: Path,
    metrics: dict,
    prediction_rows: list[dict[str, str]],
) -> None:
    rows_by_confusion: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in prediction_rows:
        if row["gold_label"] == row["predicted_label"]:
            continue
        rows_by_confusion[(row["gold_label"], row["predicted_label"])].append(row)

    lines = ["# Error Analysis", ""]
    lines.append(f"- run_id: `{metrics['run_id']}`")
    lines.append(f"- model_type: `{metrics['model_type']}`")
    lines.append(f"- feature_set: `{metrics.get('feature_set', 'unknown')}`")
    lines.append("")

    for split_payload in metrics["split_metrics"]:
        lines.append(f"## Split `{split_payload['split']}`")
        lines.append(f"- macro_f1: `{split_payload['macro_f1']:.4f}`")
        lines.append(f"- accuracy: `{split_payload['accuracy']:.4f}`")
        low_support = ", ".join(split_payload["low_support_labels"]) or "none"
        zero_recall = ", ".join(split_payload["zero_recall_labels"]) or "none"
        lines.append(f"- low_support_labels: `{low_support}`")
        lines.append(f"- zero_recall_labels: `{zero_recall}`")
        lines.append("- top_confusions:")
        for item in split_payload["top_confusions"][:5]:
            lines.append(
                f"  - `{item['gold_label']} -> {item['predicted_label']}` count=`{item['count']}`"
            )
        lines.append("")

        for item in split_payload["top_confusions"][:3]:
            key = (item["gold_label"], item["predicted_label"])
            examples = [
                row for row in rows_by_confusion.get(key, [])
                if row["split"] == split_payload["split"]
            ][:3]
            if not examples:
                continue
            lines.append(
                f"### Examples `{item['gold_label']} -> {item['predicted_label']}`"
            )
            for example in examples:
                lines.append(
                    f"- `{example['sample_id']}` conf=`{example['confidence']}` text=`{truncate_text(example['text'])}`"
                )
            lines.append("")

    lines.append("## Notes")
    lines.append("- Current failures are most useful for feature and data-scaling analysis, not runtime decisions.")
    lines.append("- Confusions may reflect both feature weakness and DocLayNet label ambiguity.")
    lines.append("- Consider larger DocLayNet pilot, stronger context features, and targeted specialist corpora before distillation.")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    feature_rows = read_rows(Path(args.features))
    if not feature_rows:
        raise SystemExit("feature TSV has no rows")

    by_split = split_rows(feature_rows)
    train_rows = by_split.get("train", [])
    dev_rows = by_split.get("dev", [])
    heldout_rows = by_split.get("heldout", [])
    if not train_rows:
        raise SystemExit("no train rows found in feature TSV")
    if not dev_rows:
        raise SystemExit("no dev rows found in feature TSV")
    if not heldout_rows:
        raise SystemExit("no heldout rows found in feature TSV")

    columns = feature_columns(feature_rows)
    labels = sorted({row["target_label"] for row in train_rows})

    x_train = rows_to_matrix(train_rows, columns)
    y_train = np.array([row["target_label"] for row in train_rows])

    model = Pipeline(
        steps=[
            ("scale", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    max_iter=1000,
                    class_weight="balanced",
                ),
            ),
        ]
    )
    model.fit(x_train, y_train)

    local_root = Path(args.output_root).expanduser()
    model_dir = local_root / "models" / args.run_id
    report_dir = local_root / "reports" / args.run_id
    model_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    with (model_dir / "model.pkl").open("wb") as handle:
        pickle.dump(model, handle)

    split_payloads = []
    all_per_label: list[dict[str, str]] = []
    all_confusions: list[dict[str, str]] = []
    all_predictions: list[dict[str, str]] = []
    for split_name, rows in [("train", train_rows), ("dev", dev_rows), ("heldout", heldout_rows)]:
        summary, per_label_rows, confusion_rows, prediction_rows = evaluate_split(
            split_name,
            model,
            rows,
            columns,
            labels,
        )
        split_payloads.append(summary)
        all_per_label.extend(per_label_rows)
        all_confusions.extend(confusion_rows)
        all_predictions.extend(prediction_rows)

    metrics = {
        "run_id": args.run_id,
        "model_type": "sklearn_logistic_regression_balanced",
        "feature_set": args.feature_set_name,
        "dataset_source": "doclaynet",
        "row_count": len(feature_rows),
        "feature_columns": columns,
        "train_split_count": len(train_rows),
        "dev_split_count": len(dev_rows),
        "heldout_split_count": len(heldout_rows),
        "train_label_distribution": dict(sorted(Counter(row["target_label"] for row in train_rows).items())),
        "dev_label_distribution": dict(sorted(Counter(row["target_label"] for row in dev_rows).items())),
        "heldout_label_distribution": dict(sorted(Counter(row["target_label"] for row in heldout_rows).items())),
        "split_metrics": split_payloads,
        "notes": [
            "local-only DocLayNet baseline",
            "gold source only; no PubLayNet weak rows mixed into eval",
            "not for runtime integration",
        ],
    }

    (report_dir / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_tsv(report_dir / "per_label.tsv", PER_LABEL_FIELDS, all_per_label)
    write_tsv(report_dir / "confusion.tsv", CONFUSION_FIELDS, all_confusions)
    write_tsv(report_dir / "predictions.tsv", PREDICTION_FIELDS, all_predictions)
    write_error_analysis(report_dir / "error_analysis.md", metrics, all_predictions)

    print(
        f"baseline training complete: run_id={args.run_id} "
        f"train={len(train_rows)} dev={len(dev_rows)} heldout={len(heldout_rows)} "
        f"report_dir={report_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
