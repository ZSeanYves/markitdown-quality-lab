#!/usr/bin/env python3
"""Report-only external_quality dry run for cooperative footer/header hints."""

from __future__ import annotations

import argparse
import csv
import os
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import build_external_quality_baseline_features as external_bridge
import evaluate_rule_model_cooperative_gate as cooperative_gate


SCRIPT_DIR = Path(__file__).resolve().parent
TEXT_BLOCK_ROOT = SCRIPT_DIR.parent
LAB_ROOT = TEXT_BLOCK_ROOT.parents[1]
REPO_ROOT = LAB_ROOT.parent

DEFAULT_QUALITY_ROOT = LAB_ROOT / "external_quality"
DEFAULT_MANIFEST = DEFAULT_QUALITY_ROOT / "_quality_rows_staging" / "manifest.tsv"
DEFAULT_OUTPUT_DIR = (
    TEXT_BLOCK_ROOT / "local_only" / "reports" / "external_quality_hint_dry_run"
)
QUALITY_HELPER = REPO_ROOT / "samples" / "helpers" / "quality" / "check.sh"
NATIVE_LAYOUT_TOOL = (
    REPO_ROOT
    / "_build"
    / "native"
    / "debug"
    / "build"
    / "doc_parse"
    / "pdf"
    / "layout_model_tool"
    / "layout_model_tool.exe"
)
FEATURE_BRIDGE_BUILDER = (
    TEXT_BLOCK_ROOT / "scripts" / "build_external_quality_baseline_features.py"
)
TEACHER_MODEL = (
    TEXT_BLOCK_ROOT
    / "local_only"
    / "models"
    / "pilot3000_v1_hgb_baseline_v3"
    / "model.pkl"
)

SUMMARY_FIELDS = [
    "row_id",
    "format",
    "input_path",
    "status",
    "reason",
    "candidate_count",
    "emitted_hint_count",
    "conflict_count",
    "no_override_count",
    "report_path",
]

CANDIDATE_FIELDS = [
    "row_id",
    "sample_id",
    "page_no",
    "block_id",
    "bbox",
    "text_preview",
    "current_rule_label_or_reason",
    "predicted_label",
    "model_confidence",
    "rule_support_score",
    "context_sanity_score",
    "conflict_penalty_score",
    "cooperative_score",
    "gate_action",
    "gate_status",
    "gate_reason",
    "risk_flags",
]

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


class DryRunError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Report-only external_quality dry run for cooperative "
            "footer_header_noise hints."
        )
    )
    parser.add_argument(
        "--quality-root",
        default=str(DEFAULT_QUALITY_ROOT),
        help="external_quality root directory.",
    )
    parser.add_argument(
        "--manifest",
        default=str(DEFAULT_MANIFEST),
        help="external_quality manifest.tsv path.",
    )
    parser.add_argument(
        "--format",
        default="pdf",
        help="Quality row format filter. Only pdf is supported.",
    )
    parser.add_argument(
        "--label",
        default="footer_header_noise",
        help="Target label. Only footer_header_noise is supported.",
    )
    parser.add_argument(
        "--profile",
        default="conservative",
        help="Cooperative profile label recorded in reports.",
    )
    parser.add_argument(
        "--cooperative-threshold",
        type=float,
        default=0.85,
        help="Recorded cooperative threshold.",
    )
    parser.add_argument(
        "--model-confidence-threshold",
        type=float,
        default=0.95,
        help="Recorded model confidence threshold.",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        help="Optional cap on filtered manifest rows.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Output directory for dry-run reports.",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Only write capability and manifest summaries; skip row execution.",
    )
    return parser.parse_args()


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise DryRunError(f"missing TSV: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def resolve_input_path(raw_path: str, *, quality_root: Path) -> Path | None:
    raw_path = raw_path.strip()
    if not raw_path:
        return None
    candidates: list[Path] = []
    p = Path(raw_path).expanduser()
    if p.is_absolute():
        candidates.append(p)
    else:
        candidates.append(REPO_ROOT / raw_path)
        candidates.append(LAB_ROOT / raw_path)
        if raw_path.startswith("external_quality/"):
            candidates.append(quality_root / raw_path[len("external_quality/") :])
        else:
            candidates.append(quality_root / raw_path)
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def truncate_preview(text: str, limit: int = 120) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 3] + "..."


def as_bool(row: dict[str, str], key: str) -> bool:
    return row.get(key, "") in {"1", "1.0", "true", "True"}


