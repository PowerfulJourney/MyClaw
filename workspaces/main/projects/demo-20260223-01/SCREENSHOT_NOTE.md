# Screenshot Note

Environment limitation encountered during automated capture:
- OpenClaw browser control unavailable (no supported local browser binary: Chrome/Chromium/Edge/Brave).

## Manual screenshot steps (fast)
1. `cd /home/administrator/.openclaw/workspace/projects/demo-20260223-01`
2. `python3 -m http.server 8000`
3. Open `http://localhost:8000`
4. Add a task and click Done
5. Capture one screenshot of the page (any OS screenshot tool)

## Temporary substitute evidence
- `curl http://127.0.0.1:8000` returns full HTML successfully.
