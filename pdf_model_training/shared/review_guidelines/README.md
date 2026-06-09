# Review Guidelines

Review model outputs by layer.

## Parser Layer

For `layout_recovery`, review:

* region label correctness
* reading-order candidates
* repeated header/footer regions
* multi-column risks
* cross-page merge candidates
* low-signal or malformed layouts

## Convert Layer

For `text_block_classifier`, review:

* semantic role labels
* confidence calibration
* abstain behavior
* heading/list/paragraph confusions
* caption and table-like leakage
* footer/header and page-number false positives

Runtime candidates require separate review from teacher-quality metrics.
