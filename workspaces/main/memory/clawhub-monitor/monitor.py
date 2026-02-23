#!/usr/bin/env python3
"""
ClawHub Skill Monitor
- Single-instance lock
- Exponential backoff + jitter retries
- 3-state daily report: success_with_new / success_no_new / fetch_failed
- Optional fallback source: fallback_skills.json
"""

import fcntl
import json
import random
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path

WORK_DIR = Path("/home/administrator/.openclaw/workspace/memory/clawhub-monitor")
STATE_FILE = WORK_DIR / "known_skills.json"
REPORT_FILE = WORK_DIR / "daily_report.md"
LOG_FILE = WORK_DIR / "monitor.log"
LOCK_FILE = WORK_DIR / "monitor.lock"
FALLBACK_FILE = WORK_DIR / "fallback_skills.json"

RETRY_TIMEOUTS = [60, 120, 240]
EXPLORE_LIMIT = 80


def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {msg}"
    print(log_line)
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line + "\n")


def warmup_npx():
    """Best-effort warmup to reduce npx first-call latency."""
    try:
        subprocess.run(
            ["npx", "clawhub", "--help"],
            capture_output=True,
            text=True,
            timeout=20,
            cwd=str(WORK_DIR),
        )
        log("npx warmup completed")
    except Exception as e:
        log(f"npx warmup skipped: {e}")


def fetch_skills_primary():
    """Fetch skills from clawhub explore with retries."""
    log("Fetching skills from clawhub explore...")
    warmup_npx()

    for attempt, timeout_seconds in enumerate(RETRY_TIMEOUTS, start=1):
        log(f"Attempt {attempt}/{len(RETRY_TIMEOUTS)} with {timeout_seconds}s timeout...")
        try:
            result = subprocess.run(
                ["npx", "clawhub", "explore", "--limit", str(EXPLORE_LIMIT)],
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=str(WORK_DIR),
            )

            if result.returncode == 0 and result.stdout.strip():
                log("Successfully fetched skills from primary source")
                return result.stdout, "primary", None

            err = (result.stderr or result.stdout or "unknown error").strip()[:260]
            log(f"clawhub error (attempt {attempt}): {err}")
        except subprocess.TimeoutExpired:
            log(f"Timeout on attempt {attempt}")
        except Exception as e:
            log(f"Error on attempt {attempt}: {e}")

        if attempt < len(RETRY_TIMEOUTS):
            sleep_s = round((2 ** (attempt - 1)) * random.uniform(0.6, 1.4), 2)
            log(f"Backoff sleeping {sleep_s}s before retry")
            time.sleep(sleep_s)

    return None, "primary", "all primary retries failed"


def fetch_skills_fallback():
    """Optional fallback from local json file."""
    if not FALLBACK_FILE.exists():
        return None, "fallback", "fallback file not found"
    try:
        data = json.loads(FALLBACK_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            log(f"Loaded fallback skills: {len(data)} records")
            if not data:
                return None, "fallback", "fallback file is empty"
            return data, "fallback", None
        return None, "fallback", "fallback json must be a list"
    except Exception as e:
        return None, "fallback", f"fallback parse error: {e}"


def _extract_downloads(line: str) -> int:
    # Try patterns like "12,345 downloads"
    m = re.search(r"([\d,]+)\s*downloads?", line, re.IGNORECASE)
    if m:
        return int(m.group(1).replace(",", ""))

    # Fallback: choose the largest standalone integer in line
    nums = re.findall(r"\b\d[\d,]*\b", line)
    if not nums:
        return 0
    values = [int(n.replace(",", "")) for n in nums]
    return max(values) if values else 0


def parse_explore_output(output):
    """Parse clawhub explore text output."""
    skills = []
    if not output:
        return skills

    lines = output.strip().split("\n")
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if s.startswith("-") or s.lower().startswith("name") or "fetching latest" in s.lower():
            continue

        parts = s.split()
        if len(parts) < 2:
            continue

        name = parts[0] if not parts[0].replace(".", "").isdigit() else parts[1]
        skills.append(
            {
                "name": name,
                "downloads": _extract_downloads(s),
                "raw": s,
                "discovered_at": datetime.now().isoformat(),
            }
        )
    return skills


def normalize_fallback_list(items):
    out = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        out.append(
            {
                "name": name,
                "downloads": int(item.get("downloads", 0) or 0),
                "raw": item.get("raw", f"{name} | downloads={item.get('downloads', 0)}"),
                "discovered_at": datetime.now().isoformat(),
            }
        )
    return out


def load_known_skills():
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        log(f"Warning: Could not load state: {e}")
        return {}


def save_known_skills(skills_dict):
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(skills_dict, indent=2, ensure_ascii=False), encoding="utf-8")


