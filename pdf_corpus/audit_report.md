# PDF Real-World Audit Report

## Current Scope

* scaffold for PDF real-world corpus audit in `markitdown-quality-lab`
* focus on source policy, manifest discipline, labeling vocabulary, and future
  layout-model research targets
* no runtime or converter changes
* no assertion changes
* no runtime model integration in this round
* no PDF OCR work in this round
* no packaging or announcement-oriented work in this directory

## Accepted Source Classes

* public-domain or clearly permissive born-digital PDFs
* government or standards PDFs with clear redistribution terms
* permissive academic or technical PDFs whose layout structure matters more than
  semantic content
* scanned archives recorded as metadata when they are useful for future OCR or
  low-signal research but not safe for tracked default-path samples
* project-owned synthetic PDFs when we need controlled layout stress cases

## Rejected Source Classes

* large dataset mirrors without immediate row-level need
* unclear-license PDFs and mixed-provenance mirrors
* PDFs with obvious `pii_risk`, personal forms, financial details, or private
  records
* anything that would turn this corpus into a public-only gate
* scanned PDF payloads pushed into the tracked default path before a separate
  OCR or provider decision exists

## P0 Source Targets

* born-digital multi-column articles with stable reading order
* manuals or specifications with heading hierarchy and numbered sections
* PDFs with figures plus captions on the same or adjacent pages
* table-heavy reports or appendices
* pages with noisy headers, footers, and page numbers

## P1 Source Targets

* multi-page documents requiring cross-page paragraph merge
* list-heavy manuals where ordered and unordered continuity matters
* forms and blank applications with key-value regions
* low-signal or mixed-text-image PDFs that are still useful for future triage

## Initial Source Search Plan

1. Start with item-level or official-source PDFs whose terms are easy to audit.
2. Prefer born-digital technical documents, manuals, reports, and public forms
   before harder scanned or mixed-signal PDFs.
3. Record large or ambiguous sources in `source_catalog.tsv` first as
   `metadata_only` or `unknown`.
4. Only add tracked payload bytes when the file is small, the license is clear,
   and the sample contributes a distinct layout or labeling target.
5. Treat scanned or image-only PDFs as future-research metadata unless a
   separate OCR or provider plan is approved later.

## Open Questions

* whether `manifest.tsv` should stay strictly for real tracked rows, with
  metadata-only planning kept mostly in `audit_report.md`
* whether later label reviews need a dedicated reviewer or confidence column in
  TSV form
* how much of `ocr_layer` and `mixed_text_image` coverage should be pursued
  before any model work exists
* whether a future local helper should validate `model_targets` and label-schema
  conformance without touching runtime code

## Next Action Checklist

* identify 5 to 10 candidate sources for born-digital manuals, reports,
  multi-column papers, and table-heavy PDFs
* verify item-level or source-level license evidence before downloading any
  bytes
* keep scanned or image-only PDFs in metadata-only buckets unless a later plan
  explicitly broadens the boundary
* draft a first tiny tracked sample set only after source and privacy review are
  both stable
* keep PDF corpus language independent from OCR image-corpus semantics
