#!/usr/bin/env python3
"""Export a local-only visual review pack for footer/header manual review."""

from __future__ import annotations

import argparse
import ast
import csv
import html
import shlex
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import quote

try:
    import fitz  # type: ignore
except Exception:  # pragma: no cover - environment dependent
    fitz = None

try:
    from PIL import Image, ImageDraw  # type: ignore
except Exception:  # pragma: no cover - environment dependent
    Image = None
    ImageDraw = None


REVIEW_REQUIRED_FIELDS = [
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

SUMMARY_REQUIRED_FIELDS = [
    "row_id",
    "input_path",
    "status",
    "reason",
    "report_path",
]

MANIFEST_REQUIRED_FIELDS = [
    "id",
    "path",
    "source_id",
    "local_cache_path",
]

ENRICHED_FIELDS = REVIEW_REQUIRED_FIELDS + [
    "manifest_id",
    "manifest_path",
    "manifest_local_cache_path",
    "manifest_source_id",
    "summary_row_id",
    "summary_status",
    "summary_reason",
    "quality_report_path",
    "input_pdf_path",
    "produced_md_path",
    "metadata_path",
    "review_entry_md_path",
    "page_image_path",
    "bbox_crop_path",
    "open_pdf_hint",
    "open_md_hint",
    "review_context_status",
    "bbox_overlay_status",
    "render_status",
    "render_error",
]


class ReviewVisualPackError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a local-only review visual pack for footer_header_noise "
            "manual-review TSV rows."
        )
    )
    parser.add_argument(
        "--review-tsv",
        required=True,
        help="Path to footer_header_manual_review.tsv.",
    )
    parser.add_argument(
        "--quality-manifest",
        required=True,
        help="Path to external_quality/_quality_rows_staging/manifest.tsv.",
    )
    parser.add_argument(
        "--summary-tsv",
        help="Path to external_quality_hint_summary.tsv.",
    )
    parser.add_argument(
        "--quality-run-dir",
        help="Dry-run output directory that contains rows/<row_id>/ report data.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Local-only output directory for the review visual pack.",
    )
    parser.add_argument(
        "--render-pages",
        action="store_true",
        help="Render page PNGs when a PDF renderer is available.",
    )
    parser.add_argument(
        "--make-crops",
        action="store_true",
        help="Generate bbox crop PNGs when a PDF renderer is available.",
    )
    parser.add_argument(
        "--max-text-chars",
        type=int,
        default=160,
        help="Maximum text preview length used in review index files.",
    )
    return parser.parse_args()


def read_tsv(path: Path, required_fields: list[str]) -> list[dict[str, str]]:
    if not path.is_file():
        raise ReviewVisualPackError(f"missing TSV: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = reader.fieldnames or []
        missing = [field for field in required_fields if field not in fieldnames]
        if missing:
            raise ReviewVisualPackError(
                f"TSV {path} is missing required columns: {', '.join(missing)}"
            )
        return list(reader)


def write_tsv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ENRICHED_FIELDS, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def normalize_path(raw: str) -> str:
    stripped = raw.strip()
    if not stripped:
        return ""
    return str(Path(stripped).resolve())


def truncate_text(text: str, limit: int) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: max(0, limit - 3)] + "..."


def path_to_file_uri(raw: str) -> str:
    if not raw:
        return ""
    return Path(raw).resolve().as_uri()


def open_hint(raw: str) -> str:
    if not raw:
        return ""
    return f"xdg-open {shlex.quote(raw)}"


def parse_bbox(raw: str) -> list[float] | None:
    if not raw.strip():
        return None
    try:
        value = ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        return None
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        return None
    try:
        return [float(item) for item in value]
    except (TypeError, ValueError):
        return None


