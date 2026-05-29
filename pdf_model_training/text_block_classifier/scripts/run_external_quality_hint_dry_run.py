#!/usr/bin/env python3
"""Report-only external_quality dry-run scaffold for text block hints.

This v0 runner intentionally does not mutate product output or expected files.
It focuses on footer_header_noise and first answers whether the current
external_quality PDF path can support teacher-compatible hint evaluation.
"""

from __future__ import annotations

import argparse
import csv
import os
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path


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
FEATURE_BUILDER = (
    TEXT_BLOCK_ROOT / "scripts" / "build_doclaynet_baseline_features.py"
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


class DryRunError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Report-only external_quality dry-run scaffold for cooperative "
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
        help="Quality row format filter. v0 only supports pdf.",
    )
    parser.add_argument(
        "--label",
        default="footer_header_noise",
        help="Target label. v0 only supports footer_header_noise.",
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


def build_capabilities(args: argparse.Namespace, rows: list[dict[str, str]]) -> dict[str, object]:
    pdf_rows = [row for row in rows if row.get("format", "") == "pdf"]
    resolved_inputs = [
        resolve_input_path(row.get("path", ""), quality_root=Path(args.quality_root))
        for row in pdf_rows
    ]
    moon_available = shutil.which("moon") is not None
    can_extract = NATIVE_LAYOUT_TOOL.is_file() or moon_available
    can_find_current_outputs = QUALITY_HELPER.is_file()
    can_find_feature_builder = FEATURE_BUILDER.is_file()
    can_find_teacher_model = TEACHER_MODEL.is_file()
    can_build_teacher_compatible_features = False
    missing = []
    if not pdf_rows:
        missing.append("no_pdf_rows")
    if not all(path is not None for path in resolved_inputs if path is not None) and not any(
        path is not None for path in resolved_inputs
    ):
        missing.append("no_resolved_inputs")
    if not can_find_current_outputs:
        missing.append("quality_helper_missing")
    if not can_extract:
        missing.append("legacy_block_export_missing")
    if not can_find_feature_builder:
        missing.append("feature_builder_missing")
    if not can_find_teacher_model:
        missing.append("teacher_model_missing")
    if not can_build_teacher_compatible_features:
        missing.append("teacher_feature_bridge_missing")
    if not pdf_rows:
        status = "not_ready"
    elif can_find_current_outputs and can_extract and can_find_feature_builder and can_find_teacher_model:
        status = "partial"
    else:
        status = "not_ready"
    return {
        "status": status,
        "can_find_pdf_rows": bool(pdf_rows),
        "can_find_inputs": any(path is not None for path in resolved_inputs),
        "can_find_current_outputs": can_find_current_outputs,
        "can_extract_or_find_block_candidates": can_extract,
        "can_find_feature_builder": can_find_feature_builder,
        "can_find_teacher_model": can_find_teacher_model,
        "can_build_teacher_compatible_features": can_build_teacher_compatible_features,
        "moon_available": moon_available,
        "native_layout_tool": str(NATIVE_LAYOUT_TOOL),
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
        1.0 if as_bool(row, "top_zone_candidate") or as_bool(row, "bottom_zone_candidate") else 0.0,
        1.0 if as_bool(row, "is_header_footer_candidate") else 0.0,
        1.0 if as_bool(row, "is_page_number_candidate") else 0.0,
        1.0 if as_bool(row, "repeated_edge_candidate") else 0.0,
        1.0 if as_float(row, "word_count") <= 8 else 0.4 if as_float(row, "word_count") <= 16 else 0.0,
    ]
    return sum(parts) / len(parts)


def legacy_context_sanity_score(row: dict[str, str]) -> float:
    parts = [
        1.0 if as_float(row, "height") <= 24 else 0.4,
        1.0 if as_bool(row, "top_zone_candidate") or as_bool(row, "bottom_zone_candidate") else 0.0,
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
        gate_reason = (
            "missing_teacher_feature_bridge"
            if not risk_flags
            else "missing_teacher_feature_bridge;" + ";".join(risk_flags)
        )
        reason_counts[gate_reason] += 1
        sample_id = f"{row_id}:p{row.get('page_index','')}.b{row.get('block_index','')}"
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
                "gate_status": "not_ready_missing_teacher_prediction",
                "gate_reason": gate_reason,
                "risk_flags": ",".join(risk_flags),
            }
        )
    return out, reason_counts, risk_counts


