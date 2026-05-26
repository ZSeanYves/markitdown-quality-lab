# Tiny Subset Policy

## Scope

This policy covers public dataset intake for the `PDF text-flow assist model`
Task A (`convert_block_classification`) only.

Important scope update:

- tiny tracked subsets are adapter/schema sanity inputs only;
- larger local-only dataset subsets are the intended route for teacher training;
- tiny tracked subsets are not the main Task A training corpus.

## Hard Rules

- Do not download or commit complete public layout datasets into the repo.
- Do not add any dataset directly to `manifest.tsv` or `manifest.v2.tsv` active rows
  before label mapping and adapter review are complete.
- Do not track bytes for datasets with unclear redistribution terms, registration
  gates, or meaningful PII risk.
- Do not treat `task_a_seed/` PDFs or historical hand labels as the main training
  route for Task A.

## Tracked Tiny Subset Conditions

Tracked tiny subset bytes are allowed only when all of the following are true:

- license is clearly compatible with redistribution in-repo;
- source URL and item-level provenance are recorded;
- byte size is small enough to remain an audit aid rather than a corpus mirror;
- no meaningful PII risk is present;
- expected Task A label mapping is documented;
- file hashes can be recorded and re-verified.

Typical tracked subset forms:

- a tiny metadata file;
- a tiny sample annotation JSON;
- a tiny loader or dataset card mirror that is already publicly distributed;
- a tiny non-PII example page when license is explicit.

Tracked tiny subsets should answer questions such as:

- does the adapter parse the schema correctly?
- are field names and label names stable?
- does a local smoke export still produce the expected columns?

They should not be used to justify claims that the training set is large enough.

## `local_only` Larger Training Subsets

For Task A teacher training, the intended route is to use larger local-only
subsets, often in the hundreds to low-thousands of pages.

Examples:

- `DocLayNet` smoke: tens of pages;
- `DocLayNet` pilot: hundreds to around one thousand pages;
- stronger teacher rounds: a few thousand pages;
- optional local-only weak supplements from `PubLayNet`;
- optional local-only `table_like` specialist support from `PubTables-1M`.

These larger subsets:

- must not be committed to git;
- should live under `pdf_model_training/local_only/datasets/...`;
- may be used for teacher training, ablation, and distillation analysis;
- must remain clearly separated from tracked metadata and tiny sanity fixtures.

## `metadata_only`

Use `metadata_only` when a dataset is valuable for planning or adapter design but
project policy should not track the dataset bytes.

Examples:

- official README or loader metadata already present locally;
- a first-rows preview file;
- a tiny category schema sample;
- a dataset discovery index such as LayoutParser dataset zoo.

## `local_only`

Use `local_only` when a dataset may still be useful for private adapter work, but
the repo should not track bytes.

Common reasons:

- redistribution is restricted or unclear;
- README says research-only or do-not-redistribute;
- source is huge enough that tiny tracked bytes would be misleading;
- source contains receipts, forms, or other documents with elevated PII risk.

## `forbidden`

Use `forbidden` when the repo should not ingest bytes at all under current policy.

Common reasons:

- license is unclear and access is registration-gated;
- redistribution is not clearly allowed;
- privacy risk is high and not worth the Task A benefit.

## Current P0/P1 Implications

- `DocLayNet` is the strongest current public gold-layout candidate for Task A.
- `PubLayNet` is useful as weak-layout supervision, but should not be treated as
  gold human annotation.
- `PubTables-1M` is valuable as a `table_like` specialist source, not a full
  Task A corpus.
- `DocBank` and `TableBank` are adapter research inputs only until their data
  redistribution constraints are resolved.
- `FUNSD`, `CORD`, and `SROIE` are form/receipt-shaped and should stay out of the
  main tracked Task A corpus because of license and/or PII concerns.

Updated interpretation:

- tracked tiny subsets remain useful, but only for schema sanity;
- local-only larger subsets are the intended teacher-training route;
- teacher artifacts remain local-only unless explicitly distilled into small,
  reviewable outputs.

## `fetch_tiny_subsets.py` Boundary

The current `scripts/fetch_tiny_subsets.py` script only supports:

- `DocLayNet` metadata (`README.md`, `DocLayNet.py`);
- `PubLayNet` tiny sample metadata (`samples.json` and a few images);
- `PubTables-1M` first-row metadata preview.

Known limitations:

- it is not a license validator;
- it does not prove a dataset is approved for tracked training bytes;
- it still writes a local manifest format that reflects older path history;
- it is suitable for metadata refresh, not for larger local-only acquisition;
- it is not a teacher-training downloader;
- it is not a "training ready" declaration tool.

## Teacher Artifact Policy

Teacher-side artifacts such as:

- large local-only feature dumps;
- local-only checkpoints;
- ablation workspaces;
- teacher eval outputs;
- local-only pseudo-label pools

should remain outside git and should not be treated as runtime dependencies.

What may become tracked later are distilled outputs such as:

- rule suggestions;
- feature importance summaries;
- confidence threshold notes;
- compact decision tables;
- small runtime-candidate evaluation reports.

## Gate Before Active Training Intake

Before any public dataset enters an active Task A training manifest, all of the
following must exist:

- dataset audit row;
- label mapping row(s);
- adapter plan;
- tiny subset policy approval for the intended byte form;
- a split strategy that does not mix weak labels and gold labels blindly.