def manifest_maps(
    rows: list[dict[str, str]],
    repo_root: Path,
) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    by_id: dict[str, dict[str, str]] = {}
    by_abs_path: dict[str, dict[str, str]] = {}
    by_rel_path: dict[str, dict[str, str]] = {}
    for row in rows:
        manifest_id = row.get("id", "").strip()
        if manifest_id:
            by_id[manifest_id] = row
        rel_path = row.get("path", "").strip()
        if rel_path:
            by_rel_path[rel_path] = row
            by_abs_path[str((repo_root / rel_path).resolve())] = row
        cache_path = row.get("local_cache_path", "").strip()
        if cache_path:
            by_rel_path[cache_path] = row
            by_abs_path[str((repo_root / cache_path).resolve())] = row
    return by_id, by_abs_path, by_rel_path


def resolve_manifest_row(
    review_row: dict[str, str],
    summary_row: dict[str, str] | None,
    manifest_by_id: dict[str, dict[str, str]],
    manifest_by_abs_path: dict[str, dict[str, str]],
    manifest_by_rel_path: dict[str, dict[str, str]],
) -> dict[str, str] | None:
    row_id = review_row.get("row_id", "").strip()
    if row_id and row_id in manifest_by_id:
        return manifest_by_id[row_id]
    if summary_row:
        input_path = normalize_path(summary_row.get("input_path", ""))
        if input_path and input_path in manifest_by_abs_path:
            return manifest_by_abs_path[input_path]
    sample_prefix = review_row.get("sample_id", "").split(":p", 1)[0].strip()
    if sample_prefix and sample_prefix in manifest_by_id:
        return manifest_by_id[sample_prefix]
    source_pdf_id = review_row.get("source_pdf_id", "").strip()
    if source_pdf_id and source_pdf_id in manifest_by_id:
        return manifest_by_id[source_pdf_id]
    if source_pdf_id and source_pdf_id in manifest_by_rel_path:
        return manifest_by_rel_path[source_pdf_id]
    return None


def derive_quality_paths(
    review_row: dict[str, str],
    summary_row: dict[str, str] | None,
    quality_run_dir: Path | None,
) -> tuple[str, str, str]:
    row_id = review_row.get("row_id", "").strip()
    report_path = ""
    row_dir: Path | None = None
    if summary_row:
        report_path = normalize_path(summary_row.get("report_path", ""))
        if report_path:
            row_dir = Path(report_path).parent
    if row_dir is None and quality_run_dir is not None:
        row_dir = quality_run_dir / "rows" / row_id
        report_candidate = row_dir / "report.md"
        report_path = str(report_candidate.resolve()) if report_candidate.exists() else ""
    if row_dir is None:
        return report_path, "", ""
    produced_md = row_dir / "quality_run" / "outputs" / row_id / f"{row_id}.md"
    metadata = (
        row_dir
        / "quality_run"
        / "outputs"
        / row_id
        / "metadata"
        / f"{row_id}.metadata.json"
    )
    produced_md_path = str(produced_md.resolve())
    metadata_path = str(metadata.resolve())
    return report_path, produced_md_path, metadata_path


def overlay_rect_pdf_bottom_left(
    bbox: list[float],
    page_width: float,
    page_height: float,
    scale: float,
) -> tuple[tuple[float, float, float, float], str]:
    x0, y0, x1, y1 = bbox
    status = "bbox_overlay_assume_pdf_bottom_left"
    if x1 < x0 or y1 < y0:
        raise ReviewVisualPackError("invalid bbox with negative span")
    if x0 < 0 or y0 < 0 or x1 > page_width or y1 > page_height:
        status = "bbox_overlay_uncertain_out_of_bounds"
    px0 = max(0.0, min(page_width, x0)) * scale
    px1 = max(0.0, min(page_width, x1)) * scale
    py0 = max(0.0, min(page_height, page_height - y1)) * scale
    py1 = max(0.0, min(page_height, page_height - y0)) * scale
    return (px0, py0, px1, py1), status


