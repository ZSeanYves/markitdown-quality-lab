# External Benchmark Corpus

`external_bench/` is the quality-lab-only corpus for real-world performance
benchmark samples. Its formal top-level layout is intentionally small:

```text
external_bench/
  README.md
  MANIFEST.tsv
  SOURCE_CATALOG.tsv
  <format>/
    <source_group>/
      <size_class>/
        <file>
```

Current format directories include `csv/`, `docx/`, `epub/`, `html/`, `json/`,
`pdf/`, `pptx/`, `tsv/`, `txt/`, `xlsx/`, `xml/`, `yaml/`, and `zip/`.

This tree is not part of the main repository runtime, public regression, or
release readiness default. CI and public-only checks must not run full external
benchmarks by default.

## Metadata Files

`MANIFEST.tsv` is the benchmark execution entrypoint. Every runnable payload
must have a row with byte count, SHA-256, source, license, layer, and tier
metadata. Benchmark runners read payload paths from the `rel_path` field.

`SOURCE_CATALOG.tsv` is the source and license traceability entrypoint. The
current benchmark schema keeps existing runner-facing fields such as
`bench_id`, `source_url`, `license_spdx`, and `target_rel_path`; do not remove
those fields without first updating the benchmark tooling that reads them.

Rows with unclear license, privacy, provenance, or redistribution status must
stay disabled until manually reviewed. Sources with
`redistributable=unknown` or `review_status=pending_review` must not be enabled
for benchmark execution.

## Non-Formal Areas

`_local_cache/`, `_tools/`, `_licenses/`, `_bench_rows_staging/`, and `archive/`
are not formal directories inside `external_bench/`.

Maintenance helpers live under `scripts/bench/`, cache and local fetch metadata
under `.tmp/bench/`, benchmark license notes under `licenses/bench/`, and old
layout files under `archive/external_bench/`.

`MANIFEST.tsv` and `SOURCE_CATALOG.tsv` must not point at `.tmp` paths or
cache-only payloads.

## Size Classes

Size class is based on the input payload size that the benchmark runner reads:

```text
tiny    < 100 KiB
small   100 KiB-1 MiB
medium  1-10 MiB
large   10-100 MiB
xlarge  100-500 MiB
```

`large` and `xlarge` payloads require explicit human confirmation before they
are fetched, enabled, or committed. When approved, verify byte count and SHA-256
and record the review decision with the source metadata.

## Layer Selection

`bench_layers` declares which benchmark execution layers may use a row:

```text
parser;convert;cli;compare
```

Main-repository `samples/bench.sh --layer parser|convert|cli|compare` filters
rows by `bench_layers`, then by `enabled_tier`. Rows with
`enabled_tier=disabled`, `pending_review`, `unknown`, or an empty value must not
be executed.

## Fetch Workflow

Run the fetch helper without flags first to inspect the plan:

```text
bash scripts/bench/tools/fetch_external_bench_samples.sh
```

The helper writes downloads to
`<format>/<source_group>/<size_class>/<file>.partial` and renames them only
after the fetch succeeds. Existing payloads are not overwritten unless
`--replace` is supplied.

Benchmark results from this corpus are same-machine, same-corpus directional
feedback. They are useful for spotting local regressions and relative trends;
they are not general performance guarantees.
