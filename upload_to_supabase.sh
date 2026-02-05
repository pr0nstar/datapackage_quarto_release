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
  curl -sS --fail \
    -X PUT \
    -H "Authorization: Bearer ${SUPABASE_SERVICE_ROLE_KEY}" \
    -H "apikey: ${SUPABASE_SERVICE_ROLE_KEY}" \
    -H "Content-Type: application/zip" \
    --data-binary @"${file}" \
    "${SUPABASE_URL}/storage/v1/object/${SUPABASE_BUCKET}/${encoded_name}.zip?upsert=true"
done
