# Teacher Distillation Plan

## Goal

The goal is to use heavier offline training to improve Task A quality, while
keeping any eventual runtime candidate lightweight and optional.

This plan applies to:

- `Task A: convert_block_classification`
- layer: `convert/pdf`

It does not mix in `Task B: parser_boundary_assist`.

## Teacher Objective

The teacher should maximize offline Task A label quality and help us understand
where the deterministic rule system is strong, weak, or ambiguous.

Focus areas include:

- `heading`
- `footer_header_noise`
- `table_like`
- `caption`
- `list_item`
- `form_row`
- `paragraph`

## Teacher Inputs

Teacher training may use a broader local-only input mix such as:

- larger local-only `DocLayNet` gold subsets;
- `PubLayNet` weak layout supplements;
- `PubTables-1M` `table_like` specialist subsets;
- existing repo manual labels;
- synthetic adapter fixtures only for parser sanity, not real training weight.

## Teacher Boundaries

The teacher:

- may be large;
- may be slow;
- may require local-only artifacts;
- must not become a runtime dependency;
- must not be described as the CLI model.

Not allowed:

- directly wiring the teacher into runtime;
- using weak-label data as gold eval;
- mixing Task B boundary labels into Task A training;
- using OCR as the intended route for this track.

## Distillation Targets

The teacher is useful only if its outputs can be distilled into smaller,
reviewable forms.

Primary distillation outputs:

1. rule suggestions
2. feature importance
3. error clusters
4. lightweight classifier candidate
5. confidence thresholds

Examples:

- a heading decision table based on font, position, numbering, and repetition;
- a footer/header noise threshold suggestion;
- a table-like negative/positive feature summary;
- a compact runtime-candidate spec that can be evaluated separately.

## Runtime Boundary

Runtime, if ever revisited later, must stay:

- lightweight;
- fail-closed;
- gated by deterministic rules;
- explainable at the feature or rule level.

This means the runtime candidate can be:

- distilled rules;
- a tiny feature-based classifier;
- confidence-gated suggestions consumed by existing rules.

It must not be:

- a heavy teacher checkpoint;
- a large dependency chain in the CLI;
- a replacement for deterministic conversion logic.

## Suggested Pipeline

1. acquire larger local-only Task A corpora;
2. adapt all sources into a common Task A export format;
3. train and evaluate one or more offline teachers;
4. study high-value error clusters and feature behavior;
5. distill into rule ideas and lightweight candidate specs;
6. evaluate lightweight candidates separately under fail-closed assumptions.

## Evaluation Boundary

Keep these evaluations separate:

- gold-only teacher eval on `DocLayNet`;
- weak-label supplemental analysis on `PubLayNet`;
- specialist `table_like` analysis on `PubTables-1M`;
- repo-specific local label sanity checks.

Do not flatten these into one score that hides the difference between gold and
weak sources.
