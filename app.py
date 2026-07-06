import sqlite3
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
import uvicorn

from database.db import get_db, init_db, pwd_context, seed_db
from schemas import RegisterForm


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_db()
    yield


app = FastAPI(lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates setup
templates = Jinja2Templates(directory="templates")


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


@app.post("/login")
async def login_post(request: Request):
    # Form submission placeholder (e.g. redirect or show message)
    return "Login POST — coming in Step 3"


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.get("/logout")
async def logout():
    return "Logout — coming in Step 3"


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