def as_float(row: dict[str, str], key: str, default: float = 0.0) -> float:
    raw = row.get(key, "")
    if raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def build_capabilities(
    args: argparse.Namespace, rows: list[dict[str, str]]
) -> dict[str, object]:
    pdf_rows = [row for row in rows if row.get("format", "") == "pdf"]
    resolved_inputs = [
        resolve_input_path(row.get("path", ""), quality_root=Path(args.quality_root))
        for row in pdf_rows
    ]
    moon_available = shutil.which("moon") is not None
    can_extract = NATIVE_LAYOUT_TOOL.is_file() or moon_available
    can_find_current_outputs = QUALITY_HELPER.is_file()
    can_find_feature_builder = FEATURE_BRIDGE_BUILDER.is_file()
    can_find_teacher_model = TEACHER_MODEL.is_file()
    missing: list[str] = []
    if not pdf_rows:
        missing.append("no_pdf_rows")
    if not any(path is not None for path in resolved_inputs):
        missing.append("no_resolved_inputs")
    if not can_find_current_outputs:
        missing.append("quality_helper_missing")
    if not can_extract:
        missing.append("legacy_block_export_missing")
    if not can_find_feature_builder:
        missing.append("external_feature_bridge_missing")
    if not can_find_teacher_model:
        missing.append("teacher_model_missing")
    status = (
        "partial"
        if pdf_rows
        and can_find_current_outputs
        and can_extract
        and can_find_feature_builder
        and can_find_teacher_model
        else "not_ready"
    )
    return {
        "status": status,
        "can_find_pdf_rows": bool(pdf_rows),
        "can_find_inputs": any(path is not None for path in resolved_inputs),
        "can_find_current_outputs": can_find_current_outputs,
        "can_extract_or_find_block_candidates": can_extract,
        "can_find_feature_builder": can_find_feature_builder,
        "can_find_teacher_model": can_find_teacher_model,
        "can_build_teacher_compatible_features": False,
        "moon_available": moon_available,
        "native_layout_tool": str(NATIVE_LAYOUT_TOOL),
        "feature_bridge_builder": str(FEATURE_BRIDGE_BUILDER),
        "missing": missing,
        "pdf_row_count": len(pdf_rows),
    }


def run_quality_row(
    *,
    row_id: str,
    quality_root: Path,
    manifest: Path,
    run_root: Path,
) -> tuple[int, Path, Path, Path]:
    quality_tmp_dir = run_root / "quality_run"
    cli_tmp_dir = quality_tmp_dir / "workspace"
    env = os.environ.copy()
    env.update(
        {
            "QUALITY_RUN_ID": f"hint-dry-run-{row_id}",
            "QUALITY_TMP_ROOT": str(run_root / "_quality_tmp"),
            "QUALITY_TMP_DIR": str(quality_tmp_dir),
            "MARKITDOWN_CLI_TMP_DIR": str(cli_tmp_dir),
            "MARKITDOWN_QUALITY_LAB": str(LAB_ROOT),
        }
    )
    cmd = [
        "bash",
        str(QUALITY_HELPER),
        "--private-only",
        "--require-lab",
        "--corpus-root",
        str(quality_root),
        "--lab-manifest",
        str(manifest),
        "--format",
        "pdf",
        "--id",
        row_id,
    ]
    result = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
    )
    row_dir = quality_tmp_dir / "outputs" / row_id
    markdown_path = row_dir / f"{row_id}.md"
    summary_path = quality_tmp_dir / "summary.tsv"
    metadata_path = row_dir / "metadata" / f"{row_id}.metadata.json"
    log_path = quality_tmp_dir / "runner.stdout.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(
        (result.stdout or "") + ("\n--- STDERR ---\n" + result.stderr if result.stderr else ""),
        encoding="utf-8",
    )
    return result.returncode, summary_path, markdown_path, metadata_path


def parse_quality_summary(summary_path: Path, row_id: str) -> dict[str, str]:
    if not summary_path.is_file():
        return {}
    rows = read_tsv(summary_path)
    for row in rows:
        if row.get("id") == row_id:
            return row
    return {}


def export_legacy_block_features(
    *,
    sample_id: str,
    input_path: Path,
    output_path: Path,
) -> tuple[bool, str]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if NATIVE_LAYOUT_TOOL.is_file():
        cmd = [
            str(NATIVE_LAYOUT_TOOL),
            "export",
            "--sample-id",
            sample_id,
            "--input",
            str(input_path),
            "--record-kind",
            "block",
            "--output",
            str(output_path),
        ]
    else:
        cmd = [
            "moon",
            "run",
            "doc_parse/pdf/layout_model_tool",
            "--",
            "export",
            "--sample-id",
            sample_id,
            "--input",
            str(input_path),
            "--record-kind",
            "block",
            "--output",
            str(output_path),
        ]
    result = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False, (result.stderr or result.stdout or "").strip()
    return output_path.is_file(), ""


def derive_rule_label(row: dict[str, str]) -> str:
    if as_bool(row, "is_noise_kind") or as_bool(row, "is_header_footer_candidate"):
        return "noise_like"
    if as_bool(row, "is_heading_kind"):
        return "heading_like"
    return "paragraph_like"


def footer_header_candidate(row: dict[str, str]) -> bool:
    return any(
        [
            as_bool(row, "is_header_footer_candidate"),
            as_bool(row, "is_page_number_candidate"),
            as_bool(row, "top_zone_candidate"),
            as_bool(row, "bottom_zone_candidate"),
            as_bool(row, "repeated_edge_candidate"),
        ]
    )


