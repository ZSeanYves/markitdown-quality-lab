# Layout Recovery Source Policy

Tracked content may include:

* dataset registry and source metadata
* adapter specifications
* label mappings
* active manifest headers
* shared adapter contracts for main-repo PDF v2 evidence exports

Local-only content should include:

* larger adapted public-dataset subsets
* teacher features, checkpoints, prediction dumps, and eval artifacts

Recommended local-only root:

```text
pdf_model_training/layout_recovery/local_only/
```

Use mature public annotated layout datasets first:

* `DocLayNet` as the preferred gold region source
* `PubLayNet` as a weak layout supplement
* `PubTables-1M` as a table-region specialist
* main-repo PDF v2 `EvidenceRow` exports only as weak or unlabeled local-only
  scaffold input, never as a DocLayNet replacement

Hard boundaries:

* do not promote repo-manual boundary rows as the active manifest
* do not flatten layout recovery into text block semantics
* do not commit local-only dataset bytes or teacher artifacts
* do not treat project-exported `EvidenceRow` rows as automatic gold
* do not split rows from the same `doc_id` across train/dev/heldout
