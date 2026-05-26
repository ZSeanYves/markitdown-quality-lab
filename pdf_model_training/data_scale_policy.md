# Data Scale Policy

## Goal

This policy defines how data for the `PDF text-flow assist model` should be
split across tracked metadata, local-only larger datasets, tiny sanity subsets,
teacher artifacts, and distilled outputs.

The guiding principle is:

- training may be heavy and local-only;
- runtime must stay light, optional, and fail closed.

## 1. Tracked Metadata

Tracked metadata is safe to keep in git and should include:

- source catalogs;
- dataset audit tables;
- label mappings;
- manifest drafts;
- adapter specifications;
- SHA256 records for tiny tracked bytes where applicable;
- source URLs and provenance notes.

Tracked metadata is for:

- reproducibility of planning;
- schema review;
- adapter design;
- auditability of source and license boundaries.

Tracked metadata is not the same thing as a sufficient training corpus.

## 2. Local-Only Dataset

Local-only dataset payloads are the intended route for meaningful Task A
teacher training.

Examples:

- hundreds to low-thousands of `DocLayNet` pages;
- optional local-only `PubLayNet` weak-label supplements;
- optional local-only `PubTables-1M` `table_like` specialist subsets.

Local-only datasets:

- must not be committed to git;
- should live under `pdf_model_training/local_only/datasets/<dataset>/`;
- may include manifests, hashes, and adapter outputs managed locally by the
  user;
- may be large, slow, and experiment-oriented.

Use local-only datasets for:

- teacher training;
- teacher evaluation;
- ablations;
- distillation analysis;
- rule extraction experiments.

## 3. Tiny Tracked Sanity Subset

Tiny tracked sanity subsets are allowed only for:

- adapter parser checks;
- schema checks;
- minimal smoke exports;
- fixture-driven tests.

They may include:

- synthetic fixtures;
- tiny rights-clean metadata;
- tiny sample annotation JSONs when license and size are safe.

They do not represent the real training corpus and must not be described as the
main Task A dataset.

## 4. Teacher Artifacts

Teacher-side artifacts may be large and local-only.

Examples:

- local-only checkpoints;
- local-only feature matrices;
- local-only prediction dumps;
- local-only eval summaries;
- local-only pseudo-label outputs.

Teacher artifacts:

- do not go into runtime;
- do not become CLI dependencies;
- should be ignored by git or stored outside tracked repo payloads.

## 5. Distilled Artifacts

Distilled artifacts are the only outputs that may later become candidates for
tracked review and possible runtime consideration.

Examples:

- rule suggestions;
- feature importance summaries;
- error-cluster reports;
- confidence threshold notes;
- small decision tables;
- lightweight classifier candidate specs.

Even distilled artifacts do not automatically enter runtime. They still need:

- task-specific evaluation;
- fail-closed runtime review;
- deterministic rule gating.

## Allowed Scale Tiers

Suggested working tiers:

- tracked sanity: synthetic or tiny metadata only;
- local-only smoke: tens of pages;
- local-only pilot: hundreds to around one thousand pages;
- stronger teacher round: roughly three to five thousand pages.

These are planning tiers, not mandatory thresholds.

## Storage Boundary

Recommended local-only storage root:

```text
pdf_model_training/local_only/datasets/<dataset>/
```

Recommended local-only artifact root:

```text
pdf_model_training/local_only/artifacts/
```

Git should only retain directory guidance such as a tracked `README.md`, not
the actual dataset payloads or teacher artifacts.
