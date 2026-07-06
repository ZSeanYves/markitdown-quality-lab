# markitdown-quality-lab

`markitdown-quality-lab` is the external corpus repository for the MoonBit
`markitdown` project. It is not runtime code, not a product deliverable, and
not a required build dependency. The main repository must still build, test,
and run without this repository present.

This repository keeps three kinds of material that should not live directly in
the main repository:

- external quality-regression corpus material
- external performance-benchmark corpus material
- PDF, layout, and model-training audit or experiment assets

## Layout

```text
markitdown-quality-lab/
  external_quality/
  external_bench/
  pdf_model_training/
  README.md
  LICENSES.md
```

## Directory roles

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

### `pdf_model_training/`

`pdf_model_training/` stores PDF, layout, and model-training assets, together
with related local audit or experiment material.

- It does not represent shipped runtime capability.
- It should not be required by public-only checks in the main repository.
- It is maintained separately from the formal `external_quality/` and
  `external_bench/` cleanup surfaces.
- Local README files, manifests, or reports inside that tree define the exact
  training, evaluation, and local-only boundaries.

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

If this repository is absent, the main repository runtime, parsers,
converters, and ordinary tests should still work.

## Intake rules

- Every formal sample must have a manifest row.
- Every formal `external_quality/` source must be traceable in
  `external_quality/SOURCE_CATALOG.tsv`.
- Every curated `external_bench/` row must retain `source_ref` and any needed
  provenance context in `MANIFEST.tsv`.
- Every source must have an explicit license and source origin.
- `UNKNOWN`, empty license fields, and empty source origins are not allowed in
  the formal catalog.
- `.tmp`, cache, local-only, and staging paths are not allowed in formal
  manifests.
- Samples with unclear license, provenance, privacy, or redistribution
  boundaries must stay out of the formal manifests.
- Sample licenses describe the samples only and do not change the
  `markitdown` code license.

## Non-goals

- This repository does not promise general benchmark conclusions.
- It does not describe OCR, PDF, or model experiment assets as shipped runtime
  capability.
- It does not act as a build dependency for the main repository.
- It does not keep private data, local cache, temporary downloads, or
  unauthorized material as tracked formal assets.
- It does not use legacy staging directories as formal consumption surfaces.

## Maintenance rules

- After changing `MANIFEST.tsv` or `SOURCE_CATALOG.tsv`, rerun the relevant
  path, source, and license checks.
- For large migrations, create a cleanup or migration plan before executing it.
- Keep `external_quality/` aligned around the
  `README + MANIFEST + SOURCE_CATALOG` contract.
- Keep `external_bench/` aligned as a curated benchmark consumption surface.
- Do not write README claims that contradict the machine-readable manifest or
  catalog records.
- Repository documents may summarize policy and status, but they do not replace
  the machine-readable constraints in the manifest and catalog files.
