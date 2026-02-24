#!/usr/bin/env bash
set -euo pipefail

ALLOWED_PREFIX="${1:-}"
if [[ -z "$ALLOWED_PREFIX" ]]; then
  echo "Usage: $0 <allowed-prefix>" >&2
  echo "Example: $0 projects/ai-translate-saas/" >&2
  exit 2
fi

# normalize: ensure trailing slash
if [[ "$ALLOWED_PREFIX" != */ ]]; then
  ALLOWED_PREFIX="$ALLOWED_PREFIX/"
fi

# Collect changed + untracked files
mapfile -t FILES < <(git status --porcelain=v1 | awk '{print $2}')

if [[ ${#FILES[@]} -eq 0 ]]; then
  echo "OK: no changes"
  exit 0
fi

BAD=0
for f in "${FILES[@]}"; do
  # ignore deletions where file path may be quoted? keep simple
  if [[ "$f" != "$ALLOWED_PREFIX"* ]]; then
    echo "OUT_OF_SCOPE: $f (allowed: $ALLOWED_PREFIX*)" >&2
    BAD=1
  fi
done

if [[ $BAD -eq 1 ]]; then
  echo "FAIL: scope violation detected" >&2
  exit 1
fi

echo "OK: all changes within scope: $ALLOWED_PREFIX"