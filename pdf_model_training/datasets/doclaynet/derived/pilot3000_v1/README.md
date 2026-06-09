# DocLayNet pilot3000_v1

Current local-only text-block adapter output:

```text
pdf_model_training/text_block_classifier/local_only/adapter_outputs/doclaynet/pilot3000_v1/task_a_rows.tsv
```

Logical row count, parsed as TSV:

```text
82373
```

Split counts:

| split | rows |
| --- | ---: |
| train | 60447 |
| dev | 10803 |
| heldout | 11123 |

Current feature export:

```text
pdf_model_training/text_block_classifier/local_only/features/doclaynet/pilot3000_v1/baseline_v3/features.tsv
```

Current baseline reports:

```text
pdf_model_training/text_block_classifier/local_only/reports/pilot3000_v1_lr_baseline_v3/metrics.json
pdf_model_training/text_block_classifier/local_only/reports/pilot3000_v1_rf_baseline_v3/metrics.json
pdf_model_training/text_block_classifier/local_only/reports/pilot3000_v1_hgb_baseline_v3/metrics.json
```

Important parsing note:

* Do not trust plain shell line counts for these TSV files.
* Some text fields contain embedded newlines or separators.
* Use a TSV parser such as Python `csv.DictReader` when computing row counts.

All referenced data files are local-only.
