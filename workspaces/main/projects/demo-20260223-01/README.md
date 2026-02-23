# DEMO-20260223-01

Minimal dependency-free todo web demo (`index.html`, `styles.css`, `app.js`).

## Start

```bash
python3 -m http.server 8000
```

## Access

Open: `http://localhost:8000`

## 3-Step Demo Path

1. Add a task using the input and **Add** button.
2. Mark it complete using **Done** (toggle back with **Undo**), and add/delete as needed.
3. Refresh the page to verify localStorage persistence.

## Rollback / Fallback Notes

- Port in use: run `lsof -i :8000` to inspect, stop conflicting process, then retry.
- No python fallback: use another available static server only if `python3` is unavailable.