def render_review_assets(
    *,
    pdf_path: Path,
    page_no: int,
    bbox: list[float] | None,
    page_image_path: Path,
    crop_path: Path | None,
) -> tuple[str, str]:
    if fitz is None or Image is None or ImageDraw is None:
        return "render_skipped_renderer_missing", "renderer_missing:fitz"
    if page_no < 1:
        return "render_skipped_invalid_page_no", "invalid page number"
    doc = fitz.open(pdf_path)
    try:
        if page_no > doc.page_count:
            return "render_skipped_invalid_page_no", "page number exceeds page count"
        page = doc.load_page(page_no - 1)
        scale = 2.0
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        draw = ImageDraw.Draw(image)
        overlay_status = "bbox_overlay_missing"
        if bbox is not None:
            rect, overlay_status = overlay_rect_pdf_bottom_left(
                bbox,
                page.rect.width,
                page.rect.height,
                scale,
            )
            draw.rectangle(rect, outline=(220, 20, 60), width=4)
        page_image_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(page_image_path)
        if crop_path is not None and bbox is not None:
            rect, _ = overlay_rect_pdf_bottom_left(
                bbox,
                page.rect.width,
                page.rect.height,
                scale,
            )
            padding = 32
            crop_box = (
                max(0, int(rect[0]) - padding),
                max(0, int(rect[1]) - padding),
                min(image.width, int(rect[2]) + padding),
                min(image.height, int(rect[3]) + padding),
            )
            if crop_box[2] > crop_box[0] and crop_box[3] > crop_box[1]:
                crop_path.parent.mkdir(parents=True, exist_ok=True)
                image.crop(crop_box).save(crop_path)
        return "rendered_page_and_crop" if crop_path and crop_path.exists() else "rendered_page", overlay_status
    finally:
        doc.close()


def relative_link(from_dir: Path, target: str) -> str:
    if not target:
        return ""
    try:
        return str(Path(target).resolve().relative_to(from_dir.resolve()))
    except ValueError:
        return str(Path(target).resolve())


def build_entry_markdown(
    row: dict[str, str],
    output_dir: Path,
) -> str:
    lines = [
        f"# {row['review_id']}",
        "",
        "## Review Row",
        f"- row_id: `{row['row_id']}`",
        f"- sample_id: `{row['sample_id']}`",
        f"- source_pdf_id: `{row['source_pdf_id']}`",
        f"- page_no: `{row['page_no']}`",
        f"- block_id: `{row['block_id']}`",
        f"- bbox: `{row['bbox']}`",
        f"- text_preview: `{row['text_preview']}`",
        f"- gate_status: `{row['gate_status']}`",
        f"- gate_reason: `{row['gate_reason']}`",
        f"- predicted_label: `{row['predicted_label']}`",
        f"- confidence: `{row['confidence']}`",
        f"- review_bucket: `{row['review_bucket']}`",
        f"- reviewer_decision: `{row['reviewer_decision'] or 'blank'}`",
        f"- reviewer_notes: `{row['reviewer_notes'] or ''}`",
        "",
        "## Source Mapping",
        f"- manifest_id: `{row['manifest_id']}`",
        f"- manifest_source_id: `{row['manifest_source_id']}`",
        f"- manifest_path: `{row['manifest_path']}`",
        f"- manifest_local_cache_path: `{row['manifest_local_cache_path']}`",
        f"- input_pdf_path: `{row['input_pdf_path']}`",
        f"- open_pdf_hint: `{row['open_pdf_hint']}`",
        "",
        "## Quality Outputs",
        f"- summary_status: `{row['summary_status']}`",
        f"- summary_reason: `{row['summary_reason']}`",
        f"- quality_report_path: `{row['quality_report_path']}`",
        f"- produced_md_path: `{row['produced_md_path']}`",
        f"- metadata_path: `{row['metadata_path']}`",
        f"- open_md_hint: `{row['open_md_hint']}`",
        "",
        "## Visual Context",
        f"- review_context_status: `{row['review_context_status']}`",
        f"- render_status: `{row['render_status']}`",
        f"- bbox_overlay_status: `{row['bbox_overlay_status']}`",
        f"- render_error: `{row['render_error']}`",
        f"- page_image_path: `{row['page_image_path']}`",
        f"- bbox_crop_path: `{row['bbox_crop_path']}`",
        "",
    ]
    if row["page_image_path"]:
        page_image_rel = relative_link(output_dir, row["page_image_path"])
        lines.extend(["## Page Image", f"![{row['review_id']} page]({page_image_rel})", ""])
    if row["bbox_crop_path"]:
        crop_rel = relative_link(output_dir, row["bbox_crop_path"])
        lines.extend(["## BBox Crop", f"![{row['review_id']} crop]({crop_rel})", ""])
    return "\n".join(lines)


