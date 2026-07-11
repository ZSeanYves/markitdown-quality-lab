# Curated External Bench Corpus

`external_bench/` is the formal benchmark corpus surface currently consumed by
the main repository `bench v2` flow.

This directory keeps only the curated payloads consumed directly by the runner:

```text
external_bench/
  README.md
  MANIFEST.tsv
  FORMAT_MATRIX.md
  <format>/
    <size_class>/
      <file>
```

Key rules:

- The main repository reads `external_bench/MANIFEST.tsv` by default.
- `rel_path` points directly to curated payloads inside this directory.
- `source_ref` keeps the provenance anchor for each row, and
  `MANIFEST.tsv` remains the canonical row-level source note.
- Local provenance and redistribution review notes live in
  `external_bench/_audit/PROVENANCE.md`.
- The main repository must still complete build, unit test, and repo-local
  regression runs without this directory present.

## Comparison classes

`external_compare` is limited to cases where the locked Microsoft MarkItDown
environment selects a format-aware converter and both outputs satisfy the
declared semantic signals. A file merely accepted by `PlainTextConverter` is
not evidence that MarkItDown implements that format's structure.

The converter registry was re-audited for the release split on 2026-07-12.
CSV, EPUB, PDF, IPYNB, PPTX, XLS/XLSX, DOCX, HTML, and ZIP have dedicated
converters relevant to this corpus. TSV, JSON, YAML, XML, subtitle formats,
JSONL/NDJSON, TOML, EML, TeX, RST, and AsciiDoc fall through to plain-text
conversion and therefore use `self_baseline`. Markdown and TXT remain
externally comparable because their source text is already the target content
semantics.

IPYNB cases containing attachment payloads use `self_baseline`: the locked
MarkItDown output leaves `attachment:` references without persisted files,
whereas the product contract requires safe asset materialization. This avoids
comparing a real asset-writing CLI path with a broken-reference output path.

These classifications are version-specific evidence. A MarkItDown dependency
update must re-run converter selection and semantic-signal checks before an
existing class is retained.

This directory describes the formal benchmark consumption surface. It is not a
complete pool of every raw upstream external source.
