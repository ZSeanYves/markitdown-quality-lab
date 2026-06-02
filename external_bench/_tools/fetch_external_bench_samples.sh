#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLAN="$ROOT/FETCH_PLAN.tsv"
MANIFEST="$ROOT/MANIFEST.tsv"
APPLY=0
REPLACE=0
ALLOW_LARGE=0
ALLOW_XLARGE=0
SLEEP_SECONDS=1
CURL_LIMIT_RATE="2m"
USER_AGENT="markitdown-external-bench-fetch/0.1 (+https://github.com/ZSeanYves/markitdown-quality-lab; dry-run-by-default)"
MANIFEST_HEADER='bench_id	format	source_group	rel_path	size_class	bytes	sha256	media_type	compression	archive_member_count	source_url	landing_url	license_spdx	license_url	attribution_required	redistributable	fetch_method	fetched_at	source_version	workload_tags	parser_stages	bench_layers	bench_profile	enabled_tier	notes'

usage() {
  cat <<'USAGE'
Usage: fetch_external_bench_samples.sh [--apply] [--replace] [--allow-large] [--allow-xlarge]
       [--plan PATH] [--manifest PATH] [--sleep SECONDS] [--limit-rate RATE]

Default mode is dry-run. --apply is required before any payload is downloaded.
USAGE
}

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply) APPLY=1 ;;
    --replace) REPLACE=1 ;;
    --allow-large) ALLOW_LARGE=1 ;;
    --allow-xlarge) ALLOW_XLARGE=1; ALLOW_LARGE=1 ;;
    --plan) PLAN="$2"; shift ;;
    --manifest) MANIFEST="$2"; shift ;;
    --sleep) SLEEP_SECONDS="$2"; shift ;;
    --limit-rate) CURL_LIMIT_RATE="$2"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) fail "unknown argument: $1" ;;
  esac
  shift
done

[[ -f "$PLAN" ]] || fail "fetch plan not found: $PLAN"

declare -A COL
read_header() {
  local header
  IFS= read -r header < "$PLAN" || fail "empty fetch plan: $PLAN"
  IFS=$'\t' read -r -a columns <<< "$header"
  for i in "${!columns[@]}"; do
    COL["${columns[$i]}"]="$i"
  done
  local required=(
    bench_id format source_group size_class target_rel_path landing_url
    source_url license_id license_url terms_url bench_layers enabled_tier
    review_status notes
  )
  for name in "${required[@]}"; do
    [[ -n "${COL[$name]+set}" ]] || fail "missing FETCH_PLAN.tsv column: $name"
  done
}

get_field() {
  local name="$1"
  local index="${COL[$name]}"
  printf '%s' "${ROW[$index]:-}"
}

valid_tier() {
  case "$1" in
    smoke|full|manual) return 0 ;;
    disabled|pending_review|unknown|"") return 1 ;;
    *) fail "invalid enabled_tier '$1' for $2" ;;
  esac
}

valid_review_status() {
  case "$1" in
    reviewed_candidate|approved|fully_approved) return 0 ;;
    pending_review|disabled|unknown|"") return 1 ;;
    *) fail "invalid review_status '$1' for $2" ;;
  esac
}

