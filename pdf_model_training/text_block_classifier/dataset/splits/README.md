# Text Block Classifier Splits

This directory tracks small split summaries only.

The actual split TSV files are local-only under:

```text
pdf_model_training/text_block_classifier/local_only/adapter_outputs/doclaynet/<subset>/splits/
```

Use a TSV parser for row counts. Some text fields in upstream adapter outputs
can contain embedded separators or newlines, so plain shell line counts are not
a reliable validation gate.
