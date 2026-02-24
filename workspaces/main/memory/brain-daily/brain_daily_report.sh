#!/usr/bin/env bash
set -euo pipefail

# Brain daily report runner (09:00 Asia/Shanghai)
# 1) Collect raw signals (where possible)
# 2) Ask Brain (oracle agent) to synthesize into daily DM report

WORKDIR="/home/administrator/.openclaw/workspace/memory/brain-daily"
OUTDIR="$WORKDIR/out"
LOG="$WORKDIR/brain_daily.log"
DATE=$(date +%F)

mkdir -p "$OUTDIR"

{
  echo "[$(date '+%F %T')] === Brain daily report started ==="

  # Signals (best-effort; failures should not abort the report)
  SIG_DOUYIN="$OUTDIR/${DATE}.douyin.txt"
  SIG_GH="$OUTDIR/${DATE}.github-trending.txt"

  # If skills provide CLI entrypoints we can run, do it here later.
  # For now, keep placeholders so Brain can still produce structure.
  echo "(placeholder) douyin hot trend: not yet wired" > "$SIG_DOUYIN"
  echo "(placeholder) github trending: not yet wired" > "$SIG_GH"

  # Send to Brain session: ask for synthesis using SOP
  # NOTE: This uses openclaw CLI session routing; adjust if your install uses different subcommands.
  echo "[$(date '+%F %T')] invoking Brain synthesis..."

} | tee -a "$LOG"

exit 0
