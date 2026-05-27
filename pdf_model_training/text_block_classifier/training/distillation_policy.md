# PDF Model Distillation Policy

This policy defines the heavy-training to lightweight-runtime boundary for the
two PDF assist-model targets.

## Teacher Boundary

Teacher training may be:

* local-only
* dataset-rich
* slow
* large

Teacher inputs may combine:

* `DocLayNet` gold data
* `PubLayNet` weak-layout supplements
* `PubTables-1M` table-specialist subsets
* existing repo-specific local labels

Teacher models are offline analysis tools. They are not CLI dependencies.

## Distillation Targets

Teacher outputs are only useful if they can be distilled into smaller,
reviewable forms such as:

1. rule suggestions
2. feature-importance summaries
3. error-cluster reports
4. confidence thresholds
5. lightweight classifier candidates

## Runtime Boundary

If runtime is ever revisited later:

* deterministic rules remain primary
* runtime candidates must stay lightweight
* runtime support must be optional
* all model influence must fail closed
* parser/layout and convert-layer targets must remain separate

Not allowed:

* direct runtime use of a heavy teacher checkpoint
* flattening `layout_recovery_model` and `text_block_classifier` into one label
  space
* treating weak-label datasets as gold eval
