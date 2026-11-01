"""FastAPI entry point for the recovered Python travel-planner workflow."""
from contextlib import asynccontextmanager
import os
from pathlib import Path
import traceback

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from .backend import close_resources, resume_travel_agent, run_travel_agent


PROJECT_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = PROJECT_DIR / "static"
TEMPLATES_DIR = PROJECT_DIR / "templates"


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Release the optional PostgreSQL connection during shutdown."""
    yield
    close_resources()


app = FastAPI(
    title="TripMate AI",
    description=(
        "LangGraph Multi-Agent Travel Planner with Supervisor, Guardrails, "
        "Human-in-the-Loop, and FastAPI Frontend"
    ),
    version="2.1.0",
    lifespan=lifespan,
)

if STATIC_DIR.is_dir():
    app.mount(
        "/static",
        StaticFiles(directory=str(STATIC_DIR)),
        name="static",
    )
else:
    raise RuntimeError(f"Static assets directory is missing: {STATIC_DIR}")

if not TEMPLATES_DIR.is_dir():
    raise RuntimeError(f"Templates directory is missing: {TEMPLATES_DIR}")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


class TravelRequest(BaseModel):
    message: str = Field(min_length=1)
    thread_id: str | None = None


class ApprovalRequest(BaseModel):
    thread_id: str = Field(min_length=1)
    approved: bool
    feedback: str = ""


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )


@app.post("/api/travel")
def travel_planner(request_data: TravelRequest):
    """Run the synchronous LangGraph workflow in FastAPI's worker thread."""
    user_message = request_data.message.strip()
    if not user_message:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Message cannot be empty."},
        )

    try:
        result = run_travel_agent(
            user_input=user_message,
            thread_id=request_data.thread_id,
        )
        return JSONResponse(content={"success": True, **result})
    except Exception as exc:
        print(f"TRAVEL PLANNER ERROR: {type(exc).__name__}: {exc}", flush=True)
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(exc),
            },
        )


@app.post("/api/travel/approve")
def approve_travel_plan(request_data: ApprovalRequest):
    """Resume the persisted LangGraph thread after human review."""
    if not request_data.approved and not request_data.feedback.strip():
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": "Please provide revision feedback when rejecting the draft.",
            },
        )

    try:
        result = resume_travel_agent(
            thread_id=request_data.thread_id,
            approved=request_data.approved,
            feedback=request_data.feedback,
        )
        return JSONResponse(content={"success": True, **result})
    except Exception as exc:
        print(f"APPROVAL ERROR: {type(exc).__name__}: {exc}", flush=True)
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(exc),
            },
        )


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "message": "TripMate AI Python API is running",
        "checkpoint_storage": (
            "postgresql"
            if os.getenv("DATABASE_URL")
            else "in-memory (development only)"
        ),
        "features": [
            "supervisor_agent",
            "input_guardrail",
            "flight_agent",
            "hotel_agent",
            "weather_agent",
            "budget_agent",
            "itinerary_agent",
            "human_in_the_loop",
        ],
    }


@app.get("/favicon.ico")
async def favicon():
    return JSONResponse(content={})


if __name__ == "__main__":
    uvicorn.run(
        "tools.app:app",
        host="0.0.0.0",
        port=int(os.getenv("PYTHON_PORT", "8000")),
        reload=False,
    )
