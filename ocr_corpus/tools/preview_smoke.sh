#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
corpus_dir="$(cd "${script_dir}/.." && pwd)"
repo_root="$(cd "${corpus_dir}/../.." && pwd)"
manifest="${corpus_dir}/manifest.tsv"
out_dir="${repo_root}/.tmp/ocr_corpus_preview"

if ! command -v tesseract >/dev/null 2>&1; then
  echo "preview_status=skipped reason=tesseract_missing"
  exit 0
fi

mkdir -p "${out_dir}"

python3 - "${manifest}" "${corpus_dir}" <<'PY' | while IFS=$'\t' read -r sample_id relative_path language_hint scenario sha256; do
import csv
import sys
from pathlib import Path

manifest = Path(sys.argv[1])
corpus_dir = Path(sys.argv[2])

with manifest.open() as f:
    reader = csv.DictReader(f, delimiter="\t")
    for row in reader:
        relative_path = row["relative_path"].strip()
        if not relative_path:
            continue
        if row["local_only"].strip() != "false":
            continue
        sample_path = corpus_dir / relative_path
        if not sample_path.exists():
            continue
        print(
            row["id"],
            relative_path,
            row["language_hint"].strip(),
            row["scenario"].strip(),
            row["sha256"].strip(),
            sep="\t",
        )
PY
  ext="$(printf '%s' "${relative_path##*.}" | tr '[:upper:]' '[:lower:]')"
  if [[ "${scenario}" == *"pdf_page_image"* ]] || [[ "${ext}" == "pdf" ]]; then
    echo "${sample_id}	skipped	pdf_page_image row skipped by image-only smoke	scope boundary: no PDF OCR run" 
    continue
  fi
  if [[ "${ext}" != "png" && "${ext}" != "jpg" && "${ext}" != "jpeg" && "${ext}" != "tif" && "${ext}" != "tiff" && "${ext}" != "bmp" ]]; then
    echo "${sample_id}	skipped	unsupported_format	${relative_path}"
    continue
  fi
  sample_path="${corpus_dir}/${relative_path}"
  stem="${sample_id}"
  out_base="${out_dir}/${stem}"
  lang="eng"
  case "${language_hint}" in
    ar* ) lang="ara" ;;
    zh* ) lang="chi_sim" ;;
    ja* ) lang="jpn" ;;
    ko* ) lang="kor" ;;
    es* ) lang="spa" ;;
  esac
  if ! tesseract --list-langs 2>/dev/null | awk 'NR>1 {print $1}' | grep -Fxq "${lang}"; then
    if [[ "${lang}" != "eng" ]]; then
      echo "${sample_id}	not_run	missing_language_pack:${lang}	${relative_path}"
      continue
    fi
  fi
  if tesseract "${sample_path}" "${out_base}" -l "${lang}" --psm 6 >/dev/null 2>&1; then
    echo "${sample_id}	ran	lang=${lang}	${out_base}.txt"
  else
    echo "${sample_id}	failed	tesseract_error	${relative_path}"
  fi
done
