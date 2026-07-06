# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

"Spendly" — a FastAPI-based expense tracker built incrementally as a learning project. The codebase is intentionally scaffolded in stages: many routes and modules exist as placeholders with comments like `# Students will write this file in Step N` or return strings like `"Login POST — coming in Step 3"`. When asked to implement a feature, check whether it corresponds to one of these placeholder steps and follow the existing route/module layout rather than restructuring.

## Commands

```bash
# Setup (venv/ is gitignored, already present locally)
pip install -r requirements.txt

# Run the dev server (reload enabled)
python app.py
# serves on http://127.0.0.1:5001

# Alternative run
uvicorn app:app --reload --port 5001

# Tests
pytest
```

There is no lint/format tooling configured yet.

## Architecture

- `app.py` — single FastAPI app instance; all routes are currently defined directly in this file (no routers yet). Templates are rendered via Jinja2 (`templates/`) using `templates.TemplateResponse(request, "name.html")`. Static assets are mounted at `/static` from the `static/` directory.
- `database/db.py` — intended to hold `get_db()` (SQLite connection with `row_factory` and foreign keys enabled), `init_db()` (creates tables with `CREATE TABLE IF NOT EXISTS`), and `seed_db()` (sample dev data). Not yet implemented — this is an early step in the build sequence.
- `templates/base.html` — shared layout (nav, footer, font/CSS includes) that all pages extend via Jinja `{% block %}`s (`title`, `head`, `content`, `scripts`). New pages should extend this base rather than duplicating the shell.
- `static/css/style.css` and `static/js/main.js` — single global stylesheet/script shared across all pages (no per-page bundling/build step — plain static files served as-is).
- SQLite is the target database (`expense_tracker.db`, gitignored, created at runtime — not committed).

## Current implementation state

Routes in `app.py` fall into two groups:
1. Working GET pages that render templates: `/`, `/register`, `/login`, `/terms`, `/privacy`.
2. Placeholder routes returning plain strings, pending implementation: `POST /register`, `POST /login`, `/logout`, `/profile`, `/expenses/add`, `/expenses/{id}/edit`, `/expenses/{id}/delete`. `database/db.py` is also unimplemented.

When implementing one of these, wire it up to real logic (form handling, session/auth, SQLite persistence via `database/db.py`) rather than just changing the placeholder text.