def write_row_report(
    path: Path,
    *,
    row: dict[str, str],
    input_path: Path | None,
    quality_summary: dict[str, str],
    markdown_path: Path,
    metadata_path: Path,
    legacy_features_path: Path,
    candidate_count: int,
    capability_reason: str,
    global_capabilities: dict[str, object],
) -> None:
    lines = [
        f"# External Quality Hint Dry Run: {row['id']}",
        "",
        f"- format: `{row.get('format','')}`",
        f"- input_path: `{input_path}`" if input_path else "- input_path: missing",
        f"- expected_signals: `{row.get('expected_signals','')}`",
        f"- quality_tier: `{row.get('quality_tier','')}`",
        f"- quality_runner_status: `{quality_summary.get('status','not_run')}`",
        f"- produced_markdown: `{markdown_path}`",
        f"- metadata_path: `{metadata_path}`",
        f"- legacy_features_path: `{legacy_features_path}`",
        f"- footer_header_candidate_count: `{candidate_count}`",
        "",
        "## Capability Status",
        "",
        f"- overall: `{global_capabilities['status']}`",
        f"- can_find_pdf_rows: `{global_capabilities['can_find_pdf_rows']}`",
        f"- can_find_inputs: `{global_capabilities['can_find_inputs']}`",
        f"- can_find_current_outputs: `{global_capabilities['can_find_current_outputs']}`",
        f"- can_extract_or_find_block_candidates: `{global_capabilities['can_extract_or_find_block_candidates']}`",
        f"- can_find_feature_builder: `{global_capabilities['can_find_feature_builder']}`",
        f"- can_find_teacher_model: `{global_capabilities['can_find_teacher_model']}`",
        f"- can_build_teacher_compatible_features: `{global_capabilities['can_build_teacher_compatible_features']}`",
        "",
        "## Result",
        "",
        f"- status: `{capability_reason}`",
        "- interpretation: current runner can inspect manifest rows, inputs, "
        "quality outputs, and legacy block candidates, but it still lacks a "
        "teacher-compatible bridge from arbitrary external PDF blocks to the "
        "`baseline_v3` / HGB cooperative gate surface.",
        "- this report is report-only and does not modify Markdown, metadata, "
        "or expected quality assertions.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_global_report(
    path: Path,
    *,
    args: argparse.Namespace,
    capabilities: dict[str, object],
    filtered_rows: list[dict[str, str]],
    summary_rows: list[dict[str, str]],
    top_reasons: Counter[str],
    top_risks: Counter[str],
) -> None:
    status_counts = Counter(row["status"] for row in summary_rows)
    total_candidates = sum(int(row["candidate_count"]) for row in summary_rows)
    total_emitted = sum(int(row["emitted_hint_count"]) for row in summary_rows)
    total_conflicts = sum(int(row["conflict_count"]) for row in summary_rows)
    total_no_override = sum(int(row["no_override_count"]) for row in summary_rows)
    lines = [
        "# External Quality Hint Dry Run",
        "",
        f"- label: `{args.label}`",
        f"- profile: `{args.profile}`",
        f"- cooperative_threshold: `{args.cooperative_threshold:.2f}`",
        f"- model_confidence_threshold: `{args.model_confidence_threshold:.2f}`",
        f"- format: `{args.format}`",
        f"- selected_rows: `{len(filtered_rows)}`",
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
        f"- missing: `{','.join(capabilities['missing'])}`",
        "",
        "## Dry-Run Totals",
        "",
        f"- rows_processed: `{len(summary_rows)}`",
        f"- total_candidates: `{total_candidates}`",
        f"- emitted_hints: `{total_emitted}`",
        f"- conflict_count: `{total_conflicts}`",
        f"- no_override_count: `{total_no_override}`",
        "- status_counts:",
    ]
    for status, count in sorted(status_counts.items()):
        lines.append(f"  - `{status}` = `{count}`")
    lines.append("- top_gate_reasons:")
    if top_reasons:
        for reason, count in top_reasons.most_common(10):
            lines.append(f"  - `{reason}` = `{count}`")
    else:
        lines.append("  - none")
    lines.append("- top_risk_flags:")
    if top_risks:
        for reason, count in top_risks.most_common(10):
            lines.append(f"  - `{reason}` = `{count}`")
    else:
        lines.append("  - none")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "- v0 dry run is still report-only and footer_header_noise-only. "
        "No teacher hints were emitted because the current external_quality "
        "path still lacks a bridge from arbitrary PDF blocks into the "
        "DocLayNet-trained baseline_v3 / HGB feature surface."
    )
    lines.append(
        "- legacy block export is still useful because it proves we can collect "
        "per-block text and geometry candidates without changing runtime behavior."
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    if args.format != "pdf":
        raise DryRunError("v0 dry run only supports --format pdf")
    if args.label != "footer_header_noise":
        raise DryRunError("v0 dry run only supports --label footer_header_noise")

    quality_root = Path(args.quality_root).resolve()
    manifest = Path(args.manifest).resolve()
    output_dir = Path(args.output_dir).resolve()
    rows = read_tsv(manifest)
    filtered = [row for row in rows if row.get("format", "") == args.format]
    if args.max_rows is not None:
        filtered = filtered[: args.max_rows]

    capabilities = build_capabilities(args, rows)

    summary_rows: list[dict[str, str]] = []
    candidate_rows: list[dict[str, str]] = []
    top_reasons: Counter[str] = Counter()
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

        quality_summary: dict[str, str] = {}
        candidate_count = 0
        emitted_hint_count = 0
        conflict_count = 0
        no_override_count = 0
        status = "not_ready"
        reason = ""

        if row.get("license_review_status") != "approved":
            status = "skip_license"
            reason = f"license_review_status={row.get('license_review_status','')}"
        elif input_path is None:
            status = "skip_missing_input"
            reason = "input_path_unresolved"
        else:
            if args.summary_only:
                status = "partial"
                reason = "summary_only"
            else:
                returncode, summary_path, produced_md, produced_metadata = run_quality_row(
                    row_id=row_id,
                    quality_root=quality_root,
                    manifest=manifest,
                    run_root=row_dir,
                )
                markdown_path = produced_md
                metadata_path = produced_metadata
                quality_summary = parse_quality_summary(summary_path, row_id)
                if returncode != 0:
                    status = "quality_row_failed"
                    reason = quality_summary.get("notes", "quality_helper_failed")
                else:
                    export_ok = False
                    export_message = ""
                    if capabilities["can_extract_or_find_block_candidates"]:
                        export_ok, export_message = export_legacy_block_features(
                            sample_id=row_id,
                            input_path=input_path,
                            output_path=legacy_features_path,
                        )
                    if not export_ok:
                        status = "partial_missing_candidate_export"
                        reason = export_message or "legacy_block_export_failed"
                    else:
                        feature_rows = read_tsv(legacy_features_path)
                        row_candidates, reason_counts, risk_counts = candidate_rows_from_legacy(
                            row_id, feature_rows
                        )
                        candidate_rows.extend(row_candidates)
                        candidate_count = len(row_candidates)
                        conflict_count = sum(
                            1 for candidate in row_candidates if candidate["risk_flags"]
                        )
                        no_override_count = candidate_count
                        top_reasons.update(reason_counts)
                        top_risks.update(risk_counts)
                        status = "not_ready_missing_teacher_feature_bridge"
                        reason = "legacy_candidates_ready_but_no_baseline_v3_bridge"

        summary_rows.append(
            {
                "row_id": row_id,
                "format": row.get("format", ""),
                "input_path": str(input_path) if input_path else "",
                "status": status,
                "reason": reason,
                "candidate_count": str(candidate_count),
                "emitted_hint_count": str(emitted_hint_count),
                "conflict_count": str(conflict_count),
                "no_override_count": str(no_override_count),
                "report_path": str(report_path),
            }
        )
        write_row_report(
            report_path,
            row=row,
            input_path=input_path,
            quality_summary=quality_summary,
            markdown_path=markdown_path,
            metadata_path=metadata_path,
            legacy_features_path=legacy_features_path,
            candidate_count=candidate_count,
            capability_reason=status + ":" + reason,
            global_capabilities=capabilities,
        )

    summary_path = output_dir / "external_quality_hint_summary.tsv"
    candidates_path = output_dir / "external_quality_hint_candidates.tsv"
    report_path = output_dir / "external_quality_hint_dry_run.md"

    write_tsv(summary_path, summary_rows, SUMMARY_FIELDS)
    write_tsv(candidates_path, candidate_rows, CANDIDATE_FIELDS)
    write_global_report(
        report_path,
        args=args,
        capabilities=capabilities,
        filtered_rows=filtered,
        summary_rows=summary_rows,
        top_reasons=top_reasons,
        top_risks=top_risks,
    )

    if capabilities["status"] != "ready":
        raise SystemExit(2)


if __name__ == "__main__":
    try:
        main()
    except DryRunError as exc:
        print(f"external quality hint dry run failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
