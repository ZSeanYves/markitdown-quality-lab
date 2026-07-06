# OCR External Quality

This subtree contains OCR-related external quality material.
It is the OCR-specific branch of the formal `external_quality/` corpus surface.

Subtrees:

- `_legacy_samples/`: legacy tracked OCR fixtures plus checked provider
  artifacts
- `_audit/`: OCR provenance notes, source-group review anchors, and local-only
  policy material
- `commons/`, `irs/`, `self_synthetic/`: source-grouped tracked sample bytes
- `archive/`: legacy or migration-only OCR material

Current recommendation:

- OCR helper scripts in the main repository still target `_legacy_samples/`
- `_audit/PROVENANCE.md` is the current local provenance closure note for the
  retained Commons, IRS, and self-synthetic OCR source groups
- promoted formal rows must still be anchored by
  `external_quality/MANIFEST.tsv` and `external_quality/SOURCE_CATALOG.tsv`
- new tracked bytes should stay source-grouped instead of creating new OCR
  top-level roots
