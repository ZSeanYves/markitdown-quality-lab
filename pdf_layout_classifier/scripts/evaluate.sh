#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TMP_ROOT="${MARKITDOWN_TMP_DIR:-$ROOT/.tmp}"
OUT_ROOT="$TMP_ROOT/pdf_layout_classifier"
FEATURE_DIR="$OUT_ROOT/features"
PRED_DIR="$OUT_ROOT/predictions"
EVAL_DIR="$OUT_ROOT/eval"
SMOKE=0
RUN_HELDOUT=0
LAB_ROOT_OVERRIDE=""
MODEL_ROOT_OVERRIDE=""
MANIFEST_OVERRIDE=""
CORPUS_ROOT_OVERRIDE=""

usage() {
  cat <<'EOF'
usage: ./samples/pdf_layout_classifier/evaluate.sh [--smoke] [--heldout] [--manifest <path>] [--lab-root <path>] [--model-root <path>] [--corpus-root <path>]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --smoke)
      SMOKE=1
      ;;
    --heldout)
      RUN_HELDOUT=1
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
    --model-root)
      [[ $# -ge 2 ]] || {
        echo "missing value for --model-root" >&2
        exit 1
      }
      MODEL_ROOT_OVERRIDE="$2"
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

if [[ "$SMOKE" -eq 1 ]]; then
  RUN_HELDOUT=1
fi

mkdir -p "$FEATURE_DIR" "$PRED_DIR" "$EVAL_DIR"

MANIFEST_PATH="${MANIFEST_OVERRIDE:-$ROOT/samples/pdf_layout_classifier/manifest.tsv}"
MODEL_PATH="$OUT_ROOT/models/pdf_layout_linear.json"
mkdir -p "$(dirname "$MODEL_PATH")"

EXPORT_CMD=("$ROOT/samples/pdf_layout_classifier/export_features.sh")
if [[ -n "$LAB_ROOT_OVERRIDE" ]]; then
  EXPORT_CMD+=(--lab-root "$LAB_ROOT_OVERRIDE")
fi
if [[ -n "$CORPUS_ROOT_OVERRIDE" ]]; then
  EXPORT_CMD+=(--corpus-root "$CORPUS_ROOT_OVERRIDE")
fi
EXPORT_CMD+=(--manifest "$MANIFEST_PATH" --out-dir "$FEATURE_DIR" --split train)
"${EXPORT_CMD[@]}"

if [[ "$RUN_HELDOUT" -eq 1 ]]; then
  EXPORT_HELDOUT_CMD=("$ROOT/samples/pdf_layout_classifier/export_features.sh")
  if [[ -n "$LAB_ROOT_OVERRIDE" ]]; then
    EXPORT_HELDOUT_CMD+=(--lab-root "$LAB_ROOT_OVERRIDE")
  fi
  if [[ -n "$CORPUS_ROOT_OVERRIDE" ]]; then
    EXPORT_HELDOUT_CMD+=(--corpus-root "$CORPUS_ROOT_OVERRIDE")
  fi
  EXPORT_HELDOUT_CMD+=(--manifest "$MANIFEST_PATH" --out-dir "$FEATURE_DIR" --split heldout)
  "${EXPORT_HELDOUT_CMD[@]}"
fi

TRAIN_CMD=(python3 "$ROOT/tools/pdf_layout_classifier/train.py")
if [[ -n "$LAB_ROOT_OVERRIDE" ]]; then
  TRAIN_CMD+=(--lab-root "$LAB_ROOT_OVERRIDE")
fi
if [[ -n "$MODEL_ROOT_OVERRIDE" ]]; then
  TRAIN_CMD+=(--model-root "$MODEL_ROOT_OVERRIDE")
fi
TRAIN_CMD+=(
  --manifest "$MANIFEST_PATH"
  --train-features "$FEATURE_DIR"
  --output "$MODEL_PATH"
  --train-summary "$EVAL_DIR/train_summary.tsv"
)
"${TRAIN_CMD[@]}"

if [[ "$RUN_HELDOUT" -eq 1 ]]; then
  tail -n +2 "$MANIFEST_PATH" | while IFS=$'\t' read -r sample_id pdf_path record_kind split label_source label_path notes; do
    [[ -n "$sample_id" ]] || continue
    if [[ "$split" != "heldout" ]]; then
      continue
    fi
    moon run "$ROOT/tools/pdf_layout_classifier" -- infer \
      --model "$MODEL_PATH" \
      --features "$FEATURE_DIR/$sample_id.features.tsv" \
      --output "$PRED_DIR/$sample_id.predictions.tsv"
  done

  EVAL_CMD=(python3 "$ROOT/tools/pdf_layout_classifier/train.py")
  if [[ -n "$LAB_ROOT_OVERRIDE" ]]; then
    EVAL_CMD+=(--lab-root "$LAB_ROOT_OVERRIDE")
  fi
  if [[ -n "$MODEL_ROOT_OVERRIDE" ]]; then
    EVAL_CMD+=(--model-root "$MODEL_ROOT_OVERRIDE")
  fi
  EVAL_CMD+=(
    --manifest "$MANIFEST_PATH"
    --train-features "$FEATURE_DIR"
    --heldout-features "$FEATURE_DIR"
    --pred-dir "$PRED_DIR"
    --train-summary "$EVAL_DIR/train_summary.tsv"
    --heldout-summary "$EVAL_DIR/heldout_summary.tsv"
    --confusion "$EVAL_DIR/confusion.tsv"
    --errors "$EVAL_DIR/errors.tsv"
    --evaluate-only
  )
  "${EVAL_CMD[@]}"
fi

if [[ "$SMOKE" -eq 1 ]]; then
  head -n 20 "$EVAL_DIR/train_summary.tsv"
  echo
  head -n 20 "$EVAL_DIR/heldout_summary.tsv"
else
  cat "$EVAL_DIR/train_summary.tsv"
  if [[ "$RUN_HELDOUT" -eq 1 ]]; then
    echo
    cat "$EVAL_DIR/heldout_summary.tsv"
    echo
    echo "confusion: $EVAL_DIR/confusion.tsv"
    echo "errors: $EVAL_DIR/errors.tsv"
  fi
fi
