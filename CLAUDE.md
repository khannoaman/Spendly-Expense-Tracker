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

- `app.py` — single FastAPI app instance; all routes are currently defined directly in this file (no routers yet). Templates are rendered via Jinja2 (`templates/`) using `templates.TemplateResponse(request, "name.html")`. Static assets are mounted at `/static` from the `static/` directory. A `lifespan` context manager calls `init_db()` then `seed_db()` on every app startup — both are idempotent, so this is safe on every dev-server reload.
- `database/db.py` — implemented. `get_db()` returns a SQLite connection (`row_factory = sqlite3.Row`, foreign keys pragma on). `init_db()` creates `users` and `expenses` tables (`CREATE TABLE IF NOT EXISTS`). `seed_db()` inserts one sample user + a few sample expenses only if `users` is empty. Schema: `users(id, name, email UNIQUE, password_hash, created_at)`; `expenses(id, user_id -> users.id ON DELETE CASCADE, amount, category TEXT, description, date TEXT ISO-8601, created_at)` — `category` is a free-text column, not a lookup table.
- Passwords are hashed with `passlib`'s `CryptContext(schemes=["bcrypt"])`. `requirements.txt` pins `bcrypt==4.0.1` deliberately — `passlib` 1.7.4 (last released 2020) is incompatible with `bcrypt` >=4.1 (it reads a `bcrypt.__about__.__version__` attribute that no longer exists), so do not bump the `bcrypt` pin without also confirming `passlib` still works, or switching hashing libraries.
- `templates/base.html` — shared layout (nav, footer, font/CSS includes) that all pages extend via Jinja `{% block %}`s (`title`, `head`, `content`, `scripts`). New pages should extend this base rather than duplicating the shell.
- `static/css/style.css` and `static/js/main.js` — single global stylesheet/script shared across all pages (no per-page bundling/build step — plain static files served as-is).
- SQLite is the database (`expense_tracker.db`, gitignored, created at runtime — not committed).

## Current implementation state

Routes in `app.py` fall into two groups:
1. Working GET pages that render templates: `/`, `/register`, `/login`, `/terms`, `/privacy`.
2. Placeholder routes returning plain strings, pending implementation: `POST /register`, `POST /login`, `/logout`, `/profile`, `/expenses/add`, `/expenses/{id}/edit`, `/expenses/{id}/delete`.

The database layer (`database/db.py`, schema, seeding, startup wiring) is implemented — see Architecture above. When implementing one of the remaining placeholder routes, wire it up to real logic (form handling, session/auth, SQLite persistence via `database/db.py`'s `get_db()`) rather than just changing the placeholder text.
