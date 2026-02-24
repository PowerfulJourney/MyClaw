#!/usr/bin/env python3
"""ClawHub Skill Monitor

- Single-instance lock
- Exponential backoff + jitter retries
- 3-state daily report: success_with_new / success_no_new / fetch_failed
- Optional fallback source: fallback_skills.json

Report format is optimized for Telegram scanning.
"""

import fcntl
import json
import random
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

WORK_DIR = Path("/home/administrator/.openclaw/workspace/memory/clawhub-monitor")
STATE_FILE = WORK_DIR / "known_skills.json"
REPORT_FILE = WORK_DIR / "daily_report.md"
LOG_FILE = WORK_DIR / "monitor.log"
LOCK_FILE = WORK_DIR / "monitor.lock"
FALLBACK_FILE = WORK_DIR / "fallback_skills.json"

RETRY_TIMEOUTS = [60, 120, 240]
EXPLORE_LIMIT = 80

# Enrichment: keep small to reduce rate-limit risk
ENRICH_TOP_N = 5
INSPECT_TIMEOUT_S = 40
INSPECT_SLEEP_S = 1.1


def log(msg: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {msg}"
    print(log_line)
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line + "\n")


def warmup_npx() -> None:
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


def fetch_skills_primary() -> Tuple[Optional[str], str, Optional[str]]:
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


def fetch_skills_fallback() -> Tuple[Optional[list], str, Optional[str]]:
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
    """Best-effort extraction of downloads count from a single explore line.

    ClawHub CLI output can change; be permissive and never throw.
    """

    # Prefer patterns like "12,345 downloads" (require at least one digit)
    m = re.search(r"(\d[\d,]*)\s*downloads?", line, re.IGNORECASE)
    if m:
        raw = (m.group(1) or "").replace(",", "").strip()
        if raw.isdigit():
            return int(raw)

    # Handle compact suffixes like 1.2k / 3M downloads
    m2 = re.search(r"(\d+(?:\.\d+)?)\s*([kKmM])\s*downloads?", line)
    if m2:
        try:
            base = float(m2.group(1))
            mult = 1000 if m2.group(2).lower() == "k" else 1_000_000
            return int(base * mult)
        except Exception:
            return 0

    # Fallback: choose the largest standalone integer in line
    nums = re.findall(r"\b\d[\d,]*\b", line)
    if not nums:
        return 0
    try:
        values = [int(n.replace(",", "")) for n in nums]
        return max(values) if values else 0
    except Exception:
        return 0


def parse_explore_output(output: str) -> List[Dict[str, Any]]:
    """Parse clawhub explore text output."""
    skills: List[Dict[str, Any]] = []
    if not output:
        return skills

    lines = output.strip().split("\n")
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if s.startswith("-") or s.lower().startswith("name") or "fetching latest" in s.lower():
            continue
        if "rate limit" in s.lower():
            # ignore the banner line; caller will handle empty parse
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


def normalize_fallback_list(items: list) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
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


def load_known_skills() -> Dict[str, Any]:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        log(f"Warning: Could not load state: {e}")
        return {}


def save_known_skills(skills_dict: Dict[str, Any]) -> None:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(skills_dict, indent=2, ensure_ascii=False), encoding="utf-8")


