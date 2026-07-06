import os
import sqlite3
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Form, HTTPException, Request
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

# Fixed categorical order for the profile category breakdown, validated for
# CVD-safe adjacent contrast against the app's card surface. Categories beyond
# this many are folded into "Other" (muted) rather than growing the palette.
_CATEGORY_COLORS = [
    "#2a78d6",  # blue
    "#1baf7a",  # aqua
    "#eda100",  # yellow
    "#008300",  # green
    "#4a3aa7",  # violet
    "#e34948",  # red
]
_OTHER_COLOR = "#898781"  # muted ink — signals "not a distinct identity"


def get_current_user(request: Request) -> sqlite3.Row:
    user_id = request.session.get("user_id")
    if user_id is not None:
        conn = get_db()
        try:
            user = conn.execute(
                "SELECT id, name, email, created_at FROM users WHERE id = ?", (user_id,)
            ).fetchone()
        finally:
            conn.close()
        if user is not None:
            return user
        request.session.clear()
    raise HTTPException(status_code=303, headers={"Location": "/login"})


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


@app.get("/profile", response_class=HTMLResponse)
async def profile(request: Request, user: sqlite3.Row = Depends(get_current_user)):
    conn = get_db()
    try:
        rows = conn.execute(
            """
            SELECT amount, category, description, date
            FROM expenses
            WHERE user_id = ?
            ORDER BY date DESC, id DESC
            """,
            (user["id"],),
        ).fetchall()
    finally:
        conn.close()

    total = sum(r["amount"] for r in rows)

    category_totals: dict[str, float] = {}
    for r in rows:
        category_totals[r["category"]] = category_totals.get(r["category"], 0) + r["amount"]
    ranked_categories = sorted(category_totals.items(), key=lambda kv: kv[1], reverse=True)

    top_categories = ranked_categories[: len(_CATEGORY_COLORS)]
    other_total = sum(amount for _, amount in ranked_categories[len(_CATEGORY_COLORS) :])

    categories = [
        {
            "name": name,
            "amount_formatted": f"{amount:,.2f}",
            "pct": (amount / total * 100) if total else 0,
            "color": _CATEGORY_COLORS[i],
        }
        for i, (name, amount) in enumerate(top_categories)
    ]
    if other_total > 0:
        categories.append(
            {
                "name": "Other",
                "amount_formatted": f"{other_total:,.2f}",
                "pct": (other_total / total * 100) if total else 0,
                "color": _OTHER_COLOR,
            }
        )

    category_color_by_name = {name: _CATEGORY_COLORS[i] for i, (name, _) in enumerate(top_categories)}

    expenses = [
        {
            "date": r["date"],
            "category": r["category"],
            "description": r["description"],
            "amount_formatted": f"{r['amount']:,.2f}",
            "color": category_color_by_name.get(r["category"], _OTHER_COLOR),
        }
        for r in rows
    ]

    return templates.TemplateResponse(
        request,
        "profile.html",
        {
            "user": user,
            "expenses": expenses,
            "total_formatted": f"{total:,.2f}",
            "transaction_count": len(rows),
            "categories": categories,
            "top_category": categories[0] if categories else None,
        },
    )


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #



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
