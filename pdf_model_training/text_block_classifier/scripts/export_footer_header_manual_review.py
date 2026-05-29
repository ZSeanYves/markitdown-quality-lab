#!/usr/bin/env python3
"""Export a report-only manual-review package for footer/header candidates."""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path


OUTPUT_FIELDS = [
    "review_id",
    "row_id",
    "sample_id",
    "source_pdf_id",
    "page_no",
    "block_id",
    "bbox",
    "text_preview",
    "gate_status",
    "gate_action",
    "gate_reason",
    "predicted_label",
    "confidence",
    "cooperative_score",
    "risk_flags",
    "review_bucket",
    "suggested_manual_label",
    "reviewer_decision",
    "reviewer_notes",
]

BODY_RISK_FLAGS = {
    "central_body_band",
    "sentence_like",
    "long_text",
    "long_word_count",
    "technical_sentence_guard",
}

CONFIDENCE_RE = re.compile(r"confidence<([0-9]+(?:\.[0-9]+)?)")


class ManualReviewExportError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a local-only manual-review package for footer_header_noise "
            "external-quality cooperative-gate outputs."
        )
    )
    parser.add_argument(
        "--candidates-tsv",
        required=True,
        help="external_quality_hint_candidates.tsv path.",
    )
    parser.add_argument(
        "--summary-tsv",
        required=True,
        help="external_quality_hint_summary.tsv path.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Output directory for local-only manual-review artifacts.",
    )
    parser.add_argument(
        "--max-text-chars",
        type=int,
        default=160,
        help="Maximum text preview length kept in exported review rows.",
    )
    parser.add_argument(
        "--include-status",
        default="emit,hard_conflict,high_confidence_no_override",
        help=(
            "Comma-separated review groups to export. Supported values: "
            "emit, hard_conflict, high_confidence_no_override"
        ),
    )
    parser.add_argument(
        "--top-near-miss",
        type=int,
        default=50,
        help="Maximum high-confidence no-override rows to include.",
    )
    return parser.parse_args()


