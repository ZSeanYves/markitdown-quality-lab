#!/usr/bin/env python3
import argparse
import csv
import os
import subprocess
import sys

from path_roots import (
    REPO_ROOT,
    default_feature_dir,
    discover_corpus_root,
    discover_layout_lab_root,
    resolve_existing_path,
    resolve_pdf_source_path,
)


DEFAULT_TOOL = "_build/native/debug/build/doc_parse/pdf/layout_model_tool/layout_model_tool.exe"
DEFAULT_OUTPUT_DIR = None


def read_tsv(path):
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def ensure_columns(rows, path):
    required = {"sample_id", "pdf_path", "record_kind", "split"}
    keys = set(rows[0].keys()) if rows else set()
    missing = sorted(required - keys)
    if missing:
        raise SystemExit(f"{path} missing required columns: {', '.join(missing)}")


def run_export(tool_path, sample_id, pdf_path, record_kind, output_path, root):
    cmd = [
        tool_path,
        "export",
        "--sample-id",
        sample_id,
        "--input",
        pdf_path,
        "--record-kind",
        record_kind,
        "--output",
        output_path,
    ]
    subprocess.run(cmd, cwd=root, check=True)


def default_tool_path(repo_root):
    candidates = [
        repo_root / "_build/native/debug/build/doc_parse/pdf/layout_model_tool/layout_model_tool.exe",
        repo_root / DEFAULT_TOOL,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def main():
    parser = argparse.ArgumentParser(
        description="Export PDF layout feature TSVs for every sample in one or more manifests.",
    )
    parser.add_argument(
        "--manifest",
        action="append",
        required=True,
        help="TSV manifest path. Can be provided multiple times.",
    )
    parser.add_argument(
        "--lab-root",
        help="PDF model-training root. Defaults to MARKITDOWN_LAYOUT_LAB or repo-local markitdown-quality-lab/pdf_model_training.",
    )
    parser.add_argument(
        "--corpus-root",
        help="External quality root. Defaults to MARKITDOWN_QUALITY_CORPUS or repo-local markitdown-quality-lab/external_quality.",
    )
    parser.add_argument(
        "--tool",
        default=DEFAULT_TOOL,
        help=f"Native export tool path. Defaults to {DEFAULT_TOOL}",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory for *.features.tsv. Defaults to {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--split",
        action="append",
        help="Optional split filter. Can be provided multiple times.",
    )
    parser.add_argument(
        "--sample-id",
        action="append",
        help="Optional sample_id filter. Can be provided multiple times.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip files that already exist.",
    )
    args = parser.parse_args()

    root = str(REPO_ROOT)
    repo_root = REPO_ROOT
    layout_lab_root = discover_layout_lab_root(repo_root, args.lab_root)
    corpus_root = discover_corpus_root(repo_root, args.corpus_root)
    tool_path = resolve_existing_path(args.tool, repo_root=repo_root)
    if tool_path is None:
        if args.tool == DEFAULT_TOOL:
            tool_path = default_tool_path(repo_root)
        else:
            tool_path = repo_root / args.tool
    output_dir = resolve_existing_path(
        args.output_dir,
        repo_root=repo_root,
        extra_roots=[layout_lab_root],
    ) if args.output_dir else None
    if output_dir is None:
        output_dir = default_feature_dir(layout_lab_root, repo_root)
    split_filter = set(args.split or [])
    sample_filter = set(args.sample_id or [])

    if not os.path.exists(tool_path):
        raise SystemExit(
            "native PDF layout model tool not found: "
            f"{tool_path}\nrun: moon build doc_parse/pdf/layout_model_tool --target native"
        )

    os.makedirs(output_dir, exist_ok=True)
    exported = 0
    skipped = 0

    for manifest_path in args.manifest:
        abs_manifest = resolve_existing_path(
            manifest_path,
            repo_root=repo_root,
            extra_roots=[layout_lab_root],
        )
        if abs_manifest is None:
            raise SystemExit(
                f"manifest not found: {manifest_path}\n"
                "hint: pass --lab-root or set MARKITDOWN_LAYOUT_LAB / MARKITDOWN_QUALITY_LAB"
            )
        rows = read_tsv(str(abs_manifest))
        ensure_columns(rows, manifest_path)
        manifest_dir = abs_manifest.parent
        for row in rows:
            sample_id = row["sample_id"].strip()
            if not sample_id:
                continue
            if split_filter and row["split"] not in split_filter:
                continue
            if sample_filter and sample_id not in sample_filter:
                continue
            pdf_path = row["pdf_path"].strip()
            resolved_pdf_path = resolve_pdf_source_path(
                pdf_path,
                repo_root=repo_root,
                manifest_dir=manifest_dir,
                corpus_root=corpus_root,
                layout_lab_root=layout_lab_root,
            )
            if resolved_pdf_path is None:
                raise SystemExit(
                    f"pdf input not found for sample {sample_id}: {pdf_path}\n"
                    "hint: pass --corpus-root or set MARKITDOWN_QUALITY_CORPUS / MARKITDOWN_QUALITY_LAB"
                )
            record_kind = (row.get("record_kind") or "block").strip() or "block"
            output_path = os.path.join(output_dir, f"{sample_id}.features.tsv")
            if args.skip_existing and os.path.exists(output_path):
                skipped += 1
                continue
            run_export(str(tool_path), sample_id, str(resolved_pdf_path), record_kind, output_path, root)
            exported += 1
            print(f"exported {sample_id} -> {os.path.relpath(output_path, root)}")

    print(
        f"feature export complete: exported={exported} skipped={skipped} "
        f"output_dir={os.path.relpath(output_dir, root)}"
    )


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)
