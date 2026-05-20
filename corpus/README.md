# Quality Corpus

`corpus/sources/...` is the canonical location for external quality payloads.

Compatibility note:

The main repository still has a one-cycle fallback for legacy
`.external/quality_corpus/...` paths. This lab keeps a compatibility tree under
`corpus/` so the main repo can resolve legacy local-manifest paths without
changing assertion rows.
