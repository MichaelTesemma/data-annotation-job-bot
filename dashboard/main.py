import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import db
from scrapers import aggregators, apis, freelance, jobboards  # noqa: F401  (registers sources)
from scrapers.registry import run_all
from scrapers.state import state

app = FastAPI(title="Data Annotation Job Bot")

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class JobUpdate(BaseModel):
    applied: bool | None = None
    notes: str | None = None


class PlatformUpdate(BaseModel):
    ethiopia_accessible: bool | None = None
    status: str | None = None
    notes: str | None = None
    url: str | None = None


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/jobs")
def get_jobs(
    sort: str | None = None,
    source: str | None = None,
    remote_only: bool = False,
    min_access: float | None = None,
    applied: bool | None = None,
    search: str | None = None,
) -> list[dict]:
    filters = {
        "source": source,
        "remote_only": remote_only,
        "min_access": min_access,
        "applied": applied,
    }
    return db.get_jobs(filters=filters, sort=sort, search=search)


@app.patch("/api/jobs/{job_id}")
def update_job(job_id: int, update: JobUpdate) -> dict:
    fields = update.model_dump(exclude_none=True)
    result = db.update_job(job_id, fields)
    if result is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return result


@app.get("/api/platforms")
def get_platforms() -> list[dict]:
    return db.list_platforms()


@app.patch("/api/platforms/{name}")
def update_platform(name: str, update: PlatformUpdate) -> dict:
    fields = update.model_dump(exclude_none=True)
    result = db.update_platform(name, fields)
    if result is None:
        raise HTTPException(status_code=404, detail="Platform not found")
    return result


@app.get("/api/source-status")
def source_status() -> list[dict]:
    return db.get_source_status()


@app.get("/api/scrape/status")
def scrape_status() -> dict:
    return state.snapshot()


@app.post("/api/refresh")
def refresh() -> dict:
    def _run() -> None:
        run_all()

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return {"started": True}