def footer_header_conflict_flags(row: dict[str, str]) -> list[str]:
    flags: list[str] = []
    if as_float(row, "word_count") > 20:
        flags.append("long_word_count")
    if as_float(row, "text_len") > 120:
        flags.append("long_text")
    if as_bool(row, "sentence_like_signal"):
        flags.append("sentence_like")
    y_center = as_float(row, "y_center_ratio")
    if 0.25 <= y_center <= 0.75 and not (
        as_bool(row, "top_zone_candidate") or as_bool(row, "bottom_zone_candidate")
    ):
        flags.append("central_body_band")
    if as_bool(row, "technical_sentence_guard_signal"):
        flags.append("technical_sentence_guard")
    if as_bool(row, "form_key_value_signal"):
        flags.append("form_key_value")
    return flags


def legacy_rule_support_score(row: dict[str, str]) -> float:
    parts = [
        1.0
        if as_bool(row, "top_zone_candidate") or as_bool(row, "bottom_zone_candidate")
        else 0.0,
        1.0 if as_bool(row, "is_header_footer_candidate") else 0.0,
        1.0 if as_bool(row, "is_page_number_candidate") else 0.0,
        1.0 if as_bool(row, "repeated_edge_candidate") else 0.0,
        1.0
        if as_float(row, "word_count") <= 8
        else 0.4 if as_float(row, "word_count") <= 16 else 0.0,
    ]
    return sum(parts) / len(parts)


def legacy_context_sanity_score(row: dict[str, str]) -> float:
    parts = [
        1.0 if as_float(row, "height") <= 24 else 0.4,
        1.0
        if as_bool(row, "top_zone_candidate") or as_bool(row, "bottom_zone_candidate")
        else 0.0,
        0.0 if footer_header_conflict_flags(row) else 1.0,
    ]
    return sum(parts) / len(parts)


def legacy_conflict_penalty_score(row: dict[str, str]) -> float:
    flags = footer_header_conflict_flags(row)
    return min(1.0, 0.25 * len(flags))


def bbox_string(row: dict[str, str]) -> str:
    return "[" + ",".join(
        f"{as_float(row, key):.2f}" for key in ("x0", "y0", "x1", "y1")
    ) + "]"


def candidate_rows_from_legacy(
    row_id: str,
    feature_rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], Counter[str], Counter[str]]:
    out: list[dict[str, str]] = []
    reason_counts: Counter[str] = Counter()
    risk_counts: Counter[str] = Counter()
    for row in feature_rows:
        if row.get("record_kind") != "block":
            continue
        if not footer_header_candidate(row):
            continue
        risk_flags = footer_header_conflict_flags(row)
        for flag in risk_flags:
            risk_counts[flag] += 1
        reason_counts["legacy_candidate_ready"] += 1
        sample_id = f"{row_id}:p{row.get('page_index', '')}.b{row.get('block_index', '')}"
        current_rule_bits = [derive_rule_label(row)]
        if as_bool(row, "is_header_footer_candidate"):
            current_rule_bits.append("header_footer_candidate")
        if as_bool(row, "is_page_number_candidate"):
            current_rule_bits.append("page_number_candidate")
        if as_bool(row, "top_zone_candidate"):
            current_rule_bits.append("top_zone")
        if as_bool(row, "bottom_zone_candidate"):
            current_rule_bits.append("bottom_zone")
        out.append(
            {
                "row_id": row_id,
                "sample_id": sample_id,
                "page_no": row.get("page_index", ""),
                "block_id": row.get("block_index", ""),
                "bbox": bbox_string(row),
                "text_preview": truncate_preview(row.get("text", "")),
                "current_rule_label_or_reason": ",".join(current_rule_bits),
                "predicted_label": "",
                "model_confidence": "",
                "rule_support_score": f"{legacy_rule_support_score(row):.4f}",
                "context_sanity_score": f"{legacy_context_sanity_score(row):.4f}",
                "conflict_penalty_score": f"{legacy_conflict_penalty_score(row):.4f}",
                "cooperative_score": "",
                "gate_action": "no_override",
                "gate_status": "pending_teacher_prediction",
                "gate_reason": "awaiting_teacher_bridge",
                "risk_flags": ",".join(risk_flags),
            }
        )
    return out, reason_counts, risk_counts


def feature_columns(rows: list[dict[str, str]]) -> list[str]:
    if not rows:
        return []
    return [name for name in rows[0].keys() if name not in META_COLUMNS]


def rows_to_matrix(rows: list[dict[str, str]], columns: list[str], np_module: Any) -> Any:
    return np_module.array(
        [[float(row[column]) for column in columns] for row in rows],
        dtype=np_module.float64,
    )


def model_classes(model: object) -> list[str]:
    classes = getattr(model, "classes_", None)
    if classes is not None:
        return list(classes)
    try:
        from sklearn.pipeline import Pipeline  # type: ignore
    except Exception as exc:
        raise DryRunError("teacher model does not expose classes_") from exc
    if isinstance(model, Pipeline):
        clf = model.named_steps.get("clf")
        if clf is not None and hasattr(clf, "classes_"):
            return list(clf.classes_)
    raise DryRunError("teacher model does not expose classes_")


def confidence_bucket(confidence: float) -> str:
    if confidence >= 0.99:
        return ">=0.99"
    if confidence >= 0.95:
        return "0.95-0.99"
    if confidence >= 0.90:
        return "0.90-0.95"
    if confidence >= 0.80:
        return "0.80-0.90"
    return "<0.80"


