# Shared PDF Model Training Contracts

This directory keeps cross-model contracts that are safe to version and review.

It does not contain raw datasets, trained model parameters, feature matrices,
prediction dumps, or runtime assets.

## Subdirectories

```text
schemas/
feature_contracts/
label_provenance/
report_templates/
review_guidelines/
```

The shared contracts support the two-model boundary:

* `layout_recovery` is parser-facing.
* `text_block_classifier` is convert-facing.
* `layout_recovery` outputs may become input features for
  `text_block_classifier`.
* `text_block_classifier` outputs must not feed back into parser-owned
  canonical layout.
