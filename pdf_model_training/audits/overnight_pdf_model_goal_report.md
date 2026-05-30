# Overnight PDF Model Goal Report

Date: 2026-05-31

## Decision

Runtime integration is not approved.

This run successfully completed the offline `text_block_classifier`
train/evaluate/distillation loop and the `layout_recovery_model` audit, but the
explicit runtime safety gates are not all satisfied:

* `footer_header_noise` has strong DocLayNet heldout evidence, but the expanded
  external-quality report-only emit set has no completed manual-review
  precision yet.
* `heading` still emits wrong rows under the v1/cooperative gates and must not
  default emit.
* `keep_as_text` still needs guard refinement and must not default emit.
* `paragraph`, `list_item`, `table_like`, and `caption` remain blocked from
  runtime override.
* `layout_recovery_model` does not yet have mature independent gold data for
  training.

No converter/runtime hook was created, and default Markdown output was not
changed.

## Environment And Repository State

Environment:

* Python: `3.11.13`
* Python path: `/home/zseanyves/miniforge3/envs/isaac-lab/bin/python`
* main repo status before training: clean
* quality-lab status before training: clean
* main repo status before report write: clean
* quality-lab status before report write: clean

Artifact boundary:

* `local_only/` outputs are ignored by quality-lab `.gitignore`.
* The only tracked artifact intended from this run is this audit report.
* No `moon.mod.json` migration diff was created.
* No OCR provider was used.
* External-quality rows were used only as validation/report-only dry-run rows,
  not as training gold.

## Reused Local Data

Reusable local DocLayNet assets:

* `DocLayNet_core.zip`
* `DocLayNet_extra.zip`
* `pilot500_v1`, `pilot1000_v1`, and `pilot3000_v1` subsets
* adapter outputs with `task_a_rows.tsv` and train/dev/heldout splits
* baseline features for `pilot500_v1`, `pilot1000_v1`, and `pilot3000_v1`
* existing local-only models/reports for LR, RF, and HGB runs

Primary feature set audited:

* path: `text_block_classifier/local_only/features/doclaynet/pilot3000_v1/baseline_v3/features.tsv`
* rows: `82373`
* fields: `118`
* train/dev/heldout rows: `60447` / `10803` / `11123`
* missing text rows: `0`
* leak-like non-meta fields: none detected

Pilot3000 label distribution:

| label | train | dev | heldout |
| --- | ---: | ---: | ---: |
| caption | 1526 | 319 | 286 |
| footer_header_noise | 3693 | 846 | 695 |
| heading | 9740 | 1748 | 1715 |
| keep_as_text | 2081 | 168 | 232 |
| list_item | 17744 | 2673 | 3378 |
| paragraph | 23680 | 4738 | 4393 |
| table_like | 1983 | 311 | 424 |

## Text Block Classifier Training

Re-ran three `pilot3000_v1` / `baseline_v3` model families into new local-only
run IDs:

| run | model | dev macro F1 | dev accuracy | heldout macro F1 | heldout accuracy |
| --- | --- | ---: | ---: | ---: | ---: |
| `overnight_20260531_pilot3000_lr_baseline_v3` | logistic regression | 0.6748 | 0.7387 | 0.6559 | 0.6875 |
| `overnight_20260531_pilot3000_rf_baseline_v3` | random forest | 0.8270 | 0.8605 | 0.7880 | 0.8125 |
| `overnight_20260531_pilot3000_hgb_baseline_v3` | HGB teacher | 0.8311 | 0.8585 | 0.8097 | 0.8269 |

Best teacher:

* `overnight_20260531_pilot3000_hgb_baseline_v3`
* matches the previous best-known HGB metrics
* heldout macro F1 clears the `>= 0.80` model-quality gate
* remains local-only and offline-only

HGB heldout per-label metrics:

