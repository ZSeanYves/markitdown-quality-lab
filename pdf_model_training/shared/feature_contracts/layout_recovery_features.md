# layout_recovery Feature Contract

Layer:

* PDF parser

Consumer:

* parser-owned `PdfDocumentModel` recovery path

## Inputs

Expected feature families:

* page index and page dimensions
* page boxes and rotation
* raw text, glyph, char, span, line, and block geometry
* image, vector, annotation, and form geometry
* content stream order and object/source references
* neighboring region geometry
* repeated edge-region evidence across pages

## Outputs

Allowed output families:

* page and region labels
* reading-order candidates
* column and multi-column hints
* cross-page merge and no-merge candidates
* risk scores
* low-confidence or abstain flags

## Runtime Boundary

Only high-confidence distilled rules or reviewed lightweight candidates may be
considered for runtime later. Heavy teacher checkpoints and local-only features
must remain external-only.

`layout_recovery` must not consume convert-layer text-block labels as canonical
parser truth.
