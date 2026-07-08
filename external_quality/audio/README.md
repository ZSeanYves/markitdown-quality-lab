# Audio External Quality

This subtree holds formal external audio quality samples for `markitdown`.

Current source groups:

- `vosk-api/`: Apache-2.0 official `alphacep/vosk-api` example speech sample,
  plus locally derived `mp3` and `m4a` transcodes retained for compressed-audio
  regression coverage.

Rules:

- keep tracked payloads under `external_quality/audio/<source>/`
- keep provenance notes under `external_quality/audio/<source>/_audit/`
- enroll every executable sample in `external_quality/MANIFEST.tsv`
- keep the source group indexed in `external_quality/SOURCE_CATALOG.tsv`