def cooperative_bucket(score: float) -> str:
    if score >= 0.90:
        return ">=0.90"
    if score >= 0.85:
        return "0.85-0.90"
    if score >= 0.70:
        return "0.70-0.85"
    return "<0.70"


def predict_feature_rows(
    feature_rows: list[dict[str, str]],
    model_path: Path,
) -> tuple[dict[str, dict[str, str]], Counter[str], Counter[str]]:
    try:
        import joblib  # type: ignore
        import numpy as np  # type: ignore
    except ImportError as exc:
        raise DryRunError(f"python dependencies missing for teacher prediction: {exc}") from exc

    if not feature_rows:
        raise DryRunError("no feature rows available for teacher prediction")
    columns = feature_columns(feature_rows)
    if not columns:
        raise DryRunError("feature TSV does not expose model columns")
    model = joblib.load(model_path)
    matrix = rows_to_matrix(feature_rows, columns, np)
    predicted = list(model.predict(matrix))
    probabilities = model.predict_proba(matrix)
    probability_by_label = {
        label: index for index, label in enumerate(model_classes(model))
    }
    predictions_by_id: dict[str, dict[str, str]] = {}
    label_counts: Counter[str] = Counter()
    confidence_counts: Counter[str] = Counter()
    for row, pred, probs in zip(feature_rows, predicted, probabilities):
        confidence = float(probs[probability_by_label[pred]])
        predictions_by_id[row["sample_id"]] = {
            "predicted_label": pred,
            "confidence": f"{confidence:.6f}",
        }
        label_counts[pred] += 1
        confidence_counts[confidence_bucket(confidence)] += 1
    return predictions_by_id, label_counts, confidence_counts


def apply_not_ready_status(
    candidate_row: dict[str, str],
    *,
    status: str,
    reason: str,
) -> None:
    candidate_row.update(
        {
            "cooperative_score": "",
            "gate_action": "no_override",
            "gate_status": status,
            "gate_reason": reason,
        }
    )


def evaluate_candidates(
    *,
    candidate_rows: list[dict[str, str]],
    feature_rows: list[dict[str, str]],
    predictions_by_id: dict[str, dict[str, str]],
    allowed_labels: set[str],
    model_confidence_threshold: float,
    cooperative_threshold: float,
    profile: str,
) -> dict[str, object]:
    feature_by_id = {row["sample_id"]: row for row in feature_rows}
    gate_status_counts: Counter[str] = Counter()
    blocked_reason_counts: Counter[str] = Counter()
    cooperative_counts: Counter[str] = Counter()

    for candidate_row in candidate_rows:
        sample_id = candidate_row["sample_id"]
        feature_row = feature_by_id.get(sample_id)
        if feature_row is None:
            apply_not_ready_status(
                candidate_row,
                status="not_ready_missing_bridge_feature_row",
                reason="bridge_missing_candidate_feature_row",
            )
            gate_status_counts[candidate_row["gate_status"]] += 1
            blocked_reason_counts[candidate_row["gate_reason"]] += 1
            continue
        prediction = predictions_by_id.get(sample_id)
        if prediction is None:
            apply_not_ready_status(
                candidate_row,
                status="not_ready_missing_teacher_prediction",
                reason="teacher_prediction_missing",
            )
            gate_status_counts[candidate_row["gate_status"]] += 1
            blocked_reason_counts[candidate_row["gate_reason"]] += 1
            continue

        candidate_row["predicted_label"] = prediction["predicted_label"]
        candidate_row["model_confidence"] = prediction["confidence"]
        hint_row = {
            "sample_id": sample_id,
            "split": feature_row.get("split", "report"),
            "source_page_id": feature_row.get("source_page_id", ""),
            "source_region_id": feature_row.get("source_region_id", ""),
            "page_no": feature_row.get("page_no", ""),
            "gold_label": feature_row.get("target_label", "unknown"),
            "predicted_label": prediction["predicted_label"],
            "confidence": prediction["confidence"],
            "text": feature_row.get("text", ""),
        }
        adapter_row = {
            "bbox": candidate_row.get("bbox", ""),
            "text": feature_row.get("text", ""),
        }
        result = cooperative_gate.evaluate_row(
            hint_row=hint_row,
            feature_row=feature_row,
            adapter_row=adapter_row,
            allowed_labels=allowed_labels,
            model_confidence_threshold=model_confidence_threshold,
            cooperative_threshold=cooperative_threshold,
            profile=profile,
        )
        candidate_row.update(
            {
                "rule_support_score": result["rule_support_score"],
                "context_sanity_score": result["context_sanity_score"],
                "conflict_penalty_score": result["conflict_penalty_score"],
                "cooperative_score": result["cooperative_score"],
                "gate_action": result["gate_action"],
                "gate_status": result["gate_status"],
                "gate_reason": result["gate_reason"],
            }
        )
        gate_status_counts[result["gate_status"]] += 1
        if result["gate_status"] != "emit":
            blocked_reason_counts[result["gate_reason"]] += 1
        cooperative_counts[cooperative_bucket(as_float(result, "cooperative_score"))] += 1

    return {
        "gate_status_counts": gate_status_counts,
        "blocked_reason_counts": blocked_reason_counts,
        "cooperative_counts": cooperative_counts,
    }


def pick_examples(candidate_rows: list[dict[str, str]], limit: int = 10) -> list[dict[str, str]]:
    def confidence_value(row: dict[str, str]) -> float:
        return as_float(row, "model_confidence")

    emitted = sorted(
        [row for row in candidate_rows if row.get("gate_status") == "emit"],
        key=confidence_value,
        reverse=True,
    )
    blocked = sorted(
        [
            row
            for row in candidate_rows
            if row.get("gate_status") != "emit" and row.get("predicted_label", "")
        ],
        key=confidence_value,
        reverse=True,
    )
    examples: list[dict[str, str]] = []
    examples.extend(emitted[: min(5, limit)])
    remaining = max(0, limit - len(examples))
    examples.extend(blocked[:remaining])
    return examples[:limit]


def write_row_report(
    path: Path,
    *,
    context: dict[str, object],
    capabilities: dict[str, object],
    bridge_report: dict[str, object] | None,
    row_candidates: list[dict[str, str]],
) -> None:
    row = context["row"]  # type: ignore[index]
    quality_summary = context.get("quality_summary", {})
    gate_counts = Counter(candidate["gate_status"] for candidate in row_candidates)
    top_reasons = Counter(
        candidate["gate_reason"]
        for candidate in row_candidates
        if candidate["gate_status"] not in {"emit", "pending_teacher_prediction"}
    )
    lines = [
        f"# External Quality Hint Dry Run: {row['id']}",
        "",
        f"- format: `{row.get('format', '')}`",
        (
            f"- input_path: `{context['input_path']}`"
            if context.get("input_path")
            else "- input_path: missing"
        ),
        f"- expected_signals: `{row.get('expected_signals', '')}`",
        f"- quality_tier: `{row.get('quality_tier', '')}`",
        f"- quality_runner_status: `{quality_summary.get('status', 'not_run')}`",
        f"- produced_markdown: `{context['markdown_path']}`",
        f"- metadata_path: `{context['metadata_path']}`",
        f"- legacy_features_path: `{context['legacy_features_path']}`",
        "",
        "## Capability Status",
        "",
        f"- overall: `{capabilities['status']}`",
        f"- can_extract_or_find_block_candidates: `{capabilities['can_extract_or_find_block_candidates']}`",
        f"- can_find_feature_builder: `{capabilities['can_find_feature_builder']}`",
        f"- can_find_teacher_model: `{capabilities['can_find_teacher_model']}`",
        f"- can_build_teacher_compatible_features: `{capabilities['can_build_teacher_compatible_features']}`",
        "",
        "## Row Result",
        "",
        f"- status: `{context['status']}`",
        f"- reason: `{context['reason']}`",
        f"- candidate_count: `{context['candidate_count']}`",
        f"- emitted_hint_count: `{context['emitted_hint_count']}`",
        f"- conflict_count: `{context['conflict_count']}`",
        f"- no_override_count: `{context['no_override_count']}`",
    ]
    if bridge_report is not None:
        lines.extend(
            [
                "",
                "## Bridge",
                "",
                f"- compatibility_status: `{bridge_report['compatibility_status']}`",
                f"- output_feature_rows: `{bridge_report['output_feature_rows']}`",
                f"- missing_feature_columns: `{','.join(bridge_report['missing_feature_columns']) or 'none'}`",
                f"- extra_feature_columns: `{','.join(bridge_report['extra_feature_columns']) or 'none'}`",
            ]
        )
    lines.extend(["", "## Candidate Gate Breakdown", ""])
    if gate_counts:
        for status, count in sorted(gate_counts.items()):
            lines.append(f"- `{status}` = `{count}`")
    else:
        lines.append("- none")
    lines.extend(["", "## Top Blocked Reasons", ""])
    if top_reasons:
        for reason, count in top_reasons.most_common(8):
            lines.append(f"- `{reason}` = `{count}`")
    else:
        lines.append("- none")
    lines.extend(["", "## Examples", ""])
    examples = pick_examples(row_candidates, limit=5)
    if examples:
        for example in examples:
            lines.append(
                f"- `{example['sample_id']}` pred=`{example['predicted_label'] or 'n/a'}` "
                f"conf=`{example['model_confidence'] or 'n/a'}` gate=`{example['gate_status']}` "
                f"risk=`{example['risk_flags'] or 'none'}` text=`{example['text_preview']}`"
            )
    else:
        lines.append("- none")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_global_report(
    path: Path,
    *,
    args: argparse.Namespace,
    capabilities: dict[str, object],
    filtered_rows: list[dict[str, str]],
    summary_rows: list[dict[str, str]],
    bridge_report: dict[str, object] | None,
    predicted_label_counts: Counter[str],
    confidence_counts: Counter[str],
    cooperative_counts: Counter[str],
    gate_status_counts: Counter[str],
    blocked_reason_counts: Counter[str],
    top_risks: Counter[str],
    examples: list[dict[str, str]],
) -> None:
    status_counts = Counter(row["status"] for row in summary_rows)
    total_candidates = sum(int(row["candidate_count"]) for row in summary_rows)
    total_emitted = sum(int(row["emitted_hint_count"]) for row in summary_rows)
    total_conflicts = sum(int(row["conflict_count"]) for row in summary_rows)
    total_no_override = sum(int(row["no_override_count"]) for row in summary_rows)
    skipped_rows = sum(1 for row in summary_rows if row["status"].startswith("skip_"))
    processed_rows = len(summary_rows) - skipped_rows
    lines = [
        "# External Quality Hint Dry Run",
        "",
        f"- label: `{args.label}`",
        f"- profile: `{args.profile}`",
        f"- cooperative_threshold: `{args.cooperative_threshold:.2f}`",
        f"- model_confidence_threshold: `{args.model_confidence_threshold:.2f}`",
        f"- format: `{args.format}`",
        f"- capability_status: `{capabilities['status']}`",
        "",
        "## Capability Check",
        "",
        f"- can_find_pdf_rows: `{capabilities['can_find_pdf_rows']}`",
        f"- can_find_inputs: `{capabilities['can_find_inputs']}`",
        f"- can_find_current_outputs: `{capabilities['can_find_current_outputs']}`",
        f"- can_extract_or_find_block_candidates: `{capabilities['can_extract_or_find_block_candidates']}`",
        f"- can_find_feature_builder: `{capabilities['can_find_feature_builder']}`",
        f"- can_find_teacher_model: `{capabilities['can_find_teacher_model']}`",
        f"- can_build_teacher_compatible_features: `{capabilities['can_build_teacher_compatible_features']}`",
        f"- missing: `{','.join(capabilities['missing']) or 'none'}`",
        "",
        "## Dry-Run Totals",
        "",
        f"- selected_rows: `{len(filtered_rows)}`",
        f"- processed_rows: `{processed_rows}`",
        f"- skipped_rows: `{skipped_rows}`",
        f"- candidate_count: `{total_candidates}`",
        f"- emitted_hints: `{total_emitted}`",
        f"- conflict_count: `{total_conflicts}`",
        f"- no_override_count: `{total_no_override}`",
        "",
        "## Feature Bridge",
        "",
    ]
    if bridge_report is None:
        lines.append("- status: `not_run`")
    else:
        lines.extend(
            [
                f"- compatibility_status: `{bridge_report['compatibility_status']}`",
                f"- matched_legacy_feature_rows: `{bridge_report['matched_legacy_feature_rows']}`",
                f"- output_feature_rows: `{bridge_report['output_feature_rows']}`",
                f"- missing_feature_columns: `{','.join(bridge_report['missing_feature_columns']) or 'none'}`",
                f"- extra_feature_columns: `{','.join(bridge_report['extra_feature_columns']) or 'none'}`",
                f"- missing_candidate_sample_ids: `{len(bridge_report['missing_candidate_sample_ids'])}`",
            ]
        )
    lines.extend(["", "## Teacher Predictions", ""])
    if predicted_label_counts:
        lines.append("- predicted_label_distribution:")
        for label, count in sorted(predicted_label_counts.items()):
            lines.append(f"  - `{label}` = `{count}`")
        lines.append("- confidence_distribution:")
        for bucket, count in sorted(confidence_counts.items()):
            lines.append(f"  - `{bucket}` = `{count}`")
    else:
        lines.append("- none")
    lines.extend(["", "## Cooperative Gate", ""])
    if gate_status_counts:
        lines.append("- gate_status_distribution:")
        for status, count in sorted(gate_status_counts.items()):
            lines.append(f"  - `{status}` = `{count}`")
        lines.append("- cooperative_score_distribution:")
        for bucket, count in sorted(cooperative_counts.items()):
            lines.append(f"  - `{bucket}` = `{count}`")
        lines.append("- top_blocked_reasons:")
        for reason, count in blocked_reason_counts.most_common(10):
            lines.append(f"  - `{reason}` = `{count}`")
    else:
        lines.append("- none")
    lines.extend(["", "## Legacy Candidate Risk Flags", ""])
    if top_risks:
        for risk, count in top_risks.most_common(10):
            lines.append(f"- `{risk}` = `{count}`")
    else:
        lines.append("- none")
    lines.extend(["", "## Row Status Counts", ""])
    for status, count in sorted(status_counts.items()):
        lines.append(f"- `{status}` = `{count}`")
    lines.extend(["", "## Examples", ""])
    if examples:
        for example in examples[:10]:
            lines.append(
                f"- `{example['row_id']}` `{example['sample_id']}` pred=`{example['predicted_label'] or 'n/a'}` "
                f"conf=`{example['model_confidence'] or 'n/a'}` gate=`{example['gate_status']}` "
                f"risk=`{example['risk_flags'] or 'none'}` text=`{example['text_preview']}`"
            )
    else:
        lines.append("- none")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    if args.format != "pdf":
        raise DryRunError("dry run only supports --format pdf")
    if args.label != "footer_header_noise":
        raise DryRunError("dry run only supports --label footer_header_noise")

    quality_root = Path(args.quality_root).resolve()
    manifest = Path(args.manifest).resolve()
    output_dir = Path(args.output_dir).resolve()
    rows = read_tsv(manifest)
    filtered = [row for row in rows if row.get("format", "") == args.format]
    if args.max_rows is not None:
        filtered = filtered[: args.max_rows]

    capabilities = build_capabilities(args, rows)
    dynamic_missing: list[str] = []

    row_contexts: dict[str, dict[str, object]] = {}
    candidate_rows: list[dict[str, str]] = []
    top_risks: Counter[str] = Counter()

    for row in filtered:
        row_id = row["id"]
        input_path = resolve_input_path(row.get("path", ""), quality_root=quality_root)
        row_dir = output_dir / "rows" / row_id
        legacy_features_path = row_dir / "legacy_features" / f"{row_id}.features.tsv"
        report_path = row_dir / "report.md"
        markdown_path = row_dir / "quality_run" / "outputs" / row_id / f"{row_id}.md"
        metadata_path = (
            row_dir / "quality_run" / "outputs" / row_id / "metadata" / f"{row_id}.metadata.json"
        )
        context: dict[str, object] = {
            "row": row,
            "input_path": str(input_path) if input_path else "",
            "legacy_features_path": str(legacy_features_path),
            "report_path": str(report_path),
            "markdown_path": str(markdown_path),
            "metadata_path": str(metadata_path),
            "quality_summary": {},
            "candidate_count": 0,
            "emitted_hint_count": 0,
            "conflict_count": 0,
            "no_override_count": 0,
            "status": "not_ready",
            "reason": "",
        }
        row_contexts[row_id] = context

        if row.get("license_review_status") != "approved":
            context["status"] = "skip_license"
            context["reason"] = f"license_review_status={row.get('license_review_status', '')}"
            continue
        if input_path is None:
            context["status"] = "skip_missing_input"
            context["reason"] = "input_path_unresolved"
            continue
        if args.summary_only:
            context["status"] = "partial"
            context["reason"] = "summary_only"
            continue

        returncode, summary_path, produced_md, produced_metadata = run_quality_row(
            row_id=row_id,
            quality_root=quality_root,
            manifest=manifest,
            run_root=row_dir,
        )
        context["markdown_path"] = str(produced_md)
        context["metadata_path"] = str(produced_metadata)
        quality_summary = parse_quality_summary(summary_path, row_id)
        context["quality_summary"] = quality_summary
        if returncode != 0:
            context["status"] = "quality_row_failed"
            context["reason"] = quality_summary.get("notes", "quality_helper_failed")
            continue

        export_ok = False
        export_message = ""
        if capabilities["can_extract_or_find_block_candidates"]:
            export_ok, export_message = export_legacy_block_features(
                sample_id=row_id,
                input_path=input_path,
                output_path=legacy_features_path,
            )
        if not export_ok:
            context["status"] = "partial_missing_candidate_export"
            context["reason"] = export_message or "legacy_block_export_failed"
            continue

        feature_rows = read_tsv(legacy_features_path)
        row_candidates, _, risk_counts = candidate_rows_from_legacy(row_id, feature_rows)
        candidate_rows.extend(row_candidates)
        top_risks.update(risk_counts)
        context["candidate_count"] = len(row_candidates)
        if row_candidates:
            context["status"] = "partial_candidates_ready"
            context["reason"] = "legacy_candidates_ready_awaiting_teacher_bridge"
        else:
            context["status"] = "ready_no_candidates"
            context["reason"] = "no_footer_header_candidates"

    summary_path = output_dir / "external_quality_hint_summary.tsv"
    candidates_path = output_dir / "external_quality_hint_candidates.tsv"
    report_path = output_dir / "external_quality_hint_dry_run.md"
    bridge_features_path = output_dir / "external_quality_hint_features.tsv"
    bridge_report_path = output_dir / "external_quality_feature_bridge.md"
    bridge_json_path = output_dir / "external_quality_feature_bridge.json"

    write_tsv(candidates_path, candidate_rows, CANDIDATE_FIELDS)

    bridge_report: dict[str, object] | None = None
    feature_rows: list[dict[str, str]] = []
    predictions_by_id: dict[str, dict[str, str]] = {}
    predicted_label_counts: Counter[str] = Counter()
    confidence_counts: Counter[str] = Counter()
    cooperative_counts: Counter[str] = Counter()
    gate_status_counts: Counter[str] = Counter()
    blocked_reason_counts: Counter[str] = Counter()

    if args.summary_only:
        dynamic_missing.append("summary_only")
    elif candidate_rows:
        if not capabilities["can_find_feature_builder"]:
            dynamic_missing.append("external_feature_bridge_missing")
        else:
            try:
                bridge_report = external_bridge.build_external_quality_features(
                    candidates_tsv=candidates_path,
                    legacy_features_root=output_dir / "rows",
                    output_features=bridge_features_path,
                    output_report=bridge_report_path,
                    output_json=bridge_json_path,
                    feature_set="baseline_v3",
                    source_dataset="external_quality",
                    split="report",
                )
                capabilities["can_build_teacher_compatible_features"] = (
                    bridge_report["compatibility_status"] == "ready"
                )
            except Exception as exc:
                dynamic_missing.append(f"teacher_feature_bridge_failed:{exc}")

        if bridge_report is not None and bridge_report["compatibility_status"] == "ready":
            feature_rows = read_tsv(bridge_features_path)
            try:
                predictions_by_id, predicted_label_counts, confidence_counts = predict_feature_rows(
                    feature_rows, TEACHER_MODEL
                )
            except Exception as exc:
                dynamic_missing.append(f"teacher_model_prediction_failed:{exc}")
        elif bridge_report is not None:
            dynamic_missing.append("teacher_feature_columns_mismatch")
    else:
        dynamic_missing.append("no_footer_header_candidates")

    if predictions_by_id:
        evaluation = evaluate_candidates(
            candidate_rows=candidate_rows,
            feature_rows=feature_rows,
            predictions_by_id=predictions_by_id,
            allowed_labels={args.label},
            model_confidence_threshold=args.model_confidence_threshold,
            cooperative_threshold=args.cooperative_threshold,
            profile=args.profile,
        )
        cooperative_counts = evaluation["cooperative_counts"]  # type: ignore[assignment]
        gate_status_counts = evaluation["gate_status_counts"]  # type: ignore[assignment]
        blocked_reason_counts = evaluation["blocked_reason_counts"]  # type: ignore[assignment]
    elif candidate_rows:
        for candidate_row in candidate_rows:
            apply_not_ready_status(
                candidate_row,
                status="not_ready_missing_teacher_prediction",
                reason="teacher_predictions_unavailable",
            )
        gate_status_counts.update(
            Counter(candidate_row["gate_status"] for candidate_row in candidate_rows)
        )
        blocked_reason_counts.update(
            Counter(candidate_row["gate_reason"] for candidate_row in candidate_rows)
        )

    candidates_by_row_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    for candidate_row in candidate_rows:
        candidates_by_row_id[candidate_row["row_id"]].append(candidate_row)

    if predictions_by_id and bridge_report is not None:
        capabilities["status"] = "ready"
    elif capabilities["status"] == "partial":
        capabilities["status"] = "partial"
    else:
        capabilities["status"] = "not_ready"
    if dynamic_missing:
        combined = list(dict.fromkeys([*capabilities["missing"], *dynamic_missing]))
        capabilities["missing"] = combined

    summary_rows: list[dict[str, str]] = []
    for row_id, context in row_contexts.items():
        row_candidates = candidates_by_row_id.get(row_id, [])
        context["candidate_count"] = len(row_candidates)
        context["emitted_hint_count"] = sum(
            1 for row in row_candidates if row["gate_status"] == "emit"
        )
        context["conflict_count"] = sum(
            1 for row in row_candidates if row["gate_status"] == "blocked_hard_conflict"
        )
        context["no_override_count"] = sum(
            1 for row in row_candidates if row["gate_action"] == "no_override"
        )

        status = str(context["status"])
        if status in {"partial_candidates_ready", "ready_no_candidates"}:
            if not row_candidates:
                context["status"] = "ready_no_candidates"
                context["reason"] = "no_footer_header_candidates"
            elif bridge_report is None:
                context["status"] = "not_ready_missing_teacher_feature_bridge"
                context["reason"] = "teacher_feature_bridge_not_run"
            elif bridge_report["compatibility_status"] != "ready":
                context["status"] = "not_ready_feature_column_mismatch"
                context["reason"] = "teacher_feature_columns_mismatch"
            elif not predictions_by_id:
                context["status"] = "not_ready_model_load_failed"
                context["reason"] = "teacher_predictions_unavailable"
            elif any(
                row["gate_status"].startswith("not_ready") for row in row_candidates
            ):
                context["status"] = "partial_missing_scorer_inputs"
                reason_counts = Counter(
                    row["gate_status"]
                    for row in row_candidates
                    if row["gate_status"].startswith("not_ready")
                )
                context["reason"] = reason_counts.most_common(1)[0][0]
            else:
                context["status"] = "ready"
                context["reason"] = "teacher_predictions_ready"

        summary_rows.append(
            {
                "row_id": row_id,
                "format": context["row"].get("format", ""),  # type: ignore[index]
                "input_path": str(context.get("input_path", "")),
                "status": str(context["status"]),
                "reason": str(context["reason"]),
                "candidate_count": str(context["candidate_count"]),
                "emitted_hint_count": str(context["emitted_hint_count"]),
                "conflict_count": str(context["conflict_count"]),
                "no_override_count": str(context["no_override_count"]),
                "report_path": str(context["report_path"]),
            }
        )
        write_row_report(
            Path(str(context["report_path"])),
            context=context,
            capabilities=capabilities,
            bridge_report=bridge_report,
            row_candidates=row_candidates,
        )

    write_tsv(summary_path, summary_rows, SUMMARY_FIELDS)
    write_tsv(candidates_path, candidate_rows, CANDIDATE_FIELDS)
    write_global_report(
        report_path,
        args=args,
        capabilities=capabilities,
        filtered_rows=filtered,
        summary_rows=summary_rows,
        bridge_report=bridge_report,
        predicted_label_counts=predicted_label_counts,
        confidence_counts=confidence_counts,
        cooperative_counts=cooperative_counts,
        gate_status_counts=gate_status_counts,
        blocked_reason_counts=blocked_reason_counts,
        top_risks=top_risks,
        examples=pick_examples(candidate_rows, limit=10),
    )

    if capabilities["status"] != "ready":
        raise SystemExit(2)


if __name__ == "__main__":
    try:
        main()
    except DryRunError as exc:
        print(f"external quality hint dry run failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
