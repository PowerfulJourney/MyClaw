# 📦 ClawHub Skill Monitor Report - 2026-02-23

⏰ Generated: 2026-02-23 08:07:50
🌏 Timezone: Asia/Shanghai
📡 Source: primary+fallback
🏷️ State: fetch_failed

## ⚠️ Status: Fetch Failed

本次未能拿到可用的 skill 列表（这不等同于‘今日无新增’）。

**Possible reasons:**
- Network connectivity issues
- ClawHub service temporarily unavailable
- API response timeout (service may be slow)

**Reason:** `all primary retries failed; fallback file is empty`

**Recommendation:**
- Retry in low-traffic window (07:00-09:00)
- Keep fallback_skills.json ready as backup source
---

📊 Monitor Configuration:
- Check frequency: Daily at 8:00 AM
- Max skills per report: 5
- Retry strategy: exponential backoff + jitter
- Single-instance lock: enabled
- Tracked skills file: `known_skills.json`

_This is an automated report from ClawHub Skill Monitor_