from pathlib import Path
import traceback
import uvicorn

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse , JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend import run_travel_agent

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title='AI TRAVEL PLANNING SYSTEM'
    description="Langgraph Multi Travel Agent with FastAPI Frontend"
    version="1.0.0"
)

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "templates")),
    name = "static"

)

templates = Jinja2Templates(
    directory = str(BASE_DIR / "templates")
)

