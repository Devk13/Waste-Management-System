# ==================================
# backend/app/main_jobs_mount.py
# (Drop-in snippet to mount + CORS; use in your main.py)
# ==================================
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import FRONTEND_ORIGINS, ENABLE_DRIVER_JOBS_SCHEDULE
from .routers.admin import jobs as admin_jobs
from .routers.driver import schedule_jobs as driver_sched   # only if you don't already have one

def mount_jobs(app: FastAPI) -> None:
    # CORS: allow explicit frontend origins only.
    if FRONTEND_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[o.strip() for o in FRONTEND_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    app.include_router(admin_jobs.router)

    # Optional: only if your project lacks /driver/schedule.
    if ENABLE_DRIVER_JOBS_SCHEDULE:
        app.include_router(driver_sched.router)
