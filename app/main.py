"""
FastAPI application entry point.
Mounts CORS middleware, includes API router, and creates tables on startup.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.database import engine, Base
from app.api.routes import router as api_router

# Import models so Base.metadata knows about all tables
from app.models.employee import Employee  # noqa: F401
from app.models.attendance import Attendance  # noqa: F401

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables if they don't exist. Shutdown: dispose engine."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="HRMS Lite API",
    description="Human Resource Management System — FastAPI Backend",
    version="2.0.0",
    lifespan=lifespan,
)

# ─── CORS Middleware ────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Global Exception Handler (mirrors Django DRF response shape) ───
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Return a consistent JSON error for unhandled exceptions."""
    return JSONResponse(
        status_code=500,
        content={"success": False, "errors": {"detail": "Internal server error."}},
    )


# ─── Routes ─────────────────────────────────────
app.include_router(api_router, prefix="/api")


# ─── Health Check ───────────────────────────────
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "hrms-backend"}
