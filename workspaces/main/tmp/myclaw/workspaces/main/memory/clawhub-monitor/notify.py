#!/usr/bin/env python3
"""
Send ClawHub Monitor Report to Telegram
Usage: python3 notify.py [report_file]
"""

import sys
from pathlib import Path

REPORT_FILE = Path("/home/administrator/.openclaw/workspace/memory/clawhub-monitor/daily_report.md")

def main():
    report_path = Path(sys.argv[1]) if len(sys.argv) > 1 else REPORT_FILE
    
    if not report_path.exists():
        print(f"Report not found: {report_path}")
        sys.exit(1)
    
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Print report content for the calling process to handle
    print(content)

if __name__ == "__main__":
    main()
