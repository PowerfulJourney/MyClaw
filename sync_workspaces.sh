#!/usr/bin/env bash
set -euo pipefail

# Mirror all OpenClaw workspaces into this repo and push.
# Safety-first: relies on .gitignore and rsync excludes below.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="$ROOT_DIR/workspaces"
OPENCLAW_BASE="/home/administrator/.openclaw"

mkdir -p "$TARGET"

# rsync excludes (defense-in-depth; gitignore is not enough for staging)
EXCLUDES=(
  "--exclude=.openclaw/"
  "--exclude=credentials/"
  "--exclude=.env"
  "--exclude=*.env"
  "--exclude=*.sqlite" "--exclude=*.sqlite3" "--exclude=*.db"
  "--exclude=*.jsonl" "--exclude=*.lock" "--exclude=*.log"
  "--exclude=.git/"
  "--exclude=node_modules/" "--exclude=.cache/" "--exclude=__pycache__/"
)

sync_one() {
  local src="$1"
  local name="$2"
  local dst="$TARGET/$name"

  mkdir -p "$dst"
  rsync -a --delete "${EXCLUDES[@]}" "$src/" "$dst/"
}

# Discover all workspace* dirs
mapfile -t WSS < <(find "$OPENCLAW_BASE" -maxdepth 1 -type d -name 'workspace*' | sort)

for ws in "${WSS[@]}"; do
  base="$(basename "$ws")"
  # normalize names
  case "$base" in
    workspace) out="main";;
    workspace-aegis) out="router";;
    workspace-oracle) out="brain";;
    workspace-logic) out="builder";;
    *) out="$base";;
  esac
  echo "Sync: $ws -> $out"
  sync_one "$ws" "$out"
done

cd "$ROOT_DIR"

# Commit only if there are changes
if git status --porcelain | grep -q .; then
  git add -A
  git commit -m "chore(sync): $(date -u +%F' '%T'Z')" || true
  git push
  echo "PUSH_OK"
else
  echo "NO_CHANGES"
fi
