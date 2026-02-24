#!/usr/bin/env bash
set -euo pipefail

# Mirror OpenClaw workspaces into this repo and push to GitHub.
# Safe-by-default: uses a whitelist of directories + excludes sensitive/runtime files.

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Workspaces to sync: name:path
WORKSPACES=(
  "main:/home/administrator/.openclaw/workspace"
  "router:/home/administrator/.openclaw/workspace-aegis"
  "brain:/home/administrator/.openclaw/workspace-oracle"
  "builder:/home/administrator/.openclaw/workspace-logic"
  "reserve-growth:/home/administrator/.openclaw/workspace-growth"
  "reserve-metrics:/home/administrator/.openclaw/workspace-metrics"
)

DEST_ROOT="$REPO_DIR/workspaces"
mkdir -p "$DEST_ROOT"

# Whitelist: what we consider "production artifacts"
INCLUDE_DIRS=(
  "tasks"
  "reports"
  "protocols"
  "projects"
  "scripts"
  "skills"
  "assets"
  "templates"
)
INCLUDE_FILES=(
  "AGENTS.md"
  "SOUL.md"
  "IDENTITY.md"
  "USER.md"
  "MEMORY.md"
  "CONVENTION.md"
  "HEARTBEAT.md"
)

rsync_one() {
  local name="$1"
  local src="$2"
  local dest="$DEST_ROOT/$name"
  mkdir -p "$dest"

  # Sync included dirs if they exist
  for d in "${INCLUDE_DIRS[@]}"; do
    if [ -d "$src/$d" ]; then
      mkdir -p "$dest/$d"
      rsync -a --delete \
        --exclude='.git/' \
        --filter=':- .gitignore' \
        "$src/$d/" "$dest/$d/"
    fi
  done

  # Sync selected top-level files
  for f in "${INCLUDE_FILES[@]}"; do
    if [ -f "$src/$f" ]; then
      rsync -a "$src/$f" "$dest/$f"
    fi
  done
}

cd "$REPO_DIR"

for item in "${WORKSPACES[@]}"; do
  name="${item%%:*}"
  path="${item#*:}"
  if [ -d "$path" ]; then
    echo "[sync] $name <= $path"
    rsync_one "$name" "$path"
  else
    echo "[skip] missing $path"
  fi
done

# Commit & push
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: $REPO_DIR is not a git repo" >&2
  exit 2
fi

git add -A
if git diff --cached --quiet; then
  echo "[sync] no changes"
  exit 0
fi

msg="sync: $(date '+%F %T')"
git commit -m "$msg"

if [ "${DRY_RUN:-}" = "1" ]; then
  echo "[sync] DRY_RUN=1 set; skipping push"
  exit 0
fi

git push origin HEAD