def save_fallback_snapshot(parsed: List[Dict[str, Any]]) -> None:
    """Write a best-effort fallback snapshot whenever we have a good parse."""
    try:
        FALLBACK_FILE.write_text(json.dumps(parsed, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        log(f"Warning: Could not write fallback snapshot: {e}")


def find_new_skills(current_skills: List[Dict[str, Any]], known_skills: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [s for s in current_skills if s.get("name") and s["name"] not in known_skills]


def _strip_cli_prefix_lines(text: str) -> str:
    lines = []
    for ln in (text or "").splitlines():
        if ln.strip().startswith("- Fetching"):
            continue
        if ln.strip().startswith("- Downloading"):
            continue
        lines.append(ln)
    return "\n".join(lines).strip()


def clawhub_inspect_json(slug: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Return (json, error)."""
    try:
        p = subprocess.run(
            ["npx", "clawhub", "inspect", slug, "--json"],
            capture_output=True,
            text=True,
            timeout=INSPECT_TIMEOUT_S,
            cwd=str(WORK_DIR),
        )
        out = _strip_cli_prefix_lines(p.stdout)
        if p.returncode != 0:
            return None, (p.stderr or p.stdout or "inspect failed").strip()[:260]
        return json.loads(out), None
    except subprocess.TimeoutExpired:
        return None, "inspect timeout"
    except Exception as e:
        return None, f"inspect error: {e}"


def clawhub_inspect_file(slug: str, path: str) -> Tuple[Optional[str], Optional[str]]:
    """Fetch a text file from the skill (<=200KB)."""
    try:
        p = subprocess.run(
            ["npx", "clawhub", "inspect", slug, "--file", path],
            capture_output=True,
            text=True,
            timeout=INSPECT_TIMEOUT_S,
            cwd=str(WORK_DIR),
        )
        out = _strip_cli_prefix_lines(p.stdout)
        if p.returncode != 0:
            return None, (p.stderr or p.stdout or "inspect file failed").strip()[:260]
        return out, None
    except subprocess.TimeoutExpired:
        return None, "inspect file timeout"
    except Exception as e:
        return None, f"inspect file error: {e}"


def _parse_tags_from_skill_md(skill_md: str) -> List[str]:
    """Extract tags from SKILL.md YAML front matter (best-effort)."""
    if not skill_md:
        return []

    # Front matter
    m = re.match(r"\s*---\n(.*?)\n---\n", skill_md, re.S)
    if not m:
        return []
    fm = m.group(1)

    # tags: [a, b]
    m1 = re.search(r"^tags:\s*\[(.*?)\]\s*$", fm, re.M)
    if m1:
        raw = m1.group(1)
        tags = [t.strip().strip("'\"") for t in raw.split(",") if t.strip()]
        return [t for t in tags if t]

    # tags:\n  - a\n  - b
    m2 = re.search(r"^tags:\s*\n((?:\s*-\s*.+\n)+)", fm, re.M)
    if m2:
        block = m2.group(1)
        tags = []
        for ln in block.splitlines():
            ln = ln.strip()
            if ln.startswith("-"):
                tags.append(ln[1:].strip().strip("'\""))
        return [t for t in tags if t]

    return []


def _extract_env_vars(skill_md: str) -> List[str]:
    """Extract ENV var names like FOO_BAR from SKILL.md (best-effort)."""
    if not skill_md:
        return []
    envs = set(re.findall(r"\b[A-Z][A-Z0-9_]{2,}\b", skill_md))
    # Filter obvious non-env tokens
    blacklist = {
        "HTTP",
        "HTTPS",
        "JSON",
        "MIT",
        "API",
        "URL",
        "CLI",
        "MCP",
        "USDC",
        "EVM",
        "SOL",
        "ETH",
        "BTC",
        "README",
        "SKILL",
    }
    envs = {e for e in envs if e not in blacklist and not e.endswith(".MD")}
    # keep most likely ones
    return sorted(envs)


def _guess_type_tags(slug: str, summary: str, tags_from_md: List[str]) -> List[str]:
    s = (summary or "").lower()
    slug_l = (slug or "").lower()

    tags = [t.lower() for t in tags_from_md if t]

    def add(t: str):
        if t not in tags:
            tags.append(t)

    if "ecommerce" in slug_l or "e-commerce" in s or "taobao" in s or "jd" in s or "pdd" in s:
        add("ecommerce")
        add("product-research")
        add("china")

    if "polymarket" in slug_l or "trade" in s or "trading" in s or "markets" in s:
        add("trading")
        if "polymarket" in slug_l:
            add("polymarket")

    if "sports" in slug_l or "sports" in s:
        add("sports")

    if "devnet" in s or "solana devnet" in s:
        add("devnet")

    if "self-evolution" in s or "self-improvement" in s or "meta-skill" in s or "evolution" in s:
        add("meta")
        add("ops")

    if "pay" in s or "paid" in s or "usdc" in s and "pay" in s:
        add("paid")

    # Keep 2-4 stable tags
    return tags[:4]


def _suggest_opportunities(slug: str, summary: str, tags: List[str]) -> List[str]:
    s = (summary or "").lower()
    t = set(tags or [])
    out: List[str] = []

    def push(x: str):
        if x and x not in out:
            out.append(x)

    if "ecommerce" in t:
        push("把选品/竞品/价格带对比自动化，提升 Brain 的机会报告含金量")
        push("做“比价/找同款/找供应链(1688)”的小工具或报告服务，形成变现路径")
        push("结合 XHS/抖音做内容选题+商品素材库沉淀，形成可复用增长资产")

    if "meta" in t:
        push("用于日常故障复盘：从日志/历史中产出修复建议与补丁草案（建议 review 模式）")
        push("把重复修复经验沉淀为可复用规则/模板，降低维护成本")
        push("为监控/脚本建立“人类在环”的安全改进流水线")

    if "trading" in t:
        push("作为“信号→下单→仓位/费用处理”的交易模板，加速策略原型验证")
        push("可替换信号源（自有数据/舆情/新闻）做差异化策略服务")
        push("沉淀风控模板（限额/确认/白名单），复用到其它高风险自动化工具")

    if "paid" in t and "trading" not in t:
        push("抽象“付费 API 调用”安全模板：二次确认、预算上限、禁止自动分页")
        push("做垂直数据检索/核验服务（按次计费），为研究报告增加可核验引用")
        push("将成本估算（preview→付费）流程产品化，减少误触发支出")

    if "sports" in t and "trading" in t:
        push("用于演示/课程素材：devnet 场景下展示 agent 自主执行闭环")
        push("如果做 agent 竞赛/排行榜玩法，可快速搭脚手架")
        push("抽象密钥落盘+本地签名范式，为其它链上工具提供安全参考")

    # Ensure 3 lines
    while len(out) < 3:
        push("观察是否能并入现有工作流：节省人工步骤、提升信息密度或减少出错")

    return out[:3]


def _build_dependency_line(skill_md: str, summary: str) -> str:
    envs = _extract_env_vars(skill_md)
    parts = []
    if envs:
        # keep up to 4 envs to avoid long lines
        parts.append("ENV: " + ", ".join(envs[:4]) + ("..." if len(envs) > 4 else ""))

    s = (summary or "").lower()
    stack = []
    if "python" in skill_md.lower() or "pip install" in skill_md.lower():
        stack.append("python")
    if "node" in skill_md.lower() or "npm" in skill_md.lower() or "npx" in skill_md.lower():
        stack.append("node")
    if "mcp" in skill_md.lower() or "mcp" in s:
        stack.append("mcp")
    if "solana" in skill_md.lower() or "solana" in s:
        stack.append("solana")
    if "evm" in skill_md.lower() or "base" in skill_md.lower() or "x402" in skill_md.lower():
        stack.append("evm/x402")

    if stack:
        parts.append("Stack: " + "+".join(dict.fromkeys(stack)))

    if "no api key" in skill_md.lower() or "no api keys" in skill_md.lower() or "no api keys" in s:
        parts.append("无需 API key")

    # Fallback to summary hints
    if not parts:
        return "无（以 SKILL.md 为准）"

    return "；".join(parts)


def _truncate_cn(text: str, max_len: int = 200) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


def enrich_skill_for_report(slug: str) -> Dict[str, Any]:
    """Fetch inspect + SKILL.md for a slug and return report-friendly fields."""
    data, err = clawhub_inspect_json(slug)
    if err or not data:
        return {
            "slug": slug,
            "link": "",
            "display": slug,
            "summary": f"（inspect 失败：{err}）",
            "type_tags": [],
            "opportunities": ["（暂无）", "（暂无）", "（暂无）"],
            "deps": "（暂无）",
            "owner": "",
            "downloads": 0,
            "stars": 0,
            "error": err,
        }

    skill = data.get("skill") or {}
    owner = (data.get("owner") or {}).get("handle") or ""
    slug = skill.get("slug") or slug

    display = skill.get("displayName") or slug
    summary = skill.get("summary") or ""

    stats = skill.get("stats") or {}
    downloads = int(stats.get("downloads") or 0)
    stars = int(stats.get("stars") or 0)

    link = f"https://clawhub.ai/{owner}/{slug}" if owner else ""

    skill_md, md_err = clawhub_inspect_file(slug, "SKILL.md")
    if md_err:
        skill_md = ""

    tags_from_md = _parse_tags_from_skill_md(skill_md or "")
    type_tags = _guess_type_tags(slug, summary, tags_from_md)

    opportunities = _suggest_opportunities(slug, summary, type_tags)
    deps = _build_dependency_line(skill_md or "", summary)

    return {
        "slug": slug,
        "link": link,
        "display": display,
        "summary": _truncate_cn(summary, 200),
        "type_tags": type_tags,
        "opportunities": opportunities,
        "deps": deps,
        "owner": owner,
        "downloads": downloads,
        "stars": stars,
    }


def generate_report(new_skills: List[Dict[str, Any]], status: str = "fetch_failed", source: str = "primary", reason: str = "") -> str:
    """status: success_with_new | success_no_new | fetch_failed"""

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today = datetime.now().strftime("%Y-%m-%d")

    report_lines = [
        f"# 📦 ClawHub 日报（Top5）- {today}",
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
                "## ⚠️ 抓取失败",
                "",
                "本次未能拿到可用的 skill 列表（这不等同于‘今日无新增’）。",
                "",
                f"**Reason:** `{reason or 'unknown'}`",
                "",
                "建议：",
                "- 稍后重试（避开高峰）",
                "- 观察是否触发 Rate limit",
                "- 保持 fallback_skills.json 有上次成功快照",
            ]
        )

    elif status == "success_no_new":
        report_lines.extend(
            [
                "## 📝 今日无新增",
                "",
                "抓取成功，但当日未发现新增技能。",
            ]
        )

    else:
        report_lines.extend(
            [
                "## 🆕 今日新增（Top5）",
                "",
                f"Found **{len(new_skills)}** new skill(s) today.",
                "",
            ]
        )

        top = sorted(new_skills, key=lambda x: x.get("downloads", 0), reverse=True)[:ENRICH_TOP_N]
        for i, skill in enumerate(top, 1):
            slug = skill.get("name") or ""
            enriched = enrich_skill_for_report(slug)

            type_tags = enriched.get("type_tags") or []
            type_str = "，".join([f"‘{t}’" for t in type_tags]) if type_tags else "‘uncategorized’"

            # Final one-line style (Telegram-friendly; avoids quote continuation issues)
            tags = enriched.get("type_tags") or []
            tag_str = "，".join([f"‘{t}’" for t in tags]) if tags else "‘uncategorized’"
            opp = enriched.get("opportunities", ["", "", ""])[:3]
            line = (
                f"{i}️⃣ [{enriched.get('display','')}]({enriched.get('link','')}) "
                f"**简介:** {enriched.get('summary','')} "
                f"**类型:** {tag_str} "
                f"**机会点:** - {opp[0]} - {opp[1]} - {opp[2]} "
                f"**依赖:** {enriched.get('deps','')} "
                f"owner: {enriched.get('owner','')} | downloads: {enriched.get('downloads',0)} | stars: {enriched.get('stars',0)}"
            )
            report_lines.append(line)

            time.sleep(INSPECT_SLEEP_S)

    report_lines.extend(
        [
            "---",
            "",
            "📊 Monitor Configuration:",
            "- Check frequency: Daily at 8:00 AM",
            f"- Explore limit: {EXPLORE_LIMIT}",
            f"- Enrich top N: {ENRICH_TOP_N}",
            "- Retry strategy: exponential backoff + jitter",
            "- Single-instance lock: enabled",
            "- Tracked skills file: `known_skills.json`",
            "",
            "_This is an automated report from ClawHub Skill Monitor_",
        ]
    )

    return "\n".join(report_lines)


def main() -> int:
    WORK_DIR.mkdir(parents=True, exist_ok=True)

    with open(LOCK_FILE, "w", encoding="utf-8") as lockf:
        try:
            fcntl.flock(lockf, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            log("Another monitor process is running. Skip this run.")
            return 0

        log("=== ClawHub Monitor Started ===")

        output, source, err = fetch_skills_primary()
        parsed: List[Dict[str, Any]] = []

        if output:
            parsed = parse_explore_output(output)
            if parsed:
                save_fallback_snapshot(parsed)
                log("Fallback snapshot updated")
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
        report = generate_report(new_skills, status=state, source=source, reason=err or "")
        REPORT_FILE.write_text(report, encoding="utf-8")

        log(f"Report saved to: {REPORT_FILE}")
        log("=== Monitor Completed ===")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