def build_index_markdown(
    rows: list[dict[str, str]],
    *,
    output_dir: Path,
    enriched_tsv_path: Path,
    review_tsv_path: Path,
    manifest_path: Path,
    summary_path: str,
    renderer_summary: str,
    stats: Counter[str],
) -> str:
    lines = [
        "# Footer Header Manual Review Visual Pack",
        "",
        "## Inputs",
        f"- review_tsv: `{review_tsv_path}`",
        f"- quality_manifest: `{manifest_path}`",
        f"- summary_tsv: `{summary_path}`",
        f"- enriched_tsv: `{enriched_tsv_path}`",
        f"- renderer_mode: `{renderer_summary}`",
        "",
        "## Mapping Note",
        "- use `row_id` as the primary join key into `external_quality_hint_summary.tsv` and manifest `id`",
        "- `sample_id` is the block-level candidate id such as `pdf_booking_layout_markitdown_movie:p1.b157`",
        "- current `source_pdf_id` is only the input PDF stem and is not a stable join key by itself",
        "",
        "## Stats",
        f"- review_rows: `{stats['review_rows']}`",
        f"- resolved_pdf_path_count: `{stats['resolved_pdf_path_count']}`",
        f"- unresolved_pdf_path_count: `{stats['unresolved_pdf_path_count']}`",
        f"- produced_md_found_count: `{stats['produced_md_found_count']}`",
        f"- metadata_found_count: `{stats['metadata_found_count']}`",
        f"- rendered_pages_count: `{stats['rendered_pages_count']}`",
        f"- crop_count: `{stats['crop_count']}`",
        f"- failed_renders_count: `{stats['failed_renders_count']}`",
        "",
        "## Review Rows",
    ]
    for row in rows:
        entry_rel = relative_link(output_dir, row["review_entry_md_path"])
        lines.append(
            f"- `{row['review_id']}` `{row['row_id']}` page=`{row['page_no']}` "
            f"gate=`{row['gate_status']}` bucket=`{row['review_bucket']}` "
            f"context=`{row['review_context_status']}` text=`{truncate_text(row['text_preview'], 80)}` "
            f"entry=`{entry_rel}`"
        )
    lines.append("")
    return "\n".join(lines)


