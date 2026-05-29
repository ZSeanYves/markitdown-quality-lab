#!/usr/bin/env python3
"""Summarize footer/header manual-review decisions for report-only audits."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


REQUIRED_FIELDS = [
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

SUMMARY_FIELDS = [
    "section",
    "item",
    "count",
    "rate",
    "denominator",
    "notes",
]

EMIT_DECISIONS = {"accept", "reject", "unsure"}
BLOCKED_DECISIONS = {"keep_blocked", "should_emit", "needs_new_guard", "out_of_scope"}
ALLOWED_DECISIONS = EMIT_DECISIONS | BLOCKED_DECISIONS | {"blank"}
ACTIONABLE_DECISIONS = {"reject", "should_emit"}


class ManualReviewSummaryError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize reviewer decisions from footer_header_noise "
            "manual-review TSV exports."
        )
    )
    parser.add_argument(
        "--review-tsv",
        required=True,
        help="Path to footer_header_manual_review.tsv.",
    )
    parser.add_argument(
        "--output-report",
        required=True,
        help="Path to the Markdown summary report to write.",
    )
    parser.add_argument(
        "--output-summary-tsv",
        required=True,
        help="Path to the machine-readable summary TSV to write.",
    )
    return parser.parse_args()


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise ManualReviewSummaryError(f"missing review TSV: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = reader.fieldnames or []
        missing = [field for field in REQUIRED_FIELDS if field not in fieldnames]
        if missing:
            raise ManualReviewSummaryError(
                f"review TSV is missing required columns: {', '.join(missing)}"
            )
        return list(reader)


def write_tsv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def normalize_decision(raw: str) -> str:
    decision = raw.strip().lower()
    if not decision or decision == "blank":
        return "blank"
    if decision not in ALLOWED_DECISIONS:
        allowed = ", ".join(sorted(ALLOWED_DECISIONS))
        raise ManualReviewSummaryError(
            f"unsupported reviewer_decision {raw!r}; expected one of: {allowed}"
        )
    return decision


def gate_family(gate_status: str) -> str:
    if gate_status.strip() == "emit":
        return "emit"
    return "blocked"


def validate_decision(row: dict[str, str], decision: str) -> None:
    if decision == "blank":
        return
    family = gate_family(row.get("gate_status", ""))
    allowed = EMIT_DECISIONS if family == "emit" else BLOCKED_DECISIONS
    if decision not in allowed:
        raise ManualReviewSummaryError(
            "decision "
            f"{decision!r} is invalid for gate_status={row.get('gate_status', '')!r} "
            f"on review_id={row.get('review_id', '')!r}"
        )


def sort_counter(counter: Counter[str]) -> list[tuple[str, int]]:
    return sorted(counter.items(), key=lambda item: (-item[1], item[0]))


def rate_text(count: int, denominator: int) -> str:
    if denominator <= 0:
        return "n/a"
    return f"{count / denominator:.4f}"


def tsv_row(
    section: str,
    item: str,
    *,
    count: int | str = "",
    denominator: int | str = "",
    rate: str = "",
    notes: str = "",
) -> dict[str, str]:
    return {
        "section": section,
        "item": item,
        "count": str(count),
        "rate": rate,
        "denominator": str(denominator),
        "notes": notes,
    }


def count_rows(rows: list[dict[str, str]], *, decision: str | None = None) -> int:
    if decision is None:
        return len(rows)
    return sum(1 for row in rows if row["normalized_reviewer_decision"] == decision)


def filter_rows(
    rows: list[dict[str, str]],
    *,
    decisions: set[str] | None = None,
    review_bucket: str | None = None,
    gate_status: str | None = None,
) -> list[dict[str, str]]:
    filtered = []
    for row in rows:
        if decisions is not None and row["normalized_reviewer_decision"] not in decisions:
            continue
        if review_bucket is not None and row.get("review_bucket", "") != review_bucket:
            continue
        if gate_status is not None and row.get("gate_status", "") != gate_status:
            continue
        filtered.append(row)
    return filtered


def top_samples(
    rows: list[dict[str, str]],
    *,
    decisions: set[str],
    limit: int = 5,
) -> list[tuple[str, int, Counter[str]]]:
    sample_counts: dict[str, Counter[str]] = {}
    for row in rows:
        decision = row["normalized_reviewer_decision"]
        if decision not in decisions:
            continue
        sample_id = row.get("sample_id", "").strip() or "<blank>"
        sample_counts.setdefault(sample_id, Counter())[decision] += 1

    ranked = []
    for sample_id, counter in sample_counts.items():
        ranked.append((sample_id, sum(counter.values()), counter))
    ranked.sort(key=lambda item: (-item[1], item[0]))
    return ranked[:limit]


def recommendation(
    rows: list[dict[str, str]],
) -> tuple[str, list[str]]:
    total_rows = len(rows)
    reviewed_rows = sum(
        1 for row in rows if row["normalized_reviewer_decision"] != "blank"
    )
    decision_counts = Counter(row["normalized_reviewer_decision"] for row in rows)
    should_emit_rows = filter_rows(rows, decisions={"should_emit"})
    near_miss_should_emit = len(
        filter_rows(
            rows,
            decisions={"should_emit"},
            review_bucket="near_miss_high_confidence",
            gate_status="blocked_model_confidence",
        )
    )

    if reviewed_rows == 0:
        return (
            "waiting_for_manual_review",
            [
                "all reviewer_decision cells are blank",
                "fill reviewer_decision and rerun the summary before proposing changes",
            ],
        )

    if decision_counts["reject"] > 0 or decision_counts["needs_new_guard"] > 0:
        reasons = []
        if decision_counts["reject"] > 0:
            reasons.append(f"reject={decision_counts['reject']}")
        if decision_counts["needs_new_guard"] > 0:
            reasons.append(f"needs_new_guard={decision_counts['needs_new_guard']}")
        return (
            "refine_guard",
            ["manual review found emit false positives or missing guard coverage"]
            + reasons,
        )

    if decision_counts["should_emit"] > 0:
        all_threshold_near_miss = (
            len(should_emit_rows) == near_miss_should_emit
            and all(
                row.get("gate_status", "") == "blocked_model_confidence"
                for row in should_emit_rows
            )
        )
        if all_threshold_near_miss:
            return (
                "adjust_threshold",
                [
                    "all should_emit rows are blocked_model_confidence near misses",
                    f"near_miss_should_emit={near_miss_should_emit}",
                ],
            )
        return (
            "refine_guard",
            [
                "should_emit rows exist outside the simple near-miss threshold bucket",
                f"should_emit={decision_counts['should_emit']}",
            ],
        )

    if decision_counts["unsure"] > 0:
        return (
            "pause",
            [
                "manual review still has unresolved emit rows",
                f"unsure={decision_counts['unsure']}",
            ],
        )

    if reviewed_rows == total_rows:
        return (
            "expand_benchmark",
            [
                "all review rows are filled with no reject/should_emit/new guard requests",
                "current profile can stay report-only while benchmark coverage grows",
            ],
        )

    return (
        "keep_profile_unchanged",
        [
            "reviewed subset is clean so far",
            "finish remaining rows before considering a larger benchmark",
        ],
    )


def summarize(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], str]:
    for row in rows:
        decision = normalize_decision(row.get("reviewer_decision", ""))
        row["normalized_reviewer_decision"] = decision
        validate_decision(row, decision)

    total_rows = len(rows)
    reviewed_rows = sum(1 for row in rows if row["normalized_reviewer_decision"] != "blank")
    blank_rows = total_rows - reviewed_rows

    emit_rows = [row for row in rows if gate_family(row.get("gate_status", "")) == "emit"]
    blocked_rows = [row for row in rows if gate_family(row.get("gate_status", "")) == "blocked"]
    reviewed_emit_rows = [
        row for row in emit_rows if row["normalized_reviewer_decision"] != "blank"
    ]
    reviewed_blocked_rows = [
        row for row in blocked_rows if row["normalized_reviewer_decision"] != "blank"
    ]

    gate_status_counts = Counter((row.get("gate_status") or "").strip() or "<blank>" for row in rows)
    review_bucket_counts = Counter((row.get("review_bucket") or "").strip() or "<blank>" for row in rows)
    decision_counts = Counter(row["normalized_reviewer_decision"] for row in rows)

    emit_decision_counts = Counter(
        row["normalized_reviewer_decision"] for row in reviewed_emit_rows
    )
    blocked_decision_counts = Counter(
        row["normalized_reviewer_decision"] for row in reviewed_blocked_rows
    )

    reject_rows = filter_rows(rows, decisions={"reject"})
    should_emit_rows = filter_rows(rows, decisions={"should_emit"})
    new_guard_rows = filter_rows(rows, decisions={"needs_new_guard"})
    near_miss_should_emit = len(
        filter_rows(
            rows,
            decisions={"should_emit"},
            review_bucket="near_miss_high_confidence",
            gate_status="blocked_model_confidence",
        )
    )

    reject_bucket_counts = Counter(row.get("review_bucket", "") or "<blank>" for row in reject_rows)
    should_emit_bucket_counts = Counter(
        row.get("review_bucket", "") or "<blank>" for row in should_emit_rows
    )
    guard_reason_counts = Counter(row.get("gate_reason", "") or "<blank>" for row in new_guard_rows)
    actionable_samples = top_samples(rows, decisions=ACTIONABLE_DECISIONS)

    recommended_action, action_reasons = recommendation(rows)

    summary_rows: list[dict[str, str]] = []
    summary_rows.extend(
        [
            tsv_row(
                "overview",
                "total_rows",
                count=total_rows,
                denominator=total_rows,
                rate=rate_text(total_rows, total_rows),
            ),
            tsv_row(
                "overview",
                "reviewed_rows",
                count=reviewed_rows,
                denominator=total_rows,
                rate=rate_text(reviewed_rows, total_rows),
            ),
            tsv_row(
                "overview",
                "blank_rows",
                count=blank_rows,
                denominator=total_rows,
                rate=rate_text(blank_rows, total_rows),
            ),
            tsv_row(
                "overview",
                "emit_rows",
                count=len(emit_rows),
                denominator=total_rows,
                rate=rate_text(len(emit_rows), total_rows),
            ),
            tsv_row(
                "overview",
                "blocked_rows",
                count=len(blocked_rows),
                denominator=total_rows,
                rate=rate_text(len(blocked_rows), total_rows),
            ),
        ]
    )

    for key, count in sort_counter(gate_status_counts):
        summary_rows.append(
            tsv_row(
                "gate_status",
                key,
                count=count,
                denominator=total_rows,
                rate=rate_text(count, total_rows),
            )
        )

    for key, count in sort_counter(review_bucket_counts):
        summary_rows.append(
            tsv_row(
                "review_bucket",
                key,
                count=count,
                denominator=total_rows,
                rate=rate_text(count, total_rows),
            )
        )

    for key, count in sort_counter(decision_counts):
        summary_rows.append(
            tsv_row(
                "reviewer_decision",
                key,
                count=count,
                denominator=total_rows,
                rate=rate_text(count, total_rows),
            )
        )

    for key in ["accept", "reject", "unsure", "blank"]:
        count = emit_decision_counts.get(key, 0)
        if key == "blank":
            count = len(emit_rows) - len(reviewed_emit_rows)
        summary_rows.append(
            tsv_row(
                "emit_review",
                key,
                count=count,
                denominator=len(emit_rows),
                rate=rate_text(count, len(emit_rows)),
                notes="rate over total emit rows",
            )
        )

    for key in ["keep_blocked", "should_emit", "needs_new_guard", "out_of_scope", "blank"]:
        count = blocked_decision_counts.get(key, 0)
        if key == "blank":
            count = len(blocked_rows) - len(reviewed_blocked_rows)
        summary_rows.append(
            tsv_row(
                "blocked_review",
                key,
                count=count,
                denominator=len(blocked_rows),
                rate=rate_text(count, len(blocked_rows)),
                notes="rate over total blocked rows",
            )
        )

    summary_rows.extend(
        [
            tsv_row(
                "focus",
                "near_miss_should_emit",
                count=near_miss_should_emit,
                denominator=total_rows,
                rate=rate_text(near_miss_should_emit, total_rows),
            ),
            tsv_row(
                "focus",
                "new_guard_requests",
                count=len(new_guard_rows),
                denominator=total_rows,
                rate=rate_text(len(new_guard_rows), total_rows),
            ),
        ]
    )

    for key, count in sort_counter(reject_bucket_counts):
        summary_rows.append(
            tsv_row(
                "reject_bucket",
                key,
                count=count,
                denominator=len(reject_rows),
                rate=rate_text(count, len(reject_rows)),
            )
        )

    for key, count in sort_counter(should_emit_bucket_counts):
        summary_rows.append(
            tsv_row(
                "should_emit_bucket",
                key,
                count=count,
                denominator=len(should_emit_rows),
                rate=rate_text(count, len(should_emit_rows)),
            )
        )

    for key, count in sort_counter(guard_reason_counts):
        summary_rows.append(
            tsv_row(
                "new_guard_reason",
                key,
                count=count,
                denominator=len(new_guard_rows),
                rate=rate_text(count, len(new_guard_rows)),
            )
        )

    if actionable_samples:
        for sample_id, count, counter in actionable_samples:
            notes = ";".join(
                f"{decision}={counter.get(decision, 0)}"
                for decision in sorted(ACTIONABLE_DECISIONS)
                if counter.get(decision, 0) > 0
            )
            summary_rows.append(
                tsv_row(
                    "top_actionable_sample",
                    sample_id,
                    count=count,
                    denominator=len(reject_rows) + len(should_emit_rows),
                    rate=rate_text(count, len(reject_rows) + len(should_emit_rows)),
                    notes=notes,
                )
            )
    else:
        summary_rows.append(
            tsv_row(
                "top_actionable_sample",
                "none",
                count=0,
                denominator=0,
                rate="n/a",
                notes="no reject or should_emit rows",
            )
        )

    summary_rows.append(
        tsv_row(
            "recommendation",
            recommended_action,
            notes="; ".join(action_reasons),
        )
    )

    report_lines = [
        "# Footer Header Manual Review Summary",
        "",
        "## Inputs",
        f"- review_tsv: `{rows[0].get('__review_tsv__', '') if rows else ''}`",
        "",
        "## Overview",
        f"- total_rows: `{total_rows}`",
        f"- reviewed_rows: `{reviewed_rows}`",
        f"- blank_rows: `{blank_rows}`",
        f"- emit_rows: `{len(emit_rows)}`",
        f"- blocked_rows: `{len(blocked_rows)}`",
        f"- recommendation: `{recommended_action}`",
    ]

    if action_reasons:
        report_lines.append("- recommendation_reasons:")
        for reason in action_reasons:
            report_lines.append(f"  - {reason}")

    report_lines.extend(
        [
            "",
            "## By Gate Status",
        ]
    )
    for key, count in sort_counter(gate_status_counts):
        report_lines.append(f"- `{key}` = `{count}`")

    report_lines.extend(
        [
            "",
            "## By Review Bucket",
        ]
    )
    for key, count in sort_counter(review_bucket_counts):
        report_lines.append(f"- `{key}` = `{count}`")

    report_lines.extend(
        [
            "",
            "## By Reviewer Decision",
        ]
    )
    for key, count in sort_counter(decision_counts):
        report_lines.append(f"- `{key}` = `{count}`")

    report_lines.extend(
        [
            "",
            "## Decision Rates",
            f"- emit_accept_rate: `{emit_decision_counts.get('accept', 0)}` / `{len(emit_rows)}` (`{rate_text(emit_decision_counts.get('accept', 0), len(emit_rows))}`)",
            f"- emit_reject_rate: `{emit_decision_counts.get('reject', 0)}` / `{len(emit_rows)}` (`{rate_text(emit_decision_counts.get('reject', 0), len(emit_rows))}`)",
            f"- emit_unsure_rate: `{emit_decision_counts.get('unsure', 0)}` / `{len(emit_rows)}` (`{rate_text(emit_decision_counts.get('unsure', 0), len(emit_rows))}`)",
            f"- blocked_keep_blocked_rate: `{blocked_decision_counts.get('keep_blocked', 0)}` / `{len(blocked_rows)}` (`{rate_text(blocked_decision_counts.get('keep_blocked', 0), len(blocked_rows))}`)",
            f"- blocked_should_emit_rate: `{blocked_decision_counts.get('should_emit', 0)}` / `{len(blocked_rows)}` (`{rate_text(blocked_decision_counts.get('should_emit', 0), len(blocked_rows))}`)",
            f"- blocked_needs_new_guard_rate: `{blocked_decision_counts.get('needs_new_guard', 0)}` / `{len(blocked_rows)}` (`{rate_text(blocked_decision_counts.get('needs_new_guard', 0), len(blocked_rows))}`)",
            f"- blocked_out_of_scope_rate: `{blocked_decision_counts.get('out_of_scope', 0)}` / `{len(blocked_rows)}` (`{rate_text(blocked_decision_counts.get('out_of_scope', 0), len(blocked_rows))}`)",
            f"- waiting_blank_rate: `{blank_rows}` / `{total_rows}` (`{rate_text(blank_rows, total_rows)}`)",
        ]
    )

    report_lines.extend(
        [
            "",
            "## Actionable Review Signals",
            f"- near_miss_should_emit_count: `{near_miss_should_emit}`",
            f"- new_guard_requests: `{len(new_guard_rows)}`",
        ]
    )

    if reject_bucket_counts:
        report_lines.append("- reject_emit_types:")
        for key, count in sort_counter(reject_bucket_counts):
            report_lines.append(f"  - `{key}` = `{count}`")
    else:
        report_lines.append("- reject_emit_types: `none`")

    if should_emit_bucket_counts:
        report_lines.append("- blocked_should_emit_types:")
        for key, count in sort_counter(should_emit_bucket_counts):
            report_lines.append(f"  - `{key}` = `{count}`")
    else:
        report_lines.append("- blocked_should_emit_types: `none`")

    if guard_reason_counts:
        report_lines.append("- new_guard_request_reasons:")
        for key, count in sort_counter(guard_reason_counts):
            report_lines.append(f"  - `{key}` = `{count}`")
    else:
        report_lines.append("- new_guard_request_reasons: `none`")

    if actionable_samples:
        report_lines.append("- top_actionable_samples:")
        for sample_id, count, counter in actionable_samples:
            details = ", ".join(
                f"{decision}={counter.get(decision, 0)}"
                for decision in sorted(ACTIONABLE_DECISIONS)
                if counter.get(decision, 0) > 0
            )
            report_lines.append(f"  - `{sample_id}` = `{count}` ({details})")
    else:
        report_lines.append("- top_actionable_samples: `none`")

    report_lines.extend(
        [
            "",
            "## Workflow Reminder",
            "- keep this package report-only",
            "- do not propose runtime or convert-path changes until manual review is filled",
            "- use reviewer_notes to capture examples that motivate keep/refine/expand decisions",
            "",
        ]
    )

    return summary_rows, "\n".join(report_lines)


def main() -> int:
    args = parse_args()
    review_tsv = Path(args.review_tsv).resolve()
    output_report = Path(args.output_report).resolve()
    output_summary_tsv = Path(args.output_summary_tsv).resolve()

    rows = read_rows(review_tsv)
    for row in rows:
        row["__review_tsv__"] = str(review_tsv)

    summary_rows, report_text = summarize(rows)
    write_tsv(output_summary_tsv, summary_rows)
    write_text(output_report, report_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
