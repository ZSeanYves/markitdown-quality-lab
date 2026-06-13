# semantic_arbitration Feature Contract

Layer:

* PDF convert-layer semantic arbitration

Consumer:

* future convert-owned low-confidence semantic helper

## Inputs

Expected feature families:

* parser/model-owned typed evidence rows, not raw Markdown output
* cross-page merge/split evidence
* heading-boundary evidence
* image-text or caption-association evidence
* source refs, page index, subject/related id relation graph
* reason tags, risk tags, blockers, and confidence
* optional reviewed gold labels added later in quality-lab

## Outputs

Allowed output families:

* heading vs paragraph hints
* title/body split hints
* list/body ownership hints
* merge/split hints
* caption association hints
* abstain or low-confidence flags

## Hard Boundaries

The semantic arbitration lane:

* must not consume product Markdown or expected samples as automatic gold
* must not rewrite parser-owned canonical layout
* must not flatten parser/layout recovery into convert semantics
* must not be treated as runtime-ready just because weak labels exist
* must keep gold, weak, and unlabeled rows explicitly separated
