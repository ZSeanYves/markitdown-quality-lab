# Repo-owned Main-Process Corpus

`external_main_process/` contains repo-owned main-process regression material
for `markitdown`.

This tree is the project-controlled fixture surface used for format-by-format
conversion checks, expected-output comparisons, and repo-owned corpus coverage.
It is not a third-party source pool.

## Layout

Most format roots follow this structure:

```text
external_main_process/<format>/
  markdown/
  expected/
  rag/
  assets/      # optional
```

Not every format uses every subdirectory, but the intent is consistent:

- `markdown/` stores input-side or lowered Markdown-facing fixtures.
- `expected/` stores expected-output snapshots used by repo-owned regression
  checks.
- `rag/` stores repo-owned retrieval-oriented or metadata-style payloads where
  applicable.
- `assets/` stores tracked sidecar material when a format needs local assets.

## Boundaries

- This tree is repo-owned and should remain free of third-party material whose
  redistribution status is unclear.
- It is separate from `external_quality/` and `external_bench/`, which are the
  formal external corpus surfaces.
- A file from this tree only enters the formal external provenance summary when
  an explicit repo-owned source entry in
  `external_quality/SOURCE_CATALOG.tsv` points at it.
- This tree does not define shipped runtime capability by itself; it is a
  regression and fixture surface.

## Maintenance rules

- Keep paths stable enough for repo-owned regression consumers.
- Prefer repo-owned or clearly authorized material only.
- Do not treat this tree as a cache, staging area, or temporary download
  location.
- When a file from this tree is promoted into `external_quality/`, update the
  corresponding repo-owned source entry and manifest rows together.
