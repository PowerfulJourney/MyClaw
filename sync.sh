#!/usr/bin/env bash
set -euo pipefail

# Mirror OpenClaw workspaces into this repo and push to GitHub.
# Safe-by-default: uses a whitelist of directories + excludes sensitive/runtime files.

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Workspaces to sync: name:path
WORKSPACES=(
  "main:/home/administrator/.openclaw/workspace"
  "router:/home/administrator/.openclaw/workspace-aegis"
  "brain:/home/administrator/.openclaw/workspace-brain"
  "builder:/home/administrator/.openclaw/workspace-builder"
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

# GitHub SSH 22 is blocked in some networks/WSL setups. Use ssh.github.com:443.
SSH_KEY="/home/administrator/.openclaw/credentials/ssh_myclaw"
export GIT_SSH_COMMAND="ssh -i $SSH_KEY -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new -p 443"

# Ensure remote uses port 443 endpoint.
git remote set-url origin "ssh://git@ssh.github.com:443/PowerfulJourney/MyClaw.git"

git add -A

# If nothing changed, we may still be ahead (previous run committed but push failed).
if git diff --cached --quiet; then
  if [ "${DRY_RUN:-}" = "1" ]; then
    echo "[sync] no changes (DRY_RUN=1; skipping push)"
    exit 0
  fi

  # Push if branch is ahead of upstream.
  ahead_count="0"
  if git rev-parse --abbrev-ref --symbolic-full-name @{u} >/dev/null 2>&1; then
    ahead_count="$(git rev-list --count @{u}..HEAD 2>/dev/null || echo 0)"
  fi

  if [ "${ahead_count}" != "0" ]; then
    echo "[sync] no file changes, but branch ahead (${ahead_count}); pushing"
    git pull --rebase --autostash origin master
    git push origin HEAD
  else
    echo "[sync] no changes"
  fi
  exit 0
fi

msg="sync: $(date '+%F %T')"
git commit -m "$msg"

if [ "${DRY_RUN:-}" = "1" ]; then
  echo "[sync] DRY_RUN=1 set; skipping push"
  exit 0
fi

git pull --rebase --autostash origin master
git push origin HEAD
