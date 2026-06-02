# External Benchmark Corpus

`external_bench/` is a quality-lab-only area for real-world performance
benchmark corpus planning and manifests. Its top-level format directories match
the `external_quality/` style, while its metadata remains benchmark-specific.

This tree is not part of the main repository runtime, public regression, or
release readiness default. CI and public-only checks must not run full external
benchmarks by default.

## Layout

Payloads are organized directly under a format directory:

```text
<format>/<source_group>/<size_class>/<file>
```

Examples:

```text
pdf/irs_publications/small/f1040.pdf
json/worldbank_api/large/json_wb_population.json
xlsx/ons/medium/mye24tablesuk.xlsx
```

Payloads are generated or fetched locally from reviewed source rows and are not
tracked in git. `MANIFEST.tsv` stores the runnable payload path in `rel_path`;
benchmark runners use that file as the execution entrypoint.

## Local Directories

* `_local_cache/` stores local fetch metadata and temporary cache files. It is
  not tracked in git.
* `_tools/` stores fetch, build, and validation scripts.
* `_licenses/` stores license and attribution review records.
* `_bench_rows_staging/` stores generated or transitional row files while
  refreshing the corpus.
* `archive/` stores old skeleton examples, historical candidates, and replaced
  plans.

## Metadata Files

* `MANIFEST.tsv` is the benchmark execution entrypoint. Every runnable payload
  must have a row with byte count, SHA-256, source, license, layer, and tier
  metadata.
* `SOURCE_CATALOG.tsv` is the source review entrypoint. It records source URLs,
  landing URLs, licenses, redistributability, review status, and planned target
  paths.
* `FETCH_PLAN.tsv` is the fetch plan entrypoint. Fetch tooling is dry-run by
  default and must not download payloads unless explicitly run with `--apply`.

Rows with unclear license, privacy, provenance, or redistribution status must
stay disabled until manually reviewed. Sources with
`redistributable=unknown` or `review_status=pending_review` must not be enabled
for benchmark execution.

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
bash external_bench/_tools/fetch_external_bench_samples.sh
```

The helper writes downloads to
`<format>/<source_group>/<size_class>/<file>.partial` and renames them only
after the fetch succeeds. Existing payloads are not overwritten unless
`--replace` is supplied.
