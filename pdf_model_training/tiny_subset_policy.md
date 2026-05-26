# Tiny Subset Policy

## Scope

This policy covers public dataset intake for the `PDF text-flow assist model`
Task A (`convert_block_classification`) only.

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

## `fetch_tiny_subsets.py` Boundary

The current `scripts/fetch_tiny_subsets.py` script only supports:

- `DocLayNet` metadata (`README.md`, `DocLayNet.py`);
- `PubLayNet` tiny sample metadata (`samples.json` and a few images);
- `PubTables-1M` first-row metadata preview.

Known limitations:

- it is not a license validator;
- it does not prove a dataset is approved for tracked training bytes;
- it still writes a local manifest format that reflects older path history;
- it is suitable for metadata refresh, not for declaring a dataset "training ready".

## Gate Before Active Training Intake

Before any public dataset enters an active Task A training manifest, all of the
following must exist:

- dataset audit row;
- label mapping row(s);
- adapter plan;
- tiny subset policy approval for the intended byte form;
- a split strategy that does not mix weak labels and gold labels blindly.
