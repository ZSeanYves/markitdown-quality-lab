# OCR Local Only

This directory is for OCR audit files that must not be committed.

Use it for:

* phone captures of receipts, invoices, menus, labels, and signage
* local manifests derived from private, ambiguous-license, or
  redistribution-restricted samples
* temporary provider outputs generated from local-only inputs
* rendered page-image experiments from sources that are not yet commit-safe

Rules:

* this subtree is git-ignored except for this README and the example manifest
* do not place reviewed commit-safe payloads here
* do not treat local-only rows as product gates or public baselines
* record `sha256`, `scenario`, and `risk_tags` even for local-only rows
* use local-only for any row carrying `pii_risk`, unresolved `license_risk`, or
  real receipt/invoice/address/signature content