def build_index_html(
    rows: list[dict[str, str]],
    *,
    enriched_tsv_path: Path,
    review_tsv_path: Path,
    manifest_path: Path,
    summary_path: str,
    renderer_summary: str,
    stats: Counter[str],
) -> str:
    cards = []
    for row in rows:
        pdf_link = path_to_file_uri(row["input_pdf_path"])
        md_link = path_to_file_uri(row["produced_md_path"])
        page_img_rel = (
            Path(row["page_image_path"]).resolve().relative_to(enriched_tsv_path.parent.resolve())
            if row["page_image_path"]
            else None
        )
        crop_rel = (
            Path(row["bbox_crop_path"]).resolve().relative_to(enriched_tsv_path.parent.resolve())
            if row["bbox_crop_path"]
            else None
        )
        links = []
        if pdf_link:
            links.append(f'<a href="{html.escape(pdf_link)}">PDF</a>')
        if md_link:
            links.append(f'<a href="{html.escape(md_link)}">Markdown</a>')
        if row["metadata_path"]:
            links.append(
                f'<a href="{html.escape(path_to_file_uri(row["metadata_path"]))}">Metadata</a>'
            )
        if row["review_entry_md_path"]:
            links.append(
                f'<a href="{html.escape(path_to_file_uri(row["review_entry_md_path"]))}">Entry</a>'
            )
        images = []
        if page_img_rel is not None:
            images.append(
                f'<img src="{html.escape(str(page_img_rel))}" alt="{html.escape(row["review_id"])} page">'
            )
        if crop_rel is not None:
            images.append(
                f'<img src="{html.escape(str(crop_rel))}" alt="{html.escape(row["review_id"])} crop">'
            )
        cards.append(
            "\n".join(
                [
                    '<section class="card">',
                    f"<h2>{html.escape(row['review_id'])}</h2>",
                    f"<p><strong>{html.escape(row['row_id'])}</strong> "
                    f"page {html.escape(row['page_no'])} "
                    f"gate={html.escape(row['gate_status'])} "
                    f"bucket={html.escape(row['review_bucket'])}</p>",
                    f"<p>{html.escape(truncate_text(row['text_preview'], 160))}</p>",
                    f"<p>context={html.escape(row['review_context_status'])} "
                    f"overlay={html.escape(row['bbox_overlay_status'])}</p>",
                    f"<p>bbox={html.escape(row['bbox'])}</p>",
                    f"<p>{' | '.join(links) if links else 'no file links resolved'}</p>",
                    '<div class="images">' + "".join(images) + "</div>",
                    "</section>",
                ]
            )
        )
    return "\n".join(
        [
            "<!DOCTYPE html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="utf-8">',
            "<title>Footer Header Manual Review Visual Pack</title>",
            "<style>",
            "body { font-family: sans-serif; margin: 24px; background: #f7f4ec; color: #1f1f1f; }",
            "main { max-width: 1080px; margin: 0 auto; }",
            ".meta, .stats { background: #fff; padding: 16px; border: 1px solid #ddd2bd; margin-bottom: 20px; }",
            ".card { background: #fff; border: 1px solid #ddd2bd; padding: 16px; margin-bottom: 16px; }",
            ".images { display: flex; gap: 12px; flex-wrap: wrap; }",
            ".images img { max-width: 100%; border: 1px solid #c6baa7; }",
            "a { color: #8c2f1b; }",
            "</style>",
            "</head>",
            "<body>",
            "<main>",
            "<h1>Footer Header Manual Review Visual Pack</h1>",
            '<section class="meta">',
            f"<p>review_tsv: {html.escape(str(review_tsv_path))}</p>",
            f"<p>quality_manifest: {html.escape(str(manifest_path))}</p>",
            f"<p>summary_tsv: {html.escape(summary_path)}</p>",
            f"<p>enriched_tsv: {html.escape(str(enriched_tsv_path))}</p>",
            f"<p>renderer_mode: {html.escape(renderer_summary)}</p>",
            "<p>use row_id as the primary join key; sample_id is the block-level candidate id; source_pdf_id is only the PDF stem.</p>",
            "</section>",
            '<section class="stats">',
            f"<p>review_rows={stats['review_rows']}</p>",
            f"<p>resolved_pdf_path_count={stats['resolved_pdf_path_count']}</p>",
            f"<p>unresolved_pdf_path_count={stats['unresolved_pdf_path_count']}</p>",
            f"<p>produced_md_found_count={stats['produced_md_found_count']}</p>",
            f"<p>metadata_found_count={stats['metadata_found_count']}</p>",
            f"<p>rendered_pages_count={stats['rendered_pages_count']}</p>",
            f"<p>crop_count={stats['crop_count']}</p>",
            f"<p>failed_renders_count={stats['failed_renders_count']}</p>",
            "</section>",
            "\n".join(cards),
            "</main>",
            "</body>",
            "</html>",
        ]
    )