check_rel_path() {
  local format="$1" source_group="$2" size_class="$3" rel_path="$4"
  local prefix="$format/$source_group/$size_class/"
  [[ "$rel_path" != /* ]] || fail "$rel_path must be relative"
  [[ "$rel_path" != *".."* ]] || fail "$rel_path must not contain '..'"
  [[ "$rel_path" == "$prefix"* ]] || fail "$rel_path must live under $prefix"
}

check_size_gate() {
  local bench_id="$1" size_class="$2"
  case "$size_class" in
    tiny|small|medium) return 0 ;;
    large)
      [[ "$ALLOW_LARGE" -eq 1 ]] && return 0
      printf 'SKIP\t%s\tlarge requires --allow-large\n' "$bench_id"
      return 1
      ;;
    xlarge)
      [[ "$ALLOW_XLARGE" -eq 1 ]] && return 0
      printf 'SKIP\t%s\txlarge requires --allow-xlarge\n' "$bench_id"
      return 1
      ;;
    *) fail "invalid size_class '$size_class' for $bench_id" ;;
  esac
}

media_type_for_format() {
  case "$1" in
    pdf) printf 'application/pdf' ;;
    html) printf 'text/html' ;;
    docx) printf 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ;;
    xlsx) printf 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ;;
    pptx) printf 'application/vnd.openxmlformats-officedocument.presentationml.presentation' ;;
    epub) printf 'application/epub+zip' ;;
    csv) printf 'text/csv' ;;
    json) printf 'application/json' ;;
    xml) printf 'application/xml' ;;
    txt) printf 'text/plain' ;;
    yaml) printf 'application/yaml' ;;
    markdown) printf 'text/markdown' ;;
    zip) printf 'application/zip' ;;
    *) printf 'application/octet-stream' ;;
  esac
}

compression_for_format() {
  case "$1" in
    epub|zip|docx|xlsx|pptx) printf 'zip-container' ;;
    *) printf 'none' ;;
  esac
}

attribution_for_license() {
  case "$1" in
    LicenseRef-US-Gov-Public-Domain|LicenseRef-SERC-Public-Domain) printf 'no' ;;
    *) printf 'yes' ;;
  esac
}

ensure_manifest() {
  if [[ ! -f "$MANIFEST" ]]; then
    printf '%s\n' "$MANIFEST_HEADER" > "$MANIFEST"
  fi
}

upsert_manifest_row() {
  local bench_id="$1" format="$2" source_group="$3" rel_path="$4"
  local size_class="$5" bytes="$6" sha256="$7" source_url="$8"
  local landing_url="$9" license_id="${10}" license_url="${11}"
  local bench_layers="${12}" enabled_tier="${13}" notes="${14}"
  local fetched_at media_type compression attribution tmp
  fetched_at="$(date -u +%Y-%m-%d)"
  media_type="$(media_type_for_format "$format")"
  compression="$(compression_for_format "$format")"
  attribution="$(attribution_for_license "$license_id")"
  notes="${notes//$'\t'/ }"
  notes="${notes//$'\n'/ }"
  ensure_manifest
  tmp="$(mktemp "${MANIFEST}.tmp.XXXXXX")"
  awk -F '\t' -v id="$bench_id" 'NR == 1 || $1 != id { print }' "$MANIFEST" > "$tmp"
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t0\t%s\t%s\t%s\t%s\t%s\tyes\tfetch_plan\t%s\tcurrent\tplanned_external_bench\tparse;inspect\t%s\tdefault\t%s\t%s\n' \
    "$bench_id" "$format" "$source_group" "$rel_path" "$size_class" "$bytes" "$sha256" \
    "$media_type" "$compression" "$source_url" "$landing_url" "$license_id" "$license_url" \
    "$attribution" "$fetched_at" "$bench_layers" "$enabled_tier" "$notes" >> "$tmp"
  mv "$tmp" "$MANIFEST"
}

read_header
printf 'mode=%s plan=%s manifest=%s\n' "$([[ "$APPLY" -eq 1 ]] && printf apply || printf dry-run)" "$PLAN" "$MANIFEST"

{
  IFS= read -r _header
  while IFS=$'\t' read -r -a ROW || [[ "${#ROW[@]}" -gt 0 ]]; do
    [[ "${#ROW[@]}" -eq 0 || -z "${ROW[*]}" || "${ROW[0]:-}" == \#* ]] && continue
    bench_id="$(get_field bench_id)"
    format="$(get_field format)"
    source_group="$(get_field source_group)"
    size_class="$(get_field size_class)"
    rel_path="$(get_field target_rel_path)"
    landing_url="$(get_field landing_url)"
    source_url="$(get_field source_url)"
    license_id="$(get_field license_id)"
    license_url="$(get_field license_url)"
    bench_layers="$(get_field bench_layers)"
    enabled_tier="$(get_field enabled_tier)"
    review_status="$(get_field review_status)"
    notes="$(get_field notes)"

    [[ -n "$bench_id" && -n "$source_url" && -n "$landing_url" && -n "$license_id" ]] || fail "missing required field in fetch row"
    check_rel_path "$format" "$source_group" "$size_class" "$rel_path"
    if ! valid_tier "$enabled_tier" "$bench_id"; then
      printf 'SKIP\t%s\tenabled_tier=%s\n' "$bench_id" "$enabled_tier"
      continue
    fi
    if ! valid_review_status "$review_status" "$bench_id"; then
      printf 'SKIP\t%s\treview_status=%s\n' "$bench_id" "$review_status"
      continue
    fi
    check_size_gate "$bench_id" "$size_class" || continue

    dest="$ROOT/$rel_path"
    partial="$dest.partial"
    if [[ -e "$dest" && "$REPLACE" -ne 1 ]]; then
      printf 'SKIP\t%s\texists: %s\n' "$bench_id" "$rel_path"
      continue
    fi
    if [[ "$APPLY" -ne 1 ]]; then
      printf 'DRY-RUN\t%s\t%s -> %s\n' "$bench_id" "$source_url" "$rel_path"
      continue
    fi

    mkdir -p "$(dirname "$dest")"
    rm -f "$partial"
    if ! curl --fail --location --retry 3 --retry-delay 2 --connect-timeout 20 --max-time 600 \
      --speed-limit 1024 --speed-time 30 \
      --limit-rate "$CURL_LIMIT_RATE" --user-agent "$USER_AGENT" --output "$partial" "$source_url"; then
      rm -f "$partial"
      fail "curl failed for $bench_id"
    fi
    bytes="$(wc -c < "$partial" | tr -d '[:space:]')"
    if [[ "$bytes" -eq 0 ]]; then
      rm -f "$partial"
      fail "download produced zero bytes for $bench_id"
    fi
    sha256="$(sha256sum "$partial" | awk '{ print $1 }')"
    mv "$partial" "$dest"
    upsert_manifest_row "$bench_id" "$format" "$source_group" "$rel_path" "$size_class" \
      "$bytes" "$sha256" "$source_url" "$landing_url" "$license_id" "$license_url" \
      "$bench_layers" "$enabled_tier" "$notes"
    printf 'FETCHED\t%s\t%s\t%s\t%s\n' "$bench_id" "$rel_path" "$bytes" "$sha256"
    sleep "$SLEEP_SECONDS"
  done
} < "$PLAN"
