# markitdown-quality-lab

`markitdown-quality-lab` is the external corpus repository for the MoonBit
`markitdown` project. It is not runtime code, not a product deliverable, and
not a required build dependency. The main repository must still build, test,
and run without this repository present.

This repository keeps three repo-local corpus surfaces that should not live
directly in the main repository:

- repo-owned main-process regression fixtures and expected outputs
- external quality-regression corpus material
- external performance-benchmark corpus material

## Layout

```text
markitdown-quality-lab/
  external_main_process/
  external_quality/
  external_bench/
  README.md
  LICENSES.md
```

## Directory roles

### `external_main_process/`

`external_main_process/` is the repo-owned main-process regression tree.

- It keeps project-controlled fixtures, expected outputs, and RAG-oriented
  payloads grouped by format.
- Typical format subtrees contain `markdown/`, `expected/`, `rag/`, and
  optional `assets/` directories.
- It is not a third-party source catalog or a formal external-license surface
  by itself.
- Files from this tree only enter the formal provenance summary when an
  explicit repo-owned source entry in `external_quality/SOURCE_CATALOG.tsv`
  points at them.

### `external_quality/`

`external_quality/` is the formal external quality-regression corpus tree.

- `MANIFEST.tsv` is the formal consumption entrypoint.
- `SOURCE_CATALOG.tsv` is the source and license tracing index.
- Tracked payloads live under `external_quality/<format>/<source>/...`.
- The main repository reads this manifest from `samples/check_quality.sh`.
- Staging, cache, and legacy archive paths are not formal consumption surfaces.

Every formal sample must be referenced by a manifest row. Samples with unclear
origin, license, privacy, or redistribution boundaries must not enter the
formal manifest.

### `external_bench/`

`external_bench/` is the formal external benchmark corpus tree.

- `MANIFEST.tsv` is the benchmark execution entrypoint.
- Tracked payloads live under `external_bench/<format>/<size_class>/...`.
- The main repository `bench v2` flow reads this manifest by default.
- The local audit note lives at `external_bench/_audit/PROVENANCE.md`.

Benchmark results are directional signals for same-machine, same-corpus,
same-parameter comparisons. They are useful for spotting local regressions and
relative trends, not for making general performance claims.

## Expected placement

The recommended layout is:

```text
markitdown/
  markitdown-quality-lab/
```

The main repository quality flow reads:

```text
markitdown-quality-lab/external_quality/MANIFEST.tsv
```

The main repository benchmark flow reads:

```text
markitdown-quality-lab/external_bench/MANIFEST.tsv
```

Repo-owned format fixtures also live under:

```text
markitdown-quality-lab/external_main_process/<format>/
```

If this repository is absent, the main repository runtime, parsers,
converters, and ordinary tests should still work.

## Intake rules

- Every formal sample must have a manifest row.
- Every formal `external_quality/` source must be traceable in
  `external_quality/SOURCE_CATALOG.tsv`.
- Every curated `external_bench/` row must retain `source_ref` and any needed
  provenance context in `MANIFEST.tsv`.
- Every promoted repo-owned file reused from `external_main_process/` must be
  represented by an explicit repo-owned source entry before it enters the
  formal `external_quality/` surface.
- Every source must have an explicit license and source origin.
- `UNKNOWN`, empty license fields, and empty source origins are not allowed in
  the formal catalog.
- `.tmp`, cache, local-only, and staging paths are not allowed in formal
  manifests.
- Samples with unclear license, provenance, privacy, or redistribution
  boundaries must stay out of the formal manifests.
- `external_main_process/` content must remain repo-owned, traceable, and free
  of private, temporary, or unauthorized tracked material.
- Sample licenses describe the samples only and do not change the
  `markitdown` code license.

## Non-goals

- This repository does not promise general benchmark conclusions.
- It does not act as a generic training-data warehouse.
- It does not act as a build dependency for the main repository.
- It does not keep private data, local cache, temporary downloads, or
  unauthorized material as tracked formal assets.
- It does not use legacy staging directories as formal consumption surfaces.

## Maintenance rules

- After changing `MANIFEST.tsv` or `SOURCE_CATALOG.tsv`, rerun the relevant
  path, source, and license checks.
- For large migrations, create a cleanup or migration plan before executing it.
- Keep `external_main_process/` aligned as the repo-owned main-process fixture
  and expected-output surface.
- Keep `external_quality/` aligned around the
  `README + MANIFEST + SOURCE_CATALOG` contract.
- Keep `external_bench/` aligned as a curated benchmark consumption surface.
- Do not write README claims that contradict the machine-readable manifest or
  catalog records.
- Repository documents may summarize policy and status, but they do not replace
  the machine-readable constraints in the manifest and catalog files.