def main() -> int:
    args = parse_args()
    repo_root = Path("/home/zseanyves/Moonbit/markitdown").resolve()
    review_tsv_path = Path(args.review_tsv).resolve()
    manifest_path = Path(args.quality_manifest).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not args.summary_tsv and not args.quality_run_dir:
        raise ReviewVisualPackError("provide --summary-tsv or --quality-run-dir")

    summary_tsv_path = Path(args.summary_tsv).resolve() if args.summary_tsv else None
    quality_run_dir = Path(args.quality_run_dir).resolve() if args.quality_run_dir else None
    if quality_run_dir is None and summary_tsv_path is not None:
        quality_run_dir = summary_tsv_path.parent

    review_rows = read_tsv(review_tsv_path, REVIEW_REQUIRED_FIELDS)
    manifest_rows = read_tsv(manifest_path, MANIFEST_REQUIRED_FIELDS)
    summary_rows = read_tsv(summary_tsv_path, SUMMARY_REQUIRED_FIELDS) if summary_tsv_path else []
    summary_by_row_id = {row.get("row_id", "").strip(): row for row in summary_rows}
    manifest_by_id, manifest_by_abs_path, manifest_by_rel_path = manifest_maps(
        manifest_rows,
        repo_root,
    )

    pages_dir = output_dir / "pages"
    crops_dir = output_dir / "crops"
    entries_dir = output_dir / "entries"
    enriched_rows: list[dict[str, str]] = []
    stats: Counter[str] = Counter()
    stats["review_rows"] = len(review_rows)
    render_requested = args.render_pages
    renderer_available = fitz is not None and Image is not None and ImageDraw is not None
    renderer_summary = "render_with_fitz" if renderer_available and render_requested else "path_only_fallback"
    if render_requested and not renderer_available:
        renderer_summary = "path_only_fallback_renderer_missing_fitz"

    for review_row in review_rows:
        stats["review_rows"] += 0
        summary_row = summary_by_row_id.get(review_row.get("row_id", "").strip())
        manifest_row = resolve_manifest_row(
            review_row,
            summary_row,
            manifest_by_id,
            manifest_by_abs_path,
            manifest_by_rel_path,
        )
        report_path, produced_md_path, metadata_path = derive_quality_paths(
            review_row,
            summary_row,
            quality_run_dir,
        )
        input_pdf_path = normalize_path(summary_row.get("input_path", "")) if summary_row else ""
        if not input_pdf_path and manifest_row:
            manifest_rel = manifest_row.get("path", "").strip()
            if manifest_rel:
                input_pdf_path = str((repo_root / manifest_rel).resolve())
        if input_pdf_path and Path(input_pdf_path).is_file():
            stats["resolved_pdf_path_count"] += 1
        else:
            stats["unresolved_pdf_path_count"] += 1
        if produced_md_path and Path(produced_md_path).exists():
            stats["produced_md_found_count"] += 1
        if metadata_path and Path(metadata_path).exists():
            stats["metadata_found_count"] += 1

        bbox = parse_bbox(review_row.get("bbox", ""))
        page_image_path = ""
        bbox_crop_path = ""
        render_status = "not_requested"
        bbox_overlay_status = "not_attempted"
        render_error = ""
        review_context_status = "ready_path_only"

        if args.render_pages:
            if not renderer_available:
                render_status = "render_skipped_renderer_missing"
                render_error = "PyMuPDF/fitz is not available"
                review_context_status = "ready_path_only_renderer_missing"
            elif not input_pdf_path:
                render_status = "render_skipped_missing_pdf_path"
                render_error = "input_pdf_path is empty"
                review_context_status = "missing_input_pdf_path"
            elif not Path(input_pdf_path).is_file():
                render_status = "render_skipped_missing_pdf_file"
                render_error = "input_pdf_path does not exist on disk"
                review_context_status = "input_pdf_missing_on_disk"
            else:
                page_image_candidate = pages_dir / f"{review_row['review_id']}_page.png"
                crop_candidate = (
                    crops_dir / f"{review_row['review_id']}_crop.png" if args.make_crops else None
                )
                try:
                    render_status, bbox_overlay_status = render_review_assets(
                        pdf_path=Path(input_pdf_path),
                        page_no=int(review_row.get("page_no", "0") or "0"),
                        bbox=bbox,
                        page_image_path=page_image_candidate,
                        crop_path=crop_candidate,
                    )
                except Exception as exc:  # pragma: no cover - defensive
                    render_status = "render_failed"
                    bbox_overlay_status = "not_attempted"
                    render_error = str(exc)
                    review_context_status = "ready_path_only_render_failed"
                    stats["failed_renders_count"] += 1
                else:
                    page_image_path = str(page_image_candidate.resolve()) if page_image_candidate.exists() else ""
                    if crop_candidate and crop_candidate.exists():
                        bbox_crop_path = str(crop_candidate.resolve())
                    if page_image_path:
                        stats["rendered_pages_count"] += 1
                    if bbox_crop_path:
                        stats["crop_count"] += 1
                    if render_status.startswith("rendered"):
                        review_context_status = (
                            "ready_with_page_and_crop"
                            if bbox_crop_path
                            else "ready_with_page_only"
                        )
                    elif render_status.startswith("render_skipped"):
                        review_context_status = "ready_path_only_render_skipped"
                    if render_status.startswith("render_skipped") and not render_error:
                        render_error = render_status

        if summary_row is None:
            review_context_status = "missing_summary_row"
        elif not input_pdf_path:
            review_context_status = "missing_input_pdf_path"

        entry_path = entries_dir / f"{review_row['review_id']}.md"
        enriched_row = {
            **{field: review_row.get(field, "") for field in REVIEW_REQUIRED_FIELDS},
            "manifest_id": manifest_row.get("id", "").strip() if manifest_row else "",
            "manifest_path": manifest_row.get("path", "").strip() if manifest_row else "",
            "manifest_local_cache_path": (
                manifest_row.get("local_cache_path", "").strip() if manifest_row else ""
            ),
            "manifest_source_id": manifest_row.get("source_id", "").strip() if manifest_row else "",
            "summary_row_id": summary_row.get("row_id", "").strip() if summary_row else "",
            "summary_status": summary_row.get("status", "").strip() if summary_row else "",
            "summary_reason": summary_row.get("reason", "").strip() if summary_row else "",
            "quality_report_path": report_path,
            "input_pdf_path": input_pdf_path,
            "produced_md_path": produced_md_path,
            "metadata_path": metadata_path,
            "review_entry_md_path": str(entry_path.resolve()),
            "page_image_path": page_image_path,
            "bbox_crop_path": bbox_crop_path,
            "open_pdf_hint": open_hint(input_pdf_path) if input_pdf_path else "",
            "open_md_hint": open_hint(produced_md_path) if produced_md_path else "",
            "review_context_status": review_context_status,
            "bbox_overlay_status": bbox_overlay_status,
            "render_status": render_status,
            "render_error": render_error,
        }
        write_text(entry_path, build_entry_markdown(enriched_row, output_dir))
        enriched_rows.append(enriched_row)

    enriched_tsv_path = output_dir / "footer_header_manual_review.enriched.tsv"
    review_index_md_path = output_dir / "review_index.md"
    review_index_html_path = output_dir / "review_index.html"
    write_tsv(enriched_tsv_path, enriched_rows)
    write_text(
        review_index_md_path,
        build_index_markdown(
            enriched_rows,
            output_dir=output_dir,
            enriched_tsv_path=enriched_tsv_path,
            review_tsv_path=review_tsv_path,
            manifest_path=manifest_path,
            summary_path=str(summary_tsv_path) if summary_tsv_path else "",
            renderer_summary=renderer_summary,
            stats=stats,
        ),
    )
    write_text(
        review_index_html_path,
        build_index_html(
            enriched_rows,
            enriched_tsv_path=enriched_tsv_path,
            review_tsv_path=review_tsv_path,
            manifest_path=manifest_path,
            summary_path=str(summary_tsv_path) if summary_tsv_path else "",
            renderer_summary=renderer_summary,
            stats=stats,
        ),
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