def find_new_skills(current_skills, known_skills):
    return [s for s in current_skills if s.get("name") and s["name"] not in known_skills]


def generate_report(new_skills, status="fetch_failed", source="primary", reason=""):
    """status: success_with_new | success_no_new | fetch_failed"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today = datetime.now().strftime("%Y-%m-%d")
    report_lines = [
        f"# 📦 ClawHub Skill Monitor Report - {today}",
        "",
        f"⏰ Generated: {now}",
        "🌏 Timezone: Asia/Shanghai",
        f"📡 Source: {source}",
        f"🏷️ State: {status}",
        "",
    ]

    if status == "fetch_failed":
        report_lines.extend(
            [
                "## ⚠️ Status: Fetch Failed",
                "",
                "本次未能拿到可用的 skill 列表（这不等同于‘今日无新增’）。",
                "",
                "**Possible reasons:**",
                "- Network connectivity issues",
                "- ClawHub service temporarily unavailable",
                "- API response timeout (service may be slow)",
                "",
                f"**Reason:** `{reason or 'unknown'}`",
                "",
                "**Recommendation:**",
                "- Retry in low-traffic window (07:00-09:00)",
                "- Keep fallback_skills.json ready as backup source",
            ]
        )
    elif status == "success_no_new":
        report_lines.extend(
            [
                "## 📝 Status: No New Skills",
                "",
                "抓取成功，但当日未发现新增技能。",
            ]
        )
    else:
        report_lines.extend(
            [
                "## 🆕 New Skills Discovered",
                "",
                f"Found **{len(new_skills)}** new skill(s) today:",
                "",
            ]
        )
        top = sorted(new_skills, key=lambda x: x.get("downloads", 0), reverse=True)[:5]
        for i, skill in enumerate(top, 1):
            report_lines.append(
                f"{i}. **{skill.get('name', 'Unknown')}** (downloads: {skill.get('downloads', 0)})"
            )
            report_lines.append(f"   - Info: `{skill.get('raw', '')}`")
            report_lines.append("")

    report_lines.extend(
        [
            "---",
            "",
            "📊 Monitor Configuration:",
            "- Check frequency: Daily at 8:00 AM",
            "- Max skills per report: 5",
            "- Retry strategy: exponential backoff + jitter",
            "- Single-instance lock: enabled",
            "- Tracked skills file: `known_skills.json`",
            "",
            "_This is an automated report from ClawHub Skill Monitor_",
        ]
    )

    return "\n".join(report_lines)


def main():
    WORK_DIR.mkdir(parents=True, exist_ok=True)

    with open(LOCK_FILE, "w", encoding="utf-8") as lockf:
        try:
            fcntl.flock(lockf, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            log("Another monitor process is running. Skip this run.")
            return 0

        log("=== ClawHub Monitor Started ===")

        output, source, err = fetch_skills_primary()
        parsed = []

        if output:
            parsed = parse_explore_output(output)
        else:
            fallback_data, fb_source, fb_err = fetch_skills_fallback()
            if fallback_data:
                source = fb_source
                parsed = normalize_fallback_list(fallback_data)
                err = "primary failed, fallback used"
            else:
                source = f"primary+{fb_source}"
                err = f"{err}; {fb_err}"

        if not parsed:
            report = generate_report([], status="fetch_failed", source=source, reason=err)
            REPORT_FILE.write_text(report, encoding="utf-8")
            log("Report generated with failure notice")
            log("=== Monitor Completed ===")
            return 1

        log(f"Parsed {len(parsed)} skills from source={source}")
        known_skills = load_known_skills()
        log(f"Loaded {len(known_skills)} known skills from state")

        new_skills = find_new_skills(parsed, known_skills)
        log(f"Found {len(new_skills)} new skills")

        for skill in parsed:
            name = skill.get("name")
            if name:
                known_skills[name] = skill

        save_known_skills(known_skills)
        log(f"Updated state with {len(known_skills)} total skills")

        state = "success_with_new" if new_skills else "success_no_new"
        report = generate_report(new_skills, status=state, source=source)
        REPORT_FILE.write_text(report, encoding="utf-8")

        log(f"Report saved to: {REPORT_FILE}")
        log("=== Monitor Completed ===")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
