#!/usr/bin/env bash
set -euo pipefail

MODEL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LAB_ROOT="$(cd "$MODEL_ROOT/.." && pwd)"
MAIN_ROOT="$(cd "$LAB_ROOT/.." && pwd)"
MANIFEST_OVERRIDE=""
LAB_ROOT_OVERRIDE=""
CORPUS_ROOT_OVERRIDE=""
OUT_DIR_OVERRIDE=""
SPLIT_FILTER=""

usage() {
  cat <<'EOF'
usage: ./markitdown-quality-lab/pdf_model_training/scripts/export_features.sh [--split train|heldout] [--manifest <path>] [--lab-root <path>] [--corpus-root <path>] [--out-dir <path>]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --split)
      [[ $# -ge 2 ]] || {
        echo "missing value for --split" >&2
        exit 1
      }
      SPLIT_FILTER="$2"
      shift
      ;;
    --manifest)
      [[ $# -ge 2 ]] || {
        echo "missing value for --manifest" >&2
        exit 1
      }
      MANIFEST_OVERRIDE="$2"
      shift
      ;;
    --lab-root)
      [[ $# -ge 2 ]] || {
        echo "missing value for --lab-root" >&2
        exit 1
      }
      LAB_ROOT_OVERRIDE="$2"
      shift
      ;;
    --corpus-root)
      [[ $# -ge 2 ]] || {
        echo "missing value for --corpus-root" >&2
        exit 1
      }
      CORPUS_ROOT_OVERRIDE="$2"
      shift
      ;;
    --out-dir)
      [[ $# -ge 2 ]] || {
        echo "missing value for --out-dir" >&2
        exit 1
      }
      OUT_DIR_OVERRIDE="$2"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage >&2
      exit 1
      ;;
  esac
  shift
done

CMD=(python3 "$MODEL_ROOT/scripts/export_manifest_features.py")
if [[ -n "$LAB_ROOT_OVERRIDE" ]]; then
  CMD+=(--lab-root "$LAB_ROOT_OVERRIDE")
fi
if [[ -n "$CORPUS_ROOT_OVERRIDE" ]]; then
  CMD+=(--corpus-root "$CORPUS_ROOT_OVERRIDE")
fi
if [[ -n "$MANIFEST_OVERRIDE" ]]; then
  CMD+=(--manifest "$MANIFEST_OVERRIDE")
else
  CMD+=(--manifest "$MODEL_ROOT/manifest.example.tsv")
fi
if [[ -n "$OUT_DIR_OVERRIDE" ]]; then
  CMD+=(--output-dir "$OUT_DIR_OVERRIDE")
fi
if [[ -n "$SPLIT_FILTER" ]]; then
  CMD+=(--split "$SPLIT_FILTER")
fi

"${CMD[@]}"
