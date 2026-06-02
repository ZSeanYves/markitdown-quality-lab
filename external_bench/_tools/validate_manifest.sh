#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST="${1:-$ROOT/MANIFEST.tsv}"

python - "$ROOT" "$MANIFEST" <<'PY'
import csv
import hashlib
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
manifest = Path(sys.argv[2])

def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)

if not manifest.is_file():
    fail(f"manifest not found: {manifest}")

required = {
    "bench_id", "format", "source_group", "rel_path", "size_class", "bytes",
    "sha256", "source_url", "landing_url", "license_spdx", "license_url",
    "bench_layers", "enabled_tier",
}
valid_tiers = {"smoke", "full", "manual", "disabled", "pending_review", "unknown"}

with manifest.open(encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f, delimiter="\t")
    if reader.fieldnames is None:
        fail(f"empty manifest: {manifest}")
    missing = sorted(required.difference(reader.fieldnames))
    if missing:
        fail("missing manifest column(s): " + ", ".join(missing))

    row_count = 0
    for line_no, row in enumerate(reader, start=2):
        if not row or (row.get("bench_id", "").lstrip().startswith("#")):
            continue
        for name in sorted(required):
            if not row.get(name, ""):
                fail(f"line {line_no} missing required field: {name}")

        tier = row["enabled_tier"]
        if tier not in valid_tiers:
            fail(f"line {line_no} invalid enabled_tier: {tier}")

        fmt = row["format"]
        source_group = row["source_group"]
        size_class = row["size_class"]
        rel_path = row["rel_path"]
        prefix = f"{fmt}/{source_group}/{size_class}/"
        if rel_path.startswith("/"):
            fail(f"line {line_no} rel_path must be relative")
        if ".." in Path(rel_path).parts:
            fail(f"line {line_no} rel_path must not contain '..'")
        if not rel_path.startswith(prefix):
            fail(f"line {line_no} rel_path must live under {prefix}")

        bytes_text = row["bytes"]
        if not re.fullmatch(r"[0-9]+", bytes_text):
            fail(f"line {line_no} bytes is not numeric: {bytes_text}")
        expected_bytes = int(bytes_text)
        if expected_bytes <= 0:
            fail(f"line {line_no} bytes must be greater than zero")

        expected_sha = row["sha256"].lower()
        if not re.fullmatch(r"[0-9a-f]{64}", expected_sha):
            fail(f"line {line_no} sha256 is not a 64-hex digest")

        path = root / rel_path
        if not path.is_file():
            fail(f"line {line_no} rel_path file missing: {rel_path}")
        data = path.read_bytes()
        if len(data) != expected_bytes:
            fail(f"line {line_no} bytes mismatch for {rel_path}: manifest={expected_bytes} actual={len(data)}")
        actual_sha = hashlib.sha256(data).hexdigest()
        if actual_sha != expected_sha:
            fail(f"line {line_no} sha256 mismatch for {rel_path}")
        row_count += 1

print(f"OK: {row_count} row(s) checked in {manifest}")
PY
