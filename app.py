import os
import sqlite3
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from starlette.middleware.sessions import SessionMiddleware
import uvicorn

from database.db import get_db, init_db, pwd_context, seed_db
from schemas import LoginForm, RegisterForm


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_db()
    yield


app = FastAPI(lifespan=lifespan)

# Session cookie signing key. Must be set via env var in production; falls
# back to a fixed dev-only value so the app still runs locally out of the box.
IS_PRODUCTION = os.environ.get("ENV", "development") == "production"
SESSION_SECRET_KEY = os.environ.get("SESSION_SECRET_KEY")
if not SESSION_SECRET_KEY:
    if IS_PRODUCTION:
        raise RuntimeError("SESSION_SECRET_KEY environment variable must be set in production")
    SESSION_SECRET_KEY = "dev-only-insecure-secret-key"

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY,
    same_site="lax",
    https_only=IS_PRODUCTION,
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates setup
templates = Jinja2Templates(directory="templates")

# Precomputed hash to verify against when no user is found, so login takes
# roughly the same time whether or not the email exists (avoids leaking
# account existence via response timing).
_DUMMY_PASSWORD_HASH = pwd_context.hash("no-such-user")


# ------------------------------------------------------------------ #
# Routes                                                             #
# ------------------------------------------------------------------ #

@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse(request, "landing.html")


@app.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse(request, "register.html")


@app.post("/register", response_class=HTMLResponse)
async def register_post(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
):
    try:
        data = RegisterForm(name=name, email=email, password=password)
    except ValidationError as exc:
        error = exc.errors()[0]["msg"].removeprefix("Value error, ")
        return templates.TemplateResponse(
            request, "register.html", {"error": error}, status_code=400
        )

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (data.name, data.email, pwd_context.hash(data.password)),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        return templates.TemplateResponse(
            request,
            "register.html",
            {"error": "An account with that email already exists."},
            status_code=400,
        )
    finally:
        conn.close()

    return RedirectResponse(url="/login", status_code=303)


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse(request, "login.html")


@app.get("/terms", response_class=HTMLResponse)
async def terms(request: Request):
    return templates.TemplateResponse(request, "terms.html")


@app.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    return templates.TemplateResponse(request, "privacy.html")


@app.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    try:
        data = LoginForm(email=email, password=password)
    except ValidationError as exc:
        error = exc.errors()[0]["msg"].removeprefix("Value error, ")
        return templates.TemplateResponse(
            request, "login.html", {"error": error}, status_code=400
        )

    conn = get_db()
    try:
        user = conn.execute(
            "SELECT id, password_hash FROM users WHERE email = ?", (data.email,)
        ).fetchone()
    finally:
        conn.close()

    password_hash = user["password_hash"] if user else _DUMMY_PASSWORD_HASH
    if not pwd_context.verify(data.password, password_hash) or user is None:
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Invalid email or password."},
            status_code=400,
        )

    request.session.clear()
    request.session["user_id"] = user["id"]
    return RedirectResponse(url="/profile", status_code=303)


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.get("/profile")
async def profile():
    return "Profile page — coming in Step 4"


@app.get("/expenses/add")
async def add_expense():
    return "Add expense — coming in Step 7"


@app.get("/expenses/{id}/edit")
async def edit_expense(id: int):
    return f"Edit expense {id} — coming in Step 8"


@app.get("/expenses/{id}/delete")
async def delete_expense(id: int):
    return f"Delete expense {id} — coming in Step 9"


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=5001, reload=True)
