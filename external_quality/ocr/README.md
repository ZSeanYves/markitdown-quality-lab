# OCR External Quality

This subtree contains OCR-related external quality material.

Subtrees:

* `_legacy_samples/`: legacy tracked OCR fixtures plus checked provider artifacts
* `_audit/`: newer OCR real-world audit notes, manifests, and local-only policy
* `commons/`, `irs/`, `self_synthetic/`: source-grouped tracked sample bytes
* `archive/`: legacy or migration-only OCR material

Current recommendation:

* OCR helper scripts in the main repo still target `_legacy_samples/`
* `_audit/` is the planning and corpus-audit surface
* new tracked bytes should stay source-grouped instead of creating new OCR top-level roots
