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

This directory describes the formal benchmark consumption surface. It is not a
complete pool of every raw upstream external source.