| label | support | precision | recall | F1 |
| --- | ---: | ---: | ---: | ---: |
| caption | 286 | 0.5631 | 0.6084 | 0.5849 |
| footer_header_noise | 695 | 0.9684 | 0.9712 | 0.9698 |
| heading | 1715 | 0.7331 | 0.8793 | 0.7996 |
| keep_as_text | 232 | 0.8261 | 0.7371 | 0.7790 |
| list_item | 3378 | 0.8503 | 0.7783 | 0.8127 |
| paragraph | 4393 | 0.8472 | 0.8329 | 0.8400 |
| table_like | 424 | 0.8643 | 0.9009 | 0.8822 |

Top heldout confusion pairs:

| gold | predicted | count |
| --- | --- | ---: |
| list_item | paragraph | 484 |
| paragraph | list_item | 327 |
| list_item | heading | 242 |
| paragraph | heading | 218 |
| paragraph | caption | 110 |

Observed failure clusters:

* patent classification/search lines remain a major paragraph/list/heading
  ambiguity source
* legal and procurement-like contract rows confuse paragraph and list-like
  structure
* scientific affiliations and short author rows confuse paragraph/list/heading
* caption/table boundary remains weak enough that `caption` stays denied
* government/financial/form-like edge rows are exactly where report-only guards
  need manual review before runtime discussion

## Distillation And Cooperative Gates

Re-exported HGB heldout hints:

* output: `local_only/reports/overnight_20260531_distillation/overnight_hgb_hints_heldout.tsv`
* thresholds: `0.90`, `0.95`
* allowed v0 labels: `footer_header_noise`, `heading`, `keep_as_text`,
  `list_item`, `paragraph`, `table_like`
* denied v0 labels: `caption`

At threshold `0.95`:

* emitted rows: `4553`
* wrong prediction rows: `123`
* strongest wrong clusters: `list_item -> paragraph`, `paragraph -> list_item`,
  `paragraph -> table_like`, `paragraph -> heading`

This confirms that broad high-confidence v0 hints are not runtime-safe.

V1 gate at threshold `0.95`:

* total heldout rows: `11123`
* emitted rows: `1219`
* emitted accuracy: `0.9779`
* wrong emitted count: `27`

V1 per-label interpretation:

| label | emitted precision | recommendation |
| --- | ---: | --- |
| footer_header_noise | 0.9975 | external-quality dry run only |
| heading | 0.9670 | needs more guard |
| keep_as_text | 0.9778 | needs more guard |
| paragraph | 0.0000 | deny |
| list_item | 0.0000 | deny |
| table_like | 0.0000 | deny |
| caption | 0.0000 | deny |

Cooperative gate, `conservative_v2`, model confidence `>= 0.95`:

| cooperative threshold | emitted | wrong emitted | emitted labels |
| ---: | ---: | ---: | --- |
| 0.80 | 1038 | 22 | footer_header_noise, heading |
| 0.85 | 693 | 3 | footer_header_noise, heading |
| 0.90 | 292 | 0 | footer_header_noise only |

Distillation candidate decision:

* `footer_header_noise`: keep as report-only candidate with high confidence,
  rule support, context sanity, hard conflict guards, and manual review.
* `heading`: audit only; do not emit.
* `keep_as_text`: audit only; do not emit.
* `paragraph`, `list_item`, `table_like`, `caption`: no runtime override.

## External Quality Report-Only Dry Run

Re-ran the external-quality PDF report-only dry run:

* run: `overnight_20260531_pdf_all_conservative_v2`
* profile: `conservative_v2`
* model confidence threshold: `0.95`
* cooperative threshold: `0.85`
* target label: `footer_header_noise`
* selected rows: `80`
* processed rows: `79`
* skipped rows: `1`
* candidate rows: `598`
* emitted report-only hints: `34`
* hard conflicts: `71`
* no override: `493`

The feature bridge was compatible:

* matched legacy feature rows: `598`
* output feature rows: `598`
* missing feature columns: none
* extra feature columns: none
* missing candidate sample IDs: `0`

