# Label Provenance

Track where labels come from and how they were adapted.

Every non-synthetic row should preserve:

* source dataset
* upstream source label
* target model
* target label
* mapping confidence
* adapter version or mapping file
* split
* local-only path if the row is not tracked

Weak-source rows must remain distinguishable from gold rows.
