#!/usr/bin/env python3

"""Adapt main-repo PDF v2 EvidenceRow exports into quality-lab readiness rows."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ADAPTER_VERSION = "pdf_v2_evidence_row_adapter_v1"

INPUT_FIELDS = [
    "schema_version",
    "row_family",
    "doc_id",
    "row_id",
    "task",
    "split",
    "page_index",
    "candidate_id",
    "prev_candidate_id",
    "next_candidate_id",
    "object_kind",
    "object_ref",
    "asset_ref",
    "evidence_kind",
    "subject_id",
    "related_id",
    "text",
    "normalized_text",
    "nearby_text",
    "current_rule_decision",
    "current_rule_confidence",
    "weak_label",
    "gold_label",
    "label_source",
    "risk_tags",
    "reason_tags",
    "source_refs",
    "blockers",
    "extra",
]

OUTPUT_FIELDS = [
    "adapter_version",
    "source_format",
    "source_schema_version",
    "source_doc_id",
    "group_id",
    "source_row_id",
    "page_index",
    "split",
    "source_task",
    "target_model",
    "target_kind",
    "lane_status",
    "evidence_kind",
    "subject_id",
    "related_id",
    "text",
    "normalized_text",
    "confidence",
    "weak_label",
    "gold_label",
    "label_source",
    "label_status",
    "reason_tags",
    "risk_tags",
    "blockers",
    "source_refs",
    "extra",
    "notes",
]

ROUTE_TABLE = {
    "cross_page_boundary": {
        "source_task": "semantic_arbitration",
        "target_model": "semantic_arbitration",
        "target_kind": "merge_split_hint",
        "lane_status": "future_tree",
    },
    "image_text_boundary": {
        "source_task": "semantic_arbitration",
        "target_model": "semantic_arbitration",
        "target_kind": "caption_relation_hint",
        "lane_status": "future_tree",
    },
    "heading_boundary": {
        "source_task": "semantic_arbitration",
        "target_model": "semantic_arbitration",
        "target_kind": "heading_boundary_hint",
        "lane_status": "future_tree",
    },
    "header_footer_variant": {
        "source_task": "layout_recovery",
        "target_model": "layout_recovery",
        "target_kind": "header_footer_region_hint",
        "lane_status": "existing_tree",
    },
    "column_layout": {
        "source_task": "layout_recovery",
        "target_model": "layout_recovery",
        "target_kind": "column_reading_order_hint",
        "lane_status": "existing_tree",
    },
}

NON_LABEL_SOURCES = {"", "none"}


class AdapterError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Adapt main-repo PDF v2 EvidenceRow TSV/JSONL exports into "
            "quality-lab training-readiness rows."
        )
    )
    parser.add_argument("--input", required=True, help="Path to flat TSV or JSONL export.")
    parser.add_argument("--output", required=True, help="Path to output adapter TSV.")
    parser.add_argument(
        "--summary-output",
        help="Optional JSON summary path for route and label counts.",
    )
    parser.add_argument(
        "--format",
        choices=("auto", "tsv", "jsonl"),
        default="auto",
        help="Input format. Defaults to auto by file suffix.",
    )
    parser.add_argument(
        "--split-override",
        help="Optional split value to apply to every adapted row.",
    )
    return parser.parse_args()


def detect_format(path: Path, requested: str) -> str:
    if requested != "auto":
        return requested
    suffix = path.suffix.lower()
    if suffix == ".tsv":
        return "tsv"
    if suffix == ".jsonl":
        return "jsonl"
    raise AdapterError(
        f"cannot infer format from suffix for {path}; pass --format tsv|jsonl"
    )


def read_rows(path: Path, input_format: str) -> list[dict[str, Any]]:
    if input_format == "tsv":
        return read_tsv_rows(path)
    if input_format == "jsonl":
        return read_jsonl_rows(path)
    raise AdapterError(f"unsupported input format: {input_format}")


def read_tsv_rows(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise AdapterError(f"missing input file: {path}")
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != INPUT_FIELDS:
            raise AdapterError(
                f"unexpected TSV header in {path}: {reader.fieldnames!r}"
            )
        for line_no, row in enumerate(reader, start=2):
            rows.append(normalize_tsv_row(row, f"{path}:{line_no}"))
    return rows


def read_jsonl_rows(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise AdapterError(f"missing input file: {path}")
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise AdapterError(f"invalid JSON at {path}:{line_no}: {exc}") from exc
            rows.append(normalize_jsonl_row(payload, f"{path}:{line_no}"))
    return rows


def normalize_tsv_row(row: dict[str, str | None], context: str) -> dict[str, Any]:
    raw = {key: "" if value is None else value for key, value in row.items()}
    return {
        "schema_version": raw["schema_version"],
        "row_family": raw["row_family"],
        "doc_id": raw["doc_id"],
        "row_id": raw["row_id"],
        "task": raw["task"],
        "split": raw["split"],
        "page_index": raw["page_index"],
        "evidence_kind": raw["evidence_kind"],
        "subject_id": raw["subject_id"],
        "related_id": raw["related_id"],
        "text": raw["text"],
        "normalized_text": raw["normalized_text"],
        "confidence": parse_confidence(raw["current_rule_confidence"], context),
        "weak_label": raw["weak_label"],
        "gold_label": raw["gold_label"],
        "label_source": raw["label_source"],
        "reason_tags": split_list_field(raw["reason_tags"]),
        "risk_tags": split_list_field(raw["risk_tags"]),
        "source_refs": split_list_field(raw["source_refs"]),
        "blockers": split_list_field(raw["blockers"]),
        "extra": raw["extra"],
    }


def normalize_jsonl_row(payload: Any, context: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise AdapterError(f"expected object at {context}")
    missing = [field for field in INPUT_FIELDS if field not in payload]
    if missing:
        raise AdapterError(f"missing JSONL fields at {context}: {missing!r}")
    return {
        "schema_version": string_field(payload["schema_version"], "schema_version", context),
        "row_family": string_field(payload["row_family"], "row_family", context),
        "doc_id": string_field(payload["doc_id"], "doc_id", context),
        "row_id": string_field(payload["row_id"], "row_id", context),
        "task": string_field(payload["task"], "task", context),
        "split": string_field(payload["split"], "split", context),
        "page_index": string_field(payload["page_index"], "page_index", context),
        "evidence_kind": string_field(payload["evidence_kind"], "evidence_kind", context),
        "subject_id": string_field(payload["subject_id"], "subject_id", context),
        "related_id": string_field(payload["related_id"], "related_id", context),
        "text": string_field(payload["text"], "text", context),
        "normalized_text": string_field(
            payload["normalized_text"], "normalized_text", context
        ),
        "confidence": parse_confidence(
            string_field(
                payload["current_rule_confidence"],
                "current_rule_confidence",
                context,
            ),
            context,
        ),
        "weak_label": string_field(payload["weak_label"], "weak_label", context),
        "gold_label": string_field(payload["gold_label"], "gold_label", context),
        "label_source": string_field(payload["label_source"], "label_source", context),
        "reason_tags": list_field(payload["reason_tags"], "reason_tags", context),
        "risk_tags": list_field(payload["risk_tags"], "risk_tags", context),
        "source_refs": list_field(payload["source_refs"], "source_refs", context),
        "blockers": list_field(payload["blockers"], "blockers", context),
        "extra": string_field(payload["extra"], "extra", context),
    }


def string_field(value: Any, field_name: str, context: str) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        raise AdapterError(f"unexpected boolean for {field_name} at {context}")
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return value
    raise AdapterError(f"unexpected type for {field_name} at {context}: {type(value)!r}")


def list_field(value: Any, field_name: str, context: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise AdapterError(f"expected list for {field_name} at {context}")
    out: list[str] = []
    for item in value:
        out.append(string_field(item, field_name, context))
    return out


def split_list_field(value: str) -> list[str]:
    if value == "":
        return []
    return [part for part in value.split("|") if part != ""]


def parse_confidence(value: str, context: str) -> str:
    try:
        float(value or "0")
    except ValueError as exc:
        raise AdapterError(f"invalid confidence at {context}: {value!r}") from exc
    return value


def is_reviewed_label_source(label_source: str) -> bool:
    lowered = label_source.lower()
    return (
        lowered.startswith("manual")
        or lowered.startswith("human_review")
        or lowered.startswith("reviewed")
        or lowered == "human_review"
    )


def determine_label_status(row: dict[str, Any]) -> str:
    weak_label = row["weak_label"]
    gold_label = row["gold_label"]
    label_source = row["label_source"]

    if weak_label and gold_label:
        raise AdapterError(
            f"row {row['row_id']} carries both weak_label and gold_label; "
            "keep them separate in the shared adapter contract"
        )
    if gold_label:
        if not is_reviewed_label_source(label_source):
            raise AdapterError(
                f"row {row['row_id']} has gold_label without reviewed/manual "
                f"label_source: {label_source!r}"
            )
        return "gold"
    if weak_label:
        if label_source in NON_LABEL_SOURCES or is_reviewed_label_source(label_source):
            raise AdapterError(
                f"row {row['row_id']} has weak_label without explicit weak "
                f"label_source: {label_source!r}"
            )
        return "weak"
    if label_source not in NON_LABEL_SOURCES:
        return "unlabeled_with_source"
    return "unlabeled"


def doc_id_needs_privacy_review(doc_id: str) -> bool:
    return doc_id.startswith("/") or "\\" in doc_id or "/" in doc_id


def adapt_rows(
    rows: list[dict[str, Any]],
    input_format: str,
    split_override: str | None,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    adapted_rows: list[dict[str, str]] = []
    route_counter: Counter[str] = Counter()
    kind_counter: Counter[str] = Counter()
    label_counter: Counter[str] = Counter()
    doc_groups: set[str] = set()
    split_values: set[str] = set()
    doc_splits: dict[str, set[str]] = defaultdict(set)
    ignored_non_evidence = 0

    for row in rows:
        if row["row_family"] != "EvidenceRow":
            ignored_non_evidence += 1
            continue

        route = ROUTE_TABLE.get(row["evidence_kind"])
        if route is None:
            raise AdapterError(
                f"row {row['row_id']} has unknown evidence_kind: {row['evidence_kind']!r}"
            )
        if row["task"] != route["source_task"]:
            raise AdapterError(
                f"row {row['row_id']} task/evidence mismatch: "
                f"task={row['task']!r} evidence_kind={row['evidence_kind']!r}"
            )
        if row["subject_id"] == "":
            raise AdapterError(f"row {row['row_id']} is missing subject_id")

        split_value = split_override if split_override is not None else (row["split"] or "unknown")
        label_status = determine_label_status(row)
        notes: list[str] = []
        if doc_id_needs_privacy_review(row["doc_id"]):
            notes.append("doc_id_needs_privacy_review")
        if split_value == "unknown":
            notes.append("split_unassigned")
        if label_status == "unlabeled_with_source":
            notes.append("label_source_without_label")

        adapted = {
            "adapter_version": ADAPTER_VERSION,
            "source_format": input_format,
            "source_schema_version": row["schema_version"],
            "source_doc_id": row["doc_id"],
            "group_id": row["doc_id"],
            "source_row_id": row["row_id"],
            "page_index": row["page_index"],
            "split": split_value,
            "source_task": row["task"],
            "target_model": route["target_model"],
            "target_kind": route["target_kind"],
            "lane_status": route["lane_status"],
            "evidence_kind": row["evidence_kind"],
            "subject_id": row["subject_id"],
            "related_id": row["related_id"],
            "text": row["text"],
            "normalized_text": row["normalized_text"],
            "confidence": row["confidence"],
            "weak_label": row["weak_label"],
            "gold_label": row["gold_label"],
            "label_source": row["label_source"],
            "label_status": label_status,
            "reason_tags": join_list(row["reason_tags"]),
            "risk_tags": join_list(row["risk_tags"]),
            "blockers": join_list(row["blockers"]),
            "source_refs": join_list(row["source_refs"]),
            "extra": row["extra"],
            "notes": join_list(notes),
        }
        adapted_rows.append(adapted)
        route_counter[route["target_model"]] += 1
        kind_counter[row["evidence_kind"]] += 1
        label_counter[label_status] += 1
        doc_groups.add(adapted["group_id"])
        split_values.add(split_value)
        if split_value != "unknown":
            doc_splits[adapted["group_id"]].add(split_value)

    if not adapted_rows:
        raise AdapterError("no EvidenceRow rows found in input export")

    split_leakage = {
        group_id: sorted(values)
        for group_id, values in doc_splits.items()
        if len(values) > 1
    }
    if split_leakage:
        raise AdapterError(
            "document-group split leakage detected: "
            + json.dumps(split_leakage, sort_keys=True)
        )

    summary = {
        "adapter_version": ADAPTER_VERSION,
        "input_row_count": len(rows),
        "evidence_row_count": len(adapted_rows),
        "ignored_non_evidence_row_count": ignored_non_evidence,
        "layout_recovery_row_count": route_counter["layout_recovery"],
        "semantic_arbitration_row_count": route_counter["semantic_arbitration"],
        "counts_by_evidence_kind": dict(sorted(kind_counter.items())),
        "counts_by_label_status": dict(sorted(label_counter.items())),
        "doc_group_count": len(doc_groups),
        "doc_groups": sorted(doc_groups),
        "grouped_split_ok": True,
        "split_values": sorted(split_values),
    }
    return adapted_rows, summary


def join_list(values: list[str]) -> str:
    return "|".join(value for value in values if value != "")


def write_output(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_summary(path: Path, summary: dict[str, Any], input_format: str, input_path: Path) -> None:
    payload = {
        **summary,
        "input_format": input_format,
        "input_path": str(input_path),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    summary_path = Path(args.summary_output) if args.summary_output else None

    try:
        input_format = detect_format(input_path, args.format)
        rows = read_rows(input_path, input_format)
        adapted_rows, summary = adapt_rows(rows, input_format, args.split_override)
        write_output(output_path, adapted_rows)
        if summary_path is not None:
            write_summary(summary_path, summary, input_format, input_path)
    except AdapterError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
