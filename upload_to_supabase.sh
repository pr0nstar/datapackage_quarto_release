#!/usr/bin/env bash
set -euo pipefail

if [ -z "${SUPABASE_URL:-}" ] || [ -z "${SUPABASE_SERVICE_ROLE_KEY:-}" ] || [ -z "${SUPABASE_BUCKET:-}" ]; then
  echo "SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, and SUPABASE_BUCKET are required when upload=true." >&2
  exit 1
fi

shopt -s nullglob
files=(build/dist/*.zip)
if [ ${#files[@]} -eq 0 ]; then
  echo "No zip files found in build/dist." >&2
  exit 1
fi

for file in "${files[@]}"; do
  name="$(basename "$file" .zip)"
  encoded_name="$(python - <<'PY' "$name"
import sys
from urllib.parse import quote
print(quote(sys.argv[1]))
PY
)"
  tmp_response="$(mktemp)"
  http_code="$(curl -sS \
    --retry 5 \
    --retry-all-errors \
    --retry-delay 2 \
    --connect-timeout 10 \
    --max-time 300 \
    -X PUT \
    -H "Authorization: Bearer ${SUPABASE_SERVICE_ROLE_KEY}" \
    -H "apikey: ${SUPABASE_SERVICE_ROLE_KEY}" \
    -H "x-upsert: true" \
    -H "Content-Type: application/zip" \
    --data-binary @"${file}" \
    -o "${tmp_response}" \
    -w "%{http_code}" \
    "${SUPABASE_URL}/storage/v1/object/${SUPABASE_BUCKET}/${encoded_name}.zip")"
  if [[ "${http_code}" != 2* ]]; then
    echo "Upload failed for ${file} (HTTP ${http_code}). Response:" >&2
    cat "${tmp_response}" >&2
    rm -f "${tmp_response}"
    exit 1
  fi
  rm -f "${tmp_response}"
done
