#!/usr/bin/env python3

"""Tiny contract tests for the shared PDF v2 EvidenceRow adapter."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("pdf_v2_evidence_row_adapter.py")
TESTDATA = Path(__file__).with_name("testdata")
TSV_FIXTURE = TESTDATA / "pdf_v2_evidence_row_fixture.tsv"
JSONL_FIXTURE = TESTDATA / "pdf_v2_evidence_row_fixture.jsonl"


class PdfV2EvidenceRowAdapterTest(unittest.TestCase):
    def run_adapter(self, fixture: Path) -> tuple[list[dict[str, str]], dict[str, object]]:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            output_path = tmp_path / "adapter.tsv"
            summary_path = tmp_path / "summary.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(fixture),
                    "--output",
                    str(output_path),
                    "--summary-output",
                    str(summary_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                proc.returncode,
                0,
                msg=f"adapter failed for {fixture}:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}",
            )
            with output_path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle, delimiter="\t"))
            with summary_path.open("r", encoding="utf-8") as handle:
                summary = json.load(handle)
        return rows, summary

    def test_tsv_fixture_routes_rows_and_preserves_labels(self) -> None:
        rows, summary = self.run_adapter(TSV_FIXTURE)

        self.assertEqual(summary["input_format"], "tsv")
        self.assertEqual(summary["input_row_count"], 6)
        self.assertEqual(summary["evidence_row_count"], 5)
        self.assertEqual(summary["ignored_non_evidence_row_count"], 1)
        self.assertEqual(summary["layout_recovery_row_count"], 2)
        self.assertEqual(summary["semantic_arbitration_row_count"], 3)
        self.assertEqual(summary["doc_groups"], ["synthetic_doc_alpha"])
        self.assertEqual(summary["split_values"], ["heldout"])

        self.assertEqual(len(rows), 5)
        self.assertEqual({row["split"] for row in rows}, {"heldout"})
        self.assertEqual({row["group_id"] for row in rows}, {"synthetic_doc_alpha"})

        by_kind = {row["evidence_kind"]: row for row in rows}
        self.assertEqual(by_kind["cross_page_boundary"]["target_model"], "semantic_arbitration")
        self.assertEqual(by_kind["cross_page_boundary"]["target_kind"], "merge_split_hint")
        self.assertEqual(by_kind["image_text_boundary"]["label_status"], "weak")
        self.assertEqual(
            by_kind["image_text_boundary"]["weak_label"],
            "caption_association_candidate",
        )
        self.assertEqual(by_kind["image_text_boundary"]["related_id"], "xobj-image-8")
        self.assertEqual(by_kind["header_footer_variant"]["target_model"], "layout_recovery")
        self.assertEqual(by_kind["header_footer_variant"]["label_status"], "gold")
        self.assertEqual(
            by_kind["header_footer_variant"]["gold_label"],
            "header_footer_region",
        )
        self.assertEqual(
            by_kind["header_footer_variant"]["blockers"],
            "needs_repeat_review|page_number_overlap",
        )
        self.assertEqual(by_kind["column_layout"]["lane_status"], "existing_tree")
        self.assertEqual(by_kind["heading_boundary"]["subject_id"], "p0:b0")

    def test_jsonl_fixture_matches_tsv_routing(self) -> None:
        rows, summary = self.run_adapter(JSONL_FIXTURE)

        self.assertEqual(summary["input_format"], "jsonl")
        self.assertEqual(summary["evidence_row_count"], 5)
        self.assertEqual(
            summary["counts_by_evidence_kind"],
            {
                "column_layout": 1,
                "cross_page_boundary": 1,
                "header_footer_variant": 1,
                "heading_boundary": 1,
                "image_text_boundary": 1,
            },
        )
        self.assertEqual(
            summary["counts_by_label_status"],
            {"gold": 1, "unlabeled": 3, "weak": 1},
        )
        self.assertEqual({row["source_format"] for row in rows}, {"jsonl"})

    def test_rejects_doc_group_split_leakage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bad_fixture = tmp_path / "bad_fixture.tsv"
            with TSV_FIXTURE.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle, delimiter="\t"))
            rows[2]["split"] = "train"
            with bad_fixture.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=rows[0].keys(),
                    delimiter="\t",
                )
                writer.writeheader()
                writer.writerows(rows)

            output_path = tmp_path / "adapter.tsv"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(bad_fixture),
                    "--output",
                    str(output_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("document-group split leakage detected", proc.stderr)


if __name__ == "__main__":
    unittest.main()