def parse_list(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise ManualReviewExportError(f"missing TSV: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def as_float(raw: str, default: float = 0.0) -> float:
    try:
        return float(raw)
    except ValueError:
        return default


def truncate_text(text: str, limit: int) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: max(0, limit - 3)] + "..."


def risk_flag_set(row: dict[str, str]) -> set[str]:
    return {flag for flag in row.get("risk_flags", "").split(",") if flag}


def has_body_risk(row: dict[str, str]) -> bool:
    return bool(risk_flag_set(row) & BODY_RISK_FLAGS)


def is_page_number_like(text: str) -> bool:
    compact = text.strip()
    if compact in {"1", "2", "3", "4", "5"}:
        return True
    return False


def infer_confidence_threshold(rows: list[dict[str, str]]) -> float:
    for row in rows:
        if row.get("gate_status") != "blocked_model_confidence":
            continue
        match = CONFIDENCE_RE.search(row.get("gate_reason", ""))
        if match:
            return as_float(match.group(1), default=0.95)
    return 0.95


def high_confidence_cutoff(threshold: float) -> float:
    return max(0.90, threshold - 0.05)


def source_pdf_id(summary_row: dict[str, str] | None, row_id: str) -> str:
    if not summary_row:
        return row_id
    raw_path = summary_row.get("input_path", "").strip()
    if not raw_path:
        return row_id
    return Path(raw_path).stem or row_id


def near_miss_priority(
    row: dict[str, str],
    *,
    threshold: float,
    high_confidence_min: float,
) -> tuple[int, int, float, int, str]:
    confidence = as_float(row.get("model_confidence", "0"))
    preview_len = len(row.get("text_preview", ""))
    predicted_label = row.get("predicted_label", "")
    gate_status = row.get("gate_status", "")
    body_risk = has_body_risk(row)

    if predicted_label == "footer_header_noise" and gate_status == "blocked_model_confidence":
        return (0, 0 if confidence >= threshold - 0.02 else 1, -confidence, preview_len, row["sample_id"])
    if gate_status == "blocked_cooperative_score":
        return (1, 0, -confidence, preview_len, row["sample_id"])
    if confidence >= high_confidence_min:
        return (
            2,
            0 if not body_risk else 1,
            preview_len,
            -confidence,
            row["sample_id"],
        )
    return (3, 1 if body_risk else 0, -confidence, preview_len, row["sample_id"])


def review_bucket(
    row: dict[str, str],
    *,
    included_as: str,
    threshold: float,
) -> str:
    text = row.get("text_preview", "")
    confidence = as_float(row.get("model_confidence", "0"))
    status = row.get("gate_status", "")
    reason = row.get("gate_reason", "")

    if included_as == "emit":
        if is_page_number_like(text):
            return "emitted_page_number_like"
        return "emitted_edge_noise_like"
    if included_as == "hard_conflict":
        if "dense_edge_row_conflict" in reason:
            return "blocked_dense_edge_row"
        if has_body_risk(row):
            return "blocked_body_text_risk"
        return "other"
    if included_as == "high_confidence_no_override":
        if status == "blocked_model_confidence":
            if confidence >= threshold - 0.02:
                return "near_miss_high_confidence"
            return "blocked_low_confidence"
        if status == "label_not_allowed":
            if has_body_risk(row):
                return "blocked_body_text_risk"
            return "blocked_label_not_allowed"
        if has_body_risk(row):
            return "blocked_body_text_risk"
        return "other"
    return "other"


def suggested_manual_label(bucket: str) -> str:
    if bucket in {"emitted_page_number_like", "emitted_edge_noise_like"}:
        return "confirm_footer_header_noise"
    if bucket in {"blocked_dense_edge_row", "blocked_body_text_risk", "blocked_label_not_allowed"}:
        return "keep_no_override"
    if bucket in {"near_miss_high_confidence", "blocked_low_confidence"}:
        return "manual_review_needed"
    return "review_needed"


def build_review_row(
    *,
    review_index: int,
    row: dict[str, str],
    summary_row: dict[str, str] | None,
    included_as: str,
    threshold: float,
    max_text_chars: int,
) -> dict[str, str]:
    bucket = review_bucket(row, included_as=included_as, threshold=threshold)
    return {
        "review_id": f"review_{review_index:04d}",
        "row_id": row.get("row_id", ""),
        "sample_id": row.get("sample_id", ""),
        "source_pdf_id": source_pdf_id(summary_row, row.get("row_id", "")),
        "page_no": row.get("page_no", ""),
        "block_id": row.get("block_id", ""),
        "bbox": row.get("bbox", ""),
        "text_preview": truncate_text(row.get("text_preview", ""), max_text_chars),
        "gate_status": row.get("gate_status", ""),
        "gate_action": row.get("gate_action", ""),
        "gate_reason": row.get("gate_reason", ""),
        "predicted_label": row.get("predicted_label", ""),
        "confidence": row.get("model_confidence", ""),
        "cooperative_score": row.get("cooperative_score", ""),
        "risk_flags": row.get("risk_flags", ""),
        "review_bucket": bucket,
        "suggested_manual_label": suggested_manual_label(bucket),
        "reviewer_decision": "",
        "reviewer_notes": "",
    }


def collect_selected_rows(
    *,
    candidate_rows: list[dict[str, str]],
    include_status: set[str],
    threshold: float,
    top_near_miss: int,
) -> list[tuple[str, dict[str, str]]]:
    selected: list[tuple[str, dict[str, str]]] = []
    seen: set[str] = set()

    def add_rows(kind: str, rows: list[dict[str, str]]) -> None:
        for row in rows:
            sample_id = row.get("sample_id", "")
            if sample_id in seen:
                continue
            seen.add(sample_id)
            selected.append((kind, row))

    if "emit" in include_status:
        add_rows(
            "emit",
            [row for row in candidate_rows if row.get("gate_status") == "emit"],
        )
    if "hard_conflict" in include_status:
        add_rows(
            "hard_conflict",
            [
                row
                for row in candidate_rows
                if row.get("gate_status") == "blocked_hard_conflict"
            ],
        )
    if "high_confidence_no_override" in include_status and top_near_miss > 0:
        high_confidence_min = high_confidence_cutoff(threshold)
        near_miss_pool = [
            row
            for row in candidate_rows
            if row.get("gate_action") == "no_override"
            and (
                (
                    row.get("predicted_label") == "footer_header_noise"
                    and row.get("gate_status") == "blocked_model_confidence"
                    and as_float(row.get("model_confidence", "0")) >= high_confidence_min
                )
                or as_float(row.get("model_confidence", "0")) >= threshold
            )
        ]
        near_miss_pool.sort(
            key=lambda row: near_miss_priority(
                row,
                threshold=threshold,
                high_confidence_min=high_confidence_min,
            )
        )
        add_rows("high_confidence_no_override", near_miss_pool[:top_near_miss])
    return selected


def bucket_counts(rows: list[dict[str, str]]) -> Counter[str]:
    return Counter(row["review_bucket"] for row in rows)


def top_samples(rows: list[dict[str, str]], limit: int = 10) -> list[tuple[str, int]]:
    counts = Counter(row["row_id"] for row in rows)
    return counts.most_common(limit)


def summarize_rows(rows: list[dict[str, str]]) -> dict[str, object]:
    review_kind_counts = Counter()
    bucket_counter = Counter()
    long_text_count = 0
    central_body_count = 0
    for row in rows:
        bucket_counter[row["review_bucket"]] += 1
        if row["review_bucket"].startswith("emitted_"):
            review_kind_counts["emit_rows"] += 1
        elif row["gate_status"] == "blocked_hard_conflict":
            review_kind_counts["hard_conflict_rows"] += 1
        elif row["gate_action"] == "no_override":
            review_kind_counts["near_miss_rows"] += 1
        flags = {flag for flag in row["risk_flags"].split(",") if flag}
        if "long_text" in flags:
            long_text_count += 1
        if "central_body_band" in flags:
            central_body_count += 1
    return {
        "review_rows": len(rows),
        "bucket_counter": bucket_counter,
        "review_kind_counts": review_kind_counts,
        "long_text_count": long_text_count,
        "central_body_count": central_body_count,
        "top_samples": top_samples(rows),
    }


def render_markdown(
    *,
    rows: list[dict[str, str]],
    args: argparse.Namespace,
    threshold: float,
    summary_rows: list[dict[str, str]],
) -> str:
    summary = summarize_rows(rows)
    summary_lookup = {row["row_id"]: row for row in summary_rows}
    out: list[str] = []
    out.append("# Footer Header Manual Review")
    out.append("")
    out.append("## Export Config")
    out.append("")
    out.append(f"- candidates_tsv: `{Path(args.candidates_tsv).resolve()}`")
    out.append(f"- summary_tsv: `{Path(args.summary_tsv).resolve()}`")
    out.append(f"- include_status: `{args.include_status}`")
    out.append(f"- top_near_miss: `{args.top_near_miss}`")
    out.append(f"- max_text_chars: `{args.max_text_chars}`")
    out.append(f"- inferred_confidence_threshold: `{threshold:.2f}`")
    out.append("")
    out.append("## Totals")
    out.append("")
    out.append(f"- review_rows: `{summary['review_rows']}`")
    kind_counts = summary["review_kind_counts"]
    out.append(f"- emit_rows: `{kind_counts.get('emit_rows', 0)}`")
    out.append(f"- hard_conflict_rows: `{kind_counts.get('hard_conflict_rows', 0)}`")
    out.append(f"- near_miss_rows: `{kind_counts.get('near_miss_rows', 0)}`")
    out.append(f"- long_text_flagged_review_rows: `{summary['long_text_count']}`")
    out.append(f"- central_body_flagged_review_rows: `{summary['central_body_count']}`")
    out.append("- bucket_distribution:")
    for bucket, count in sorted(summary["bucket_counter"].items()):
        out.append(f"  - `{bucket}` = `{count}`")
    out.append("- top_samples:")
    for row_id, count in summary["top_samples"]:
        out.append(f"  - `{row_id}` = `{count}`")
    out.append("")

    sections = [
        ("Emit Rows", [row for row in rows if row["review_bucket"].startswith("emitted_")]),
        (
            "Hard Conflict Rows",
            [row for row in rows if row["gate_status"] == "blocked_hard_conflict"],
        ),
        (
            "High-Confidence No-Override Rows",
            [row for row in rows if row["gate_action"] == "no_override"],
        ),
    ]
    for title, section_rows in sections:
        out.append(f"## {title}")
        out.append("")
        if not section_rows:
            out.append("- none")
            out.append("")
            continue
        for row in section_rows:
            row_summary = summary_lookup.get(row["row_id"], {})
            out.append(
                f"- `{row['review_id']}` `{row['row_id']}` `{row['sample_id']}` "
                f"page=`{row['page_no']}` block=`{row['block_id']}` "
                f"pred=`{row['predicted_label']}` conf=`{row['confidence']}` "
                f"gate=`{row['gate_status']}` bucket=`{row['review_bucket']}` "
                f"risk=`{row['risk_flags'] or 'none'}` text=`{row['text_preview']}`"
            )
            report_path = row_summary.get("report_path", "")
            if report_path:
                out.append(f"  report: `{report_path}`")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def main() -> None:
    args = parse_args()
    include_status = set(parse_list(args.include_status))
    allowed_status = {"emit", "hard_conflict", "high_confidence_no_override"}
    unknown = include_status - allowed_status
    if unknown:
        raise ManualReviewExportError(
            f"unsupported include-status values: {sorted(unknown)}"
        )

    candidate_rows = read_tsv(Path(args.candidates_tsv).resolve())
    summary_rows = read_tsv(Path(args.summary_tsv).resolve())
    summary_lookup = {row["row_id"]: row for row in summary_rows}
    threshold = infer_confidence_threshold(candidate_rows)
    selected_rows = collect_selected_rows(
        candidate_rows=candidate_rows,
        include_status=include_status,
        threshold=threshold,
        top_near_miss=args.top_near_miss,
    )

    review_rows = [
        build_review_row(
            review_index=index,
            row=row,
            summary_row=summary_lookup.get(row.get("row_id", "")),
            included_as=kind,
            threshold=threshold,
            max_text_chars=args.max_text_chars,
        )
        for index, (kind, row) in enumerate(selected_rows, start=1)
    ]

    output_dir = Path(args.output_dir).resolve()
    write_tsv(output_dir / "footer_header_manual_review.tsv", review_rows)
    write_text(
        output_dir / "footer_header_manual_review.md",
        render_markdown(
            rows=review_rows,
            args=args,
            threshold=threshold,
            summary_rows=summary_rows,
        ),
    )


if __name__ == "__main__":
    main()
