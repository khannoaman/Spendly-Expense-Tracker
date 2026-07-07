# Spendly

A small expense tracker built with FastAPI. This project exists mainly as a way to **learn FastAPI** by building something real end-to-end — server-rendered HTML, forms, auth, and a database — rather than to ship a polished product.

## Why this project

The goal was to get hands-on with FastAPI's core building blocks by using each of them for a genuine reason, not a toy example:

- **Routing & request handling** — `GET`/`POST` routes, path params (`/expenses/{id}/edit`), form data via `Form(...)`.
- **Dependency injection** — `Depends(get_current_user)` guards every authenticated route instead of repeating auth checks.
- **Pydantic validation** — request data (registration, login, expense forms) is validated through `BaseModel` + `field_validator`, with errors surfaced back into the HTML forms.
- **Server-rendered templates** — Jinja2 (`Jinja2Templates`) with a shared `base.html` layout and `{% block %}` inheritance, no frontend framework.
- **Sessions & middleware** — `SessionMiddleware` (`starlette`) for login state, signed with a secret key.
- **Lifespan events** — `@asynccontextmanager` lifespan hook to initialize and seed the SQLite database on startup.
- **Static files** — `StaticFiles` mounted for CSS/JS.
- **Working directly with SQLite** — no ORM; raw `sqlite3` with `row_factory = sqlite3.Row`, to see what an ORM would otherwise abstract away.

## Features

- User registration and login (bcrypt-hashed passwords via `passlib`)
- Session-based authentication with logout
- Profile dashboard: total spent, transaction count, top category, category breakdown
- Full expense CRUD: add, edit, and delete expenses, scoped so a user can only touch their own data
- Server-side validation with inline error messages on all forms

## Tech stack

| Layer      | Choice                          |
|------------|----------------------------------|
| Framework  | FastAPI                          |
| Templates  | Jinja2                           |
| Database   | SQLite (raw `sqlite3`, no ORM)   |
| Auth       | Sessions (`itsdangerous`-signed cookies) + `passlib`/`bcrypt` |
| Validation | Pydantic                         |
| Server     | Uvicorn                          |

## Project structure

```
app.py                  # FastAPI app, routes, session/auth wiring, lifespan
schemas.py               # Pydantic models for form validation
database/db.py           # get_db(), init_db(), seed_db() — raw SQLite, no ORM
templates/                # Jinja2 templates (base.html + one per page)
static/css/style.css      # single global stylesheet
static/js/main.js         # single global script
```

## Running it

```bash
pip install -r requirements.txt
python app.py
# http://127.0.0.1:5001
```

A SQLite file (`expense_tracker.db`) is created and seeded automatically on first run — it's gitignored, so it's safe to delete to reset local data.

A seeded demo user is available: `hello@example.com` / `password123`.


