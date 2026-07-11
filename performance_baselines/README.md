# Performance Baselines

This directory stores reviewed, platform-specific baselines for cases whose
performance is not compared with Microsoft MarkItDown.

- `macos-arm64.json` is produced on the declared macOS arm64 runner class.
- `linux-x64.json` is produced on the declared Linux x64 runner class.
- A baseline is usable only when every environment fingerprint matches.
- Fingerprint mismatches produce a candidate artifact and never silently
  reuse historical timing data.

The schema is defined by `schema.json`. Baseline updates require the raw
benchmark run, main repository SHA, quality repository SHA, input hashes, and
an explicit review status.
