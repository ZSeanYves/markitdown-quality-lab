# OCR Local Only

This directory is for OCR audit files that must not be committed.

Use it for:

* local payload images
* local manifests derived from private or redistribution-restricted samples
* temporary provider outputs generated from local-only inputs

Rules:

* this subtree is git-ignored except for this README and the example manifest
* do not place reviewed commit-safe payloads here
* do not treat local-only rows as product gates or public baselines
* record `sha256`, scenario tags, and risk notes even for local-only rows