Emit distribution:

* `pdf_niosh_2015_100_public_domain_booklet`: `21`
* `pdf_irs_w4_form_official_counts`: `6`
* `md_test_pdf`: `2`
* `pdf_section_numbering_markitdown_test`: `2`
* `pdf_tounicode_unicode_markitdown_test`: `2`
* `pdf_booking_layout_markitdown_movie`: `1`

Risk readout:

* NIOSH emits look like repeated booklet header/page-number shells.
* IRS W-4 emits include table/form numbers and an amount-like row; these need
  manual review before any precision claim.
* The existing manual-review TSV has `58` rows and `58` blank
  `reviewer_decision` values.

External-quality report-only precision is therefore `waiting_for_manual_review`,
not `>= 0.99`. This blocks runtime hook/proposal creation.

## Layout Recovery Model

Task B remains separate from Task A.

Current `layout_recovery_model` state:

* active manifest is header-only
* dataset plan is documented but planned/review status only
* label mapping covers layout-region concepts such as table, caption, figure,
  header/footer, and text/heading regions
* archived repo-manual boundary rows are tiny historical references
* debug layout assist TSVs are smoke/debug scale, not mature training gold

Decision:

* no layout recovery model was trained
* no runtime hints were proposed
* no hard layout rule override was created

Acquisition plan:

* define a public-source adapter for region-level DocLayNet layout recovery
  rows without mixing block semantics
* keep reading order, column boundary, paragraph boundary, cross-page merge,
  and attachment relation labels explicit and separate
* use PubLayNet only as weak layout evidence
* use PubTables only as a table-region specialist source
* build an independent heldout eval before any runtime discussion

## PubTables Specialist

No large PubTables data was downloaded.

Available local/tracked evidence:

* `dataset/source_metadata/pubtables_1m/first_rows_train.json`
* metadata preview rows: `100`
* parsed table objects: `126`

Interpretation:

* the preview validates the XML/table-box schema
* no local page images, word JSON, or adapter outputs are present
* this is suitable for adapter planning and smoke only
* it must not be mixed into DocLayNet gold heldout

Recommended next specialist step:

* create a local-only adapter smoke that emits `table_like` positives from
  table boxes when real local PubTables bytes are available
* keep `caption` as weak/audit-only
* keep source-separated reports

## Quality Validation

Validation commands run after offline model work:

| command | result |
| --- | --- |
| `moon check` | passed |
| `bash samples/check.sh --manifest-only` | passed |
| `bash samples/check.sh` | passed, all 9 stages |
| `bash samples/check_quality.sh --format pdf` | passed, 79 rows / 0 failed / 1 skipped |
| `bash samples/check_quality.sh` | passed, 315 rows / 0 failed / 1 skipped |
| `bash samples/bench.sh --help` | passed |

Because runtime was not modified, no sample expected outputs were updated.

## Safety Gate Summary

| gate | status | note |
| --- | --- | --- |
| text block heldout macro F1 >= 0.80 | pass | HGB heldout macro F1 `0.8097` |
| footer_header_noise report-only precision >= 0.99 | blocked | manual review not completed |
| heading default emit guard | fail | cooperative gates still show wrong heading emits |
| keep_as_text default emit guard | fail | needs more guard refinement |
| paragraph/list/table/caption runtime override | blocked | explicitly out of runtime scope |
| layout recovery independent training/eval | blocked | no mature gold data yet |
| quality regression checks | pass | sample and external-quality checks green |
| default-off report-only integration | not created | previous gates did not pass |

## Final Recommendation

Keep this work offline and report-only.

The next productive step is manual review of the expanded
`footer_header_noise` package, especially the IRS W-4 table/form number emits
and the NIOSH repeated header/page-number emits. If manual precision passes,
the next proposal should still be disabled-by-default and report-only, with
model version, feature schema, confidence, rule support, context sanity, and
hard conflict/no-override reasons recorded for every hint.
