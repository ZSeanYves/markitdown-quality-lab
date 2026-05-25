#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: preview_smoke.sh [--out-dir DIR] [--sample-id ID] [--summary-only]
USAGE
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
corpus_dir="$(cd "${script_dir}/.." && pwd)"
repo_root="$(cd "${corpus_dir}/../.." && pwd)"
manifest="${corpus_dir}/manifest.tsv"
out_dir="${repo_root}/.tmp/external_quality_ocr_preview"
summary_only=false
sample_id_filter=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --out-dir)
      [[ $# -ge 2 ]] || { echo "missing value for --out-dir" >&2; exit 2; }
      out_dir="$2"
      shift 2
      ;;
    --sample-id)
      [[ $# -ge 2 ]] || { echo "missing value for --sample-id" >&2; exit 2; }
      sample_id_filter="$2"
      shift 2
      ;;
    --summary-only)
      summary_only=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown arg: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

mkdir -p "${out_dir}"
summary_path="${out_dir}/preview_summary.tsv"
langs_cache="${out_dir}/.available_langs.txt"

if command -v tesseract >/dev/null 2>&1; then
  tesseract --list-langs 2>/dev/null | awk 'NR>1 {print $1}' | LC_ALL=C sort -u >"${langs_cache}" || :
else
  : >"${langs_cache}"
fi

printf 'sample_id\tstatus\treason\tlanguage_hint\tscenario\toutput_path\n' >"${summary_path}"

append_summary() {
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" "$5" "$6" >>"${summary_path}"
}

status_from_output() {
  python3 - "$1" "$2" "$3" "$4" <<'PY'
import re
import sys
from pathlib import Path
sample_id = sys.argv[1]
out_path = Path(sys.argv[2])
scenario = sys.argv[3]
risk_tags = sys.argv[4]
if not out_path.exists():
    print('failed\toutput_missing')
    raise SystemExit
text = out_path.read_text(errors='ignore')
text = text.strip()
if not text:
    is_negative = 'negative' in scenario.split(';') or any(
        tag in {'no_text', 'text_too_sparse'} for tag in risk_tags.split(';') if tag
    )
    if is_negative:
        print('pass\tno_text_expected')
    else:
        print('weak\tempty_output')
    raise SystemExit
lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
words = re.findall(r'\w+', text, re.UNICODE)
chars = len(re.sub(r'\s+', '', text, flags=re.UNICODE))
if chars >= 160 or len(words) >= 30 or len(lines) >= 6:
    print('pass\tnonempty_text')
else:
    print('weak\tlimited_text')
PY
}

python3 - "${manifest}" "${corpus_dir}" "${sample_id_filter}" <<'PY' | while IFS=$'\t' read -r sample_id relative_path language_hint scenario risk_tags expected_sha; do
import csv
import sys
from pathlib import Path
manifest = Path(sys.argv[1])
corpus_dir = Path(sys.argv[2])
sample_filter = sys.argv[3]
with manifest.open() as f:
    reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        rel = row['relative_path'].strip()
        if not rel:
            continue
        if row['local_only'].strip() != 'false':
            continue
        if sample_filter and row['id'] != sample_filter:
            continue
        p = corpus_dir / rel
        if not p.exists():
            continue
        print(
            row['id'],
            rel,
            row['language_hint'].strip(),
            row['scenario'].strip(),
            row['risk_tags'].strip(),
            row['sha256'].strip(),
            sep='\t',
        )
PY
  ext="$(printf '%s' "${relative_path##*.}" | tr '[:upper:]' '[:lower:]')"
  sample_path="${corpus_dir}/${relative_path}"
  out_base="${out_dir}/${sample_id}"
  out_text="${out_base}.txt"
  status=""
  reason=""

  if [[ "${scenario}" == *"pdf_page_image"* ]] || [[ "${ext}" == "pdf" ]]; then
    status="skipped"
    reason="pdf_page_image"
    append_summary "${sample_id}" "${status}" "${reason}" "${language_hint}" "${scenario}" ""
    printf '%s\t%s\t%s\t%s\n' "${sample_id}" "${status}" "${reason}" ""
    continue
  fi

  case "${ext}" in
    png|jpg|jpeg|tif|tiff|bmp) ;;
    *)
      status="skipped"
      reason="unsupported_format:${ext}"
      append_summary "${sample_id}" "${status}" "${reason}" "${language_hint}" "${scenario}" ""
      printf '%s\t%s\t%s\t%s\n' "${sample_id}" "${status}" "${reason}" ""
      continue
      ;;
  esac

  if ! command -v tesseract >/dev/null 2>&1; then
    status="not_run"
    reason="tesseract_missing"
    append_summary "${sample_id}" "${status}" "${reason}" "${language_hint}" "${scenario}" ""
    printf '%s\t%s\t%s\t%s\n' "${sample_id}" "${status}" "${reason}" ""
    continue
  fi

  lang="eng"
  case "${language_hint}" in
    ar*) lang="ara" ;;
    zh*|cmn*) lang="chi_sim" ;;
    ja*) lang="jpn" ;;
    ko*) lang="kor" ;;
    es*) lang="spa" ;;
  esac

  if ! grep -Fxq "${lang}" "${langs_cache}"; then
    if [[ "${lang}" != "eng" ]]; then
      status="not_run"
      reason="missing_language_pack:${lang}"
      append_summary "${sample_id}" "${status}" "${reason}" "${language_hint}" "${scenario}" ""
      printf '%s\t%s\t%s\t%s\n' "${sample_id}" "${status}" "${reason}" ""
      continue
    fi
  fi

  if [[ "${summary_only}" == "false" ]]; then
    rm -f "${out_text}"
    if ! tesseract "${sample_path}" "${out_base}" -l "${lang}" --psm 6 >/dev/null 2>&1; then
      status="failed"
      reason="tesseract_error"
      append_summary "${sample_id}" "${status}" "${reason}" "${language_hint}" "${scenario}" ""
      printf '%s\t%s\t%s\t%s\n' "${sample_id}" "${status}" "${reason}" ""
      continue
    fi
  fi

  if [[ ! -f "${out_text}" ]]; then
    status="not_run"
    reason="output_missing"
    append_summary "${sample_id}" "${status}" "${reason}" "${language_hint}" "${scenario}" ""
    printf '%s\t%s\t%s\t%s\n' "${sample_id}" "${status}" "${reason}" ""
    continue
  fi

  status_reason="$(status_from_output "${sample_id}" "${out_text}" "${scenario}" "${risk_tags}")"
  status="${status_reason%%$'\t'*}"
  reason="${status_reason#*$'\t'}"
  append_summary "${sample_id}" "${status}" "${reason}" "${language_hint}" "${scenario}" "${out_text}"
  printf '%s\t%s\t%s\t%s\n' "${sample_id}" "${status}" "${reason}" "${out_text}"
done

printf 'preview_summary\tgenerated\t%s\n' "${summary_path}"
