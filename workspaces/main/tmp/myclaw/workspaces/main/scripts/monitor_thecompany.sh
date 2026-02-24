#!/usr/bin/env bash
set -euo pipefail

# Monitor OpenClaw gateway logs for Telegram group health issues.
# Keeps state in workspace so we only scan new log content.

STATE_FILE="/home/administrator/.openclaw/workspace/memory/group-health-state.json"
GROUP_ID_DEFAULT="-1003883808495"  # detected from logs; override with GROUP_ID env
GROUP_ID="${GROUP_ID:-$GROUP_ID_DEFAULT}"

LOG_DATE="$(date +%F)"
LOG_FILE="/tmp/openclaw/openclaw-${LOG_DATE}.log"

if [[ ! -f "$LOG_FILE" ]]; then
  echo "WARN: log file not found: $LOG_FILE"
  exit 0
fi

mkdir -p "$(dirname "$STATE_FILE")"

LAST_BYTE=0
if [[ -f "$STATE_FILE" ]]; then
  # Very small JSON: {"lastByte":123,"lastFile":"..."}
  LAST_BYTE=$(node -e "const fs=require('fs');try{const s=JSON.parse(fs.readFileSync(process.argv[1],'utf8'));console.log(s.lastFile===process.argv[2]?String(s.lastByte||0):'0')}catch(e){console.log('0')}" "$STATE_FILE" "$LOG_FILE")
fi

SIZE=$(wc -c <"$LOG_FILE" | tr -d ' ')
if [[ "$SIZE" -lt "$LAST_BYTE" ]]; then
  # rotated/truncated
  LAST_BYTE=0
fi

# Read new chunk (cap to last ~2MB to avoid huge processing)
MAX_READ=$((2*1024*1024))
START=$LAST_BYTE
if [[ $((SIZE-START)) -gt $MAX_READ ]]; then
  START=$((SIZE-MAX_READ))
fi

CHUNK=$(tail -c +$((START+1)) "$LOG_FILE" || true)

# Update state to end of file
node -e "const fs=require('fs');fs.writeFileSync(process.argv[1],JSON.stringify({lastByte:Number(process.argv[2]),lastFile:process.argv[3],updatedAt:new Date().toISOString()},null,2));" "$STATE_FILE" "$SIZE" "$LOG_FILE" >/dev/null

# Patterns that indicate problems (focus on reliability + routing + pairing + visibility)
PATTERN='pairing required|Session send visibility is restricted|skipping group message|closed before connect|gateway connect failed|HttpError: Network request|Failed to start|rate limit|429|timeout|ECONN|EAI_AGAIN'

# Filter only lines likely relevant to Telegram/group; keep generic fallback
MATCHES=$(printf "%s" "$CHUNK" | grep -Ei "$PATTERN" || true)

if [[ -z "$MATCHES" ]]; then
  exit 0
fi

# Prefer lines that include the group id, if present
GROUP_MATCHES=$(printf "%s" "$MATCHES" | grep -F -- "$GROUP_ID" || true)

echo "【群健康巡检告警】"
echo "groupId: $GROUP_ID"
echo "log: $LOG_FILE"
echo "---"
if [[ -n "$GROUP_MATCHES" ]]; then
  echo "$GROUP_MATCHES" | tail -n 30
else
  echo "$MATCHES" | tail -n 30
fi

echo "---"
echo "临时规避建议："
echo "- 若是 pairing required：检查 openclaw devices list 是否有 pending（需要 approve）；以及对应 bot/账号的 DM 是否完成 pairing。"
echo "- 若是 visibility is restricted：确认 Aegis 的 tools.sessions.visibility=all 且 tools.agentToAgent.enabled=true。"
echo "- 若是 skipping group message：确认群组 allowlist/groupPolicy/requireMention 配置与提及规则。"