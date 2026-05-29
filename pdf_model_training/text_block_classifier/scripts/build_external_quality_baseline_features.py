#!/usr/bin/env python3
"""Bridge external_quality PDF block candidates into baseline_v3 features."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from build_doclaynet_baseline_features import (
    BASE_OUTPUT_FIELDS,
    V2_EXTRA_FIELDS,
    V3_EXTRA_FIELDS,
    build_feature_rows,
)


NON_MODEL_REPORT_COLUMNS = [
    "row_id",
    "block_id",
    "bbox",
    "text_preview",
    "current_rule_label_or_reason",
    "risk_flags",
    "gate_action",
    "gate_status",
    "gate_reason",
    "predicted_label",
    "model_confidence",
    "rule_support_score",
    "context_sanity_score",
    "conflict_penalty_score",
    "cooperative_score",
]

REQUIRED_LEGACY_FIELDS = [
    "page_index",
    "block_index",
    "text",
    "x0",
    "y0",
    "x1",
    "y1",
]


class BridgeError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build baseline_v3-compatible report-only features from "
            "external_quality block candidates and legacy block exports."
        )
    )
    parser.add_argument("--candidates-tsv", required=True, help="Candidate TSV path.")
    parser.add_argument(
        "--legacy-features-root",
        help=(
            "Root directory that contains rows/<row_id>/legacy_features/<row_id>.features.tsv. "
            "Defaults to <candidates parent>/rows."
        ),
    )
    parser.add_argument("--output-features", required=True, help="Output feature TSV path.")
    parser.add_argument("--output-report", required=True, help="Output Markdown report path.")
    parser.add_argument(
        "--output-json",
        help="Optional JSON report path. Defaults to <output-report> with .json suffix.",
    )
    parser.add_argument(
        "--feature-set",
        default="baseline_v3",
        choices=["baseline_v3"],
        help="Feature set to emit. Only baseline_v3 is supported for the bridge.",
    )
    parser.add_argument(
        "--source-dataset",
        default="external_quality",
        help="Metadata source_dataset value.",
    )
    parser.add_argument(
        "--split",
        default="report",
        help="Metadata split value.",
    )
    return parser.parse_args()


def expected_feature_columns(feature_set: str) -> list[str]:
    columns = list(BASE_OUTPUT_FIELDS)
    if feature_set in {"baseline_v2", "baseline_v3"}:
        columns.extend(V2_EXTRA_FIELDS)
    if feature_set == "baseline_v3":
        columns.extend(V3_EXTRA_FIELDS)
    return columns


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise BridgeError(f"missing TSV: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def legacy_path_for_row(rows_root: Path, row_id: str) -> Path:
    return rows_root / row_id / "legacy_features" / f"{row_id}.features.tsv"


def legacy_candidate_sample_id(row_id: str, legacy_row: dict[str, str]) -> str:
    return f"{row_id}:p{legacy_row.get('page_index', '')}.b{legacy_row.get('block_index', '')}"


def format_bbox(x0: float, y0: float, x1: float, y1: float) -> str:
    width = max(x1 - x0, 0.0)
    height = max(y1 - y0, 0.0)
    return f"{x0:.6f},{y0:.6f},{width:.6f},{height:.6f}"


def missing_required_fields(row: dict[str, str]) -> list[str]:
    missing: list[str] = []
    for field in REQUIRED_LEGACY_FIELDS:
        if row.get(field, "") == "":
            missing.append(field)
    return missing


def parse_float(raw: str, *, field: str, sample_id: str) -> float:
    try:
        return float(raw)
    except ValueError as exc:
        raise BridgeError(
            f"invalid float in legacy_features for sample_id={sample_id} field={field}: {raw!r}"
        ) from exc


def legacy_row_to_adapter(
    *,
    row_id: str,
    legacy_row: dict[str, str],
    source_dataset: str,
    split: str,
    risk_flags: str,
    is_candidate: bool,
) -> dict[str, str]:
    sample_id = legacy_candidate_sample_id(row_id, legacy_row)
    x0 = parse_float(legacy_row["x0"], field="x0", sample_id=sample_id)
    y0 = parse_float(legacy_row["y0"], field="y0", sample_id=sample_id)
    x1 = parse_float(legacy_row["x1"], field="x1", sample_id=sample_id)
    y1 = parse_float(legacy_row["y1"], field="y1", sample_id=sample_id)
    notes = [
        "external_quality_feature_bridge_v1",
        f"row_id={row_id}",
        f"record_kind={legacy_row.get('record_kind', '') or 'block'}",
        "candidate=1" if is_candidate else "candidate=0",
    ]
    if risk_flags:
        notes.append(f"risk_flags={risk_flags}")
    return {
        "sample_id": sample_id,
        "source_dataset": source_dataset,
        "source_page_id": f"{row_id}:p{legacy_row.get('page_index', '')}",
        "source_region_id": legacy_row.get("block_index", ""),
        "page_no": legacy_row.get("page_index", ""),
        "bbox": format_bbox(x0, y0, x1, y1),
        "source_label": "external_quality_candidate" if is_candidate else "external_quality_context",
        "target_label": "unknown",
        "split": split,
        "text": legacy_row.get("text", ""),
        "notes": ";".join(notes),
    }


def build_report_markdown(report: dict[str, Any]) -> str:
    missing_fields = report["missing_required_field_counts"]
    lines = [
        "# External Quality Feature Bridge",
        "",
        f"- feature_set: `{report['feature_set']}`",
        f"- source_dataset: `{report['source_dataset']}`",
        f"- split: `{report['split']}`",
        f"- compatibility_status: `{report['compatibility_status']}`",
        f"- candidate_rows: `{report['candidate_rows']}`",
        f"- unique_row_ids: `{report['unique_row_ids']}`",
        f"- matched_legacy_feature_rows: `{report['matched_legacy_feature_rows']}`",
        f"- context_block_rows_used: `{report['context_block_rows_used']}`",
        f"- output_feature_rows: `{report['output_feature_rows']}`",
        f"- feature_column_count: `{report['feature_column_count']}`",
        f"- model_feature_column_count: `{report['model_feature_column_count']}`",
        "",
        "## Compatibility",
        "",
        f"- missing_feature_columns: `{','.join(report['missing_feature_columns']) or 'none'}`",
        f"- extra_feature_columns: `{','.join(report['extra_feature_columns']) or 'none'}`",
        f"- missing_model_feature_columns: `{','.join(report['missing_model_feature_columns']) or 'none'}`",
        f"- extra_model_feature_columns: `{','.join(report['extra_model_feature_columns']) or 'none'}`",
        f"- defaulted_feature_columns: `{','.join(report['defaulted_feature_columns']) or 'none'}`",
        f"- unrecoverable_feature_columns: `{','.join(report['unrecoverable_feature_columns']) or 'none'}`",
        "",
        "## Source Coverage",
        "",
        f"- missing_legacy_files: `{len(report['missing_legacy_files'])}`",
        f"- missing_candidate_sample_ids: `{len(report['missing_candidate_sample_ids'])}`",
        f"- duplicate_candidate_sample_ids: `{len(report['duplicate_candidate_sample_ids'])}`",
        "",
        "## Notes",
        "",
        "- legacy_features are the primary source for text, geometry, and page-order context.",
        "- candidates TSV is used only for row/block alignment plus report metadata such as `risk_flags`.",
        "- `target_label=unknown`, `source_label=external_quality_candidate`, and `split=report` are metadata only and are not used as model features.",
        "- bridge-native feature defaults are currently empty; remaining boundary defaults come from the existing baseline_v3 builder itself.",
        f"- non-model report columns: `{','.join(report['non_model_report_columns'])}`",
    ]
    lines.append("")
    lines.append("## Missing Required Source Fields")
    lines.append("")
    if missing_fields:
        for field, count in sorted(missing_fields.items()):
            lines.append(f"- `{field}` = `{count}`")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Missing Legacy Files")
    lines.append("")
    if report["missing_legacy_files"]:
        for item in report["missing_legacy_files"][:20]:
            lines.append(f"- `{item}`")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Missing Candidate Sample IDs")
    lines.append("")
    if report["missing_candidate_sample_ids"]:
        for item in report["missing_candidate_sample_ids"][:20]:
            lines.append(f"- `{item}`")
    else:
        lines.append("- none")
    return "\n".join(lines)


def build_external_quality_features(
    *,
    candidates_tsv: Path,
    legacy_features_root: Path,
    output_features: Path,
    output_report: Path,
    output_json: Path,
    feature_set: str,
    source_dataset: str,
    split: str,
) -> dict[str, Any]:
    candidate_rows = read_tsv(candidates_tsv)
    if not candidate_rows:
        raise BridgeError(f"candidate TSV has no rows: {candidates_tsv}")

    candidate_order: list[str] = []
    candidate_by_sample: dict[str, dict[str, str]] = {}
    duplicate_candidate_sample_ids: list[str] = []
    row_ids: list[str] = []
    seen_row_ids: set[str] = set()
    for row in candidate_rows:
        sample_id = row.get("sample_id", "")
        row_id = row.get("row_id", "")
        if not sample_id or not row_id:
            raise BridgeError(
                f"candidate row missing row_id/sample_id in {candidates_tsv}: {row!r}"
            )
        if sample_id in candidate_by_sample:
            duplicate_candidate_sample_ids.append(sample_id)
            continue
        candidate_by_sample[sample_id] = row
        candidate_order.append(sample_id)
        if row_id not in seen_row_ids:
            seen_row_ids.add(row_id)
            row_ids.append(row_id)

    expected_columns = expected_feature_columns(feature_set)
    all_adapter_rows: list[dict[str, str]] = []
    matched_legacy_feature_rows = 0
    context_block_rows_used = 0
    missing_legacy_files: list[str] = []
    missing_required_field_counts: Counter[str] = Counter()

    for row_id in row_ids:
        legacy_path = legacy_path_for_row(legacy_features_root, row_id)
        if not legacy_path.is_file():
            missing_legacy_files.append(str(legacy_path))
            continue
        for legacy_row in read_tsv(legacy_path):
            if legacy_row.get("record_kind", "") != "block":
                continue
            sample_id = legacy_candidate_sample_id(row_id, legacy_row)
            missing_fields = missing_required_fields(legacy_row)
            if missing_fields:
                for field in missing_fields:
                    missing_required_field_counts[field] += 1
                continue
            is_candidate = sample_id in candidate_by_sample
            risk_flags = candidate_by_sample[sample_id].get("risk_flags", "") if is_candidate else ""
            all_adapter_rows.append(
                legacy_row_to_adapter(
                    row_id=row_id,
                    legacy_row=legacy_row,
                    source_dataset=source_dataset,
                    split=split,
                    risk_flags=risk_flags,
                    is_candidate=is_candidate,
                )
            )
            context_block_rows_used += 1
            if is_candidate:
                matched_legacy_feature_rows += 1

    if not all_adapter_rows:
        raise BridgeError("no usable legacy block rows found for feature bridge")

    built_rows = build_feature_rows(all_adapter_rows, feature_set)
    built_by_sample = {row["sample_id"]: row for row in built_rows}
    output_rows = [built_by_sample[sid] for sid in candidate_order if sid in built_by_sample]
    if not output_rows:
        raise BridgeError("bridge produced zero candidate feature rows")

    actual_columns = list(output_rows[0].keys())
    missing_feature_columns = [col for col in expected_columns if col not in actual_columns]
    extra_feature_columns = [col for col in actual_columns if col not in expected_columns]

    meta_columns = {
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
    expected_model_columns = [col for col in expected_columns if col not in meta_columns]
    actual_model_columns = [col for col in actual_columns if col not in meta_columns]
    missing_model_feature_columns = [
        col for col in expected_model_columns if col not in actual_model_columns
    ]
    extra_model_feature_columns = [
        col for col in actual_model_columns if col not in expected_model_columns
    ]

    write_tsv(output_features, output_rows, expected_columns)

    missing_candidate_sample_ids = [sid for sid in candidate_order if sid not in built_by_sample]
    compatibility_status = (
        "ready"
        if not missing_feature_columns
        and not extra_feature_columns
        and not missing_model_feature_columns
        and not extra_model_feature_columns
        else "not_ready"
    )
    report: dict[str, Any] = {
        "feature_set": feature_set,
        "source_dataset": source_dataset,
        "split": split,
        "compatibility_status": compatibility_status,
        "candidate_rows": len(candidate_order),
        "unique_row_ids": len(row_ids),
        "matched_legacy_feature_rows": matched_legacy_feature_rows,
        "context_block_rows_used": context_block_rows_used,
        "output_feature_rows": len(output_rows),
        "feature_column_count": len(actual_columns),
        "model_feature_column_count": len(actual_model_columns),
        "missing_feature_columns": missing_feature_columns,
        "extra_feature_columns": extra_feature_columns,
        "missing_model_feature_columns": missing_model_feature_columns,
        "extra_model_feature_columns": extra_model_feature_columns,
        "defaulted_feature_columns": [],
        "unrecoverable_feature_columns": [],
        "missing_legacy_files": missing_legacy_files,
        "missing_candidate_sample_ids": missing_candidate_sample_ids,
        "duplicate_candidate_sample_ids": duplicate_candidate_sample_ids,
        "missing_required_field_counts": dict(sorted(missing_required_field_counts.items())),
        "non_model_report_columns": NON_MODEL_REPORT_COLUMNS,
        "output_features": str(output_features),
        "output_report": str(output_report),
        "output_json": str(output_json),
    }

    output_report.parent.mkdir(parents=True, exist_ok=True)
    output_report.write_text(build_report_markdown(report), encoding="utf-8")
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report


def main() -> int:
    args = parse_args()
    candidates_tsv = Path(args.candidates_tsv).resolve()
    legacy_features_root = (
        Path(args.legacy_features_root).resolve()
        if args.legacy_features_root
        else candidates_tsv.parent / "rows"
    )
    output_features = Path(args.output_features).resolve()
    output_report = Path(args.output_report).resolve()
    output_json = (
        Path(args.output_json).resolve()
        if args.output_json
        else output_report.with_suffix(".json")
    )
    report = build_external_quality_features(
        candidates_tsv=candidates_tsv,
        legacy_features_root=legacy_features_root,
        output_features=output_features,
        output_report=output_report,
        output_json=output_json,
        feature_set=args.feature_set,
        source_dataset=args.source_dataset,
        split=args.split,
    )
    print(
        "external quality feature bridge complete: "
        f"status={report['compatibility_status']} "
        f"candidates={report['candidate_rows']} "
        f"matched={report['matched_legacy_feature_rows']} "
        f"rows={report['output_feature_rows']} "
        f"output={output_features}"
    )
    return 0 if report["compatibility_status"] == "ready" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BridgeError as exc:
        print(f"external quality feature bridge failed: {exc}")
        raise SystemExit(1)
