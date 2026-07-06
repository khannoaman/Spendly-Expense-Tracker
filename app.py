from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from database.db import init_db, seed_db


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


@app.post("/register")
async def register_post(request: Request):
    # Form submission placeholder (e.g. redirect or show message)
    return "Register POST — coming in Step 2"


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
