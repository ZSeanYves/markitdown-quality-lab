# PDF Model Data Policy

This policy applies to both `layout_recovery_model` and
`text_block_classifier`.

## Tracked Metadata

Tracked git content may include:

* dataset registry and audit TSVs
* source catalog rows
* label schema and mapping files
* manifest examples and draft manifests
* adapter specifications
* tiny synthetic fixtures
* hashes and provenance for tiny tracked bytes when they are intentionally kept

Tracked metadata is for schema review and reproducibility. It is not the real
training corpus.

## Local-Only Dataset

Meaningful training data should live under:

```text
pdf_model_training/local_only/datasets/<dataset>/
```

Use local-only storage for:

* larger `DocLayNet` subsets
* local `PubLayNet` weak-label subsets
* local `PubTables-1M` table-specialist subsets
* adapted teacher-training exports
* local split manifests

These bytes must not be committed.

## Tiny Tracked Sanity Subset

Tiny tracked subsets are allowed only for:

* adapter parser sanity
* schema sanity
* synthetic or rights-clear fixture tests
* minimal smoke exports

They do not represent the real training set and should never be described as
the main route.

## Teacher Artifacts

Teacher-side artifacts may be large and slow. Keep them under:

```text
pdf_model_training/local_only/artifacts/
```

Examples:

* checkpoints
* feature matrices
* prediction dumps
* local eval summaries
* pseudo-label pools

Teacher artifacts never go into runtime.

## Distilled Outputs

Only distilled outputs are candidates for future tracked review:

* rule suggestions
* feature-importance notes
* error clusters
* compact decision tables
* lightweight classifier candidates
* confidence-threshold proposals

Even these do not enter runtime automatically.

## Hard Boundaries

* Do not commit full public datasets.
* Do not commit local-only manifests or teacher artifacts.
* Do not use OCR as the main route for this track.
* Do not mix gold and weak sources without keeping source identity explicit.
* Do not wire heavy training artifacts into CLI runtime.
