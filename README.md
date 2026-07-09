# markitdown-quality-lab

`markitdown-quality-lab` is the repo-local corpus and validation lab for the
MoonBit `markitdown` project.

It is:

- the checked-out home for formal external regression corpora
- the checked-out home for curated benchmark payloads and manifests
- the checked-out home for repo-owned main-process regression fixtures that do
  not belong in the main runtime repository

It is not:

- runtime code
- a shipped product artifact
- a required build dependency for the main repository

The main `markitdown` repository must still build, run, and pass ordinary
`moon test` without this repository present.

## Root Layout

```text
markitdown-quality-lab/
  README.md
  LICENSE
  LICENSES.md
  external_main_process/
    README.md
    MANIFEST.tsv
    <format>/
      <lane>/
      expected/<lane>/
      assets/                # optional
  external_quality/
    README.md
    MANIFEST.tsv
    SOURCE_CATALOG.tsv
    <format>/<source>/...
  external_accurate/
    README.md
    MANIFEST.tsv
    SOURCE_CATALOG.tsv
    <format>/<source>/...
  external_bench/
    README.md
    MANIFEST.tsv
    FORMAT_MATRIX.md
    <format>/<size_class>/<file>
```

## Directory Roles

### `external_main_process/`

`external_main_process/` is the repo-owned main-regression corpus.

- It feeds `samples/check_balance.sh` in the main repository.
- Its machine-readable entrypoint is `external_main_process/MANIFEST.tsv`.
- It is project-controlled fixture material, not a third-party source pool.
- Format roots typically use lane-shaped inputs and outputs such as:
  `markdown/`, `rag/`, `ocr/`, and `expected/<lane>/`.
- Optional `assets/` directories keep tracked sidecar material for formats
  like `docx`, `epub`, `html`, `ipynb`, `odt`, `odp`, `pptx`, and `zip`.

Typical shape:

```text
external_main_process/<format>/
  markdown/                 # or another input lane
  rag/                      # optional
  ocr/                      # optional
  expected/
    markdown/
    rag/
    ocr/
    assets/                 # optional
  assets/                   # optional
```

This tree is repo-owned and should remain free of unclear third-party
redistribution material. Promotion from this tree into a formal external
surface must stay explicitly traceable.

### `external_quality/`

`external_quality/` is the formal external balance/default quality-regression
surface.

- It feeds `samples/check_balance_quality.sh` in the main repository.
- `MANIFEST.tsv` is the row-level consumption contract.
- `SOURCE_CATALOG.tsv` is the source, license, and provenance index.
- Tracked payloads live under `external_quality/<format>/<source>/...`.
- This tree is for broader quality signals on the normal product surface, not
  for accurate-only behavior.

Use this tree for real-world or audited external samples that should influence
the default quality signal for supported formats.

### `external_accurate/`

`external_accurate/` is the formal accurate-only regression surface.

- It feeds `samples/check_accurate.sh` in the main repository.
- `MANIFEST.tsv` is the row-level contract.
- `SOURCE_CATALOG.tsv` is the source, license, and provenance index.
- Tracked payloads live under `external_accurate/<format>/<source>/...`.
- This tree is intentionally separate from `external_quality/`.

It exists for:

- accurate-mode output differences
- route-upgrade evidence
- provider-truth checks for OCR and PDF OCR
- feature-specific diagnostics that belong in `markdown`, `debug`, or
  `provenance` validation views

Current enrolled formats include `docx`, `xlsx`, `pptx`, `odt`, `ods`, `odp`,
`ocr`, and `pdf`.

### `external_bench/`

`external_bench/` is the curated benchmark corpus surface.

- It feeds the main repository `bench v2` flow.
- `MANIFEST.tsv` is the benchmark execution entrypoint.
- `FORMAT_MATRIX.md` summarizes size-class coverage per format.
- Tracked payloads live under `external_bench/<format>/<size_class>/...`.

Benchmark results from this tree are for same-machine, same-corpus,
same-parameter comparison. They are useful for spotting local regressions and
relative trends, not for making general performance claims.

## Expected Placement

The official checked-out location is:

```text
markitdown/
  markitdown-quality-lab/
```

From the main repository root, the default consumers are:

- `samples/check_balance.sh`
  reads `./markitdown-quality-lab/external_main_process/`
- `samples/check_balance_quality.sh`
  reads `./markitdown-quality-lab/external_quality/MANIFEST.tsv`
- `samples/check_accurate.sh`
  reads `./markitdown-quality-lab/external_accurate/MANIFEST.tsv`
- `bench` / `bench v2`
  reads `./markitdown-quality-lab/external_bench/MANIFEST.tsv`

If this repository is absent, the main repository runtime, parsers,
converters, and ordinary tests should still work.

## Intake Rules

- Every formal row must be represented in the relevant `MANIFEST.tsv`.
- Every formal external source in `external_quality/` and
  `external_accurate/` must be represented in the corresponding
  `SOURCE_CATALOG.tsv`.
- Repo-owned files reused from `external_main_process/` must stay explicitly
  traceable when promoted into a formal external surface.
- Every source must have explicit origin, license, and redistribution clarity.
- `UNKNOWN`, empty license metadata, empty source origin, private data, cache
  artifacts, and temporary downloads do not belong in formal surfaces.
- Samples with unclear license, privacy, provenance, or redistribution
  boundaries must stay out of the formal manifests.
- README summaries must not contradict the machine-readable manifest or source
  catalog files.

## Non-goals

- This repository is not a generic training-data warehouse.
- It is not a runtime dependency for the main repository.
- It does not justify public benchmark claims beyond local comparative runs.
- It should not be used as a staging area for `.tmp`, cache, or local-only
  artifacts.

## Maintenance Notes

- After changing `MANIFEST.tsv` or `SOURCE_CATALOG.tsv`, rerun the relevant
  validation flow in the main repository.
- Keep subtree README files aligned with the machine-readable contracts.
- Prefer the subtree-specific README when you need format-level or
  surface-specific conventions:
  `external_main_process/README.md`,
  `external_quality/README.md`,
  `external_accurate/README.md`,
  `external_bench/README.md`.
