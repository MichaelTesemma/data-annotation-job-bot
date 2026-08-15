import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from config import SETTINGS


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    company TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    location TEXT NOT NULL DEFAULT '',
    remote INTEGER NOT NULL DEFAULT 0,
    pay TEXT NOT NULL DEFAULT '',
    posted_at TEXT NOT NULL DEFAULT '',
    discovered_at TEXT NOT NULL DEFAULT '',
    access_score REAL NOT NULL DEFAULT 0.0,
    overall_score REAL NOT NULL DEFAULT 0.0,
    applied INTEGER NOT NULL DEFAULT 0,
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS platforms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    url TEXT NOT NULL DEFAULT '',
    ethiopia_accessible INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'not_applied',
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS source_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    count_found INTEGER NOT NULL DEFAULT 0,
    error TEXT
);

CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);
CREATE INDEX IF NOT EXISTS idx_jobs_remote ON jobs(remote);
CREATE INDEX IF NOT EXISTS idx_jobs_applied ON jobs(applied);
"""


@contextmanager
def get_conn():
    db_path: Path = SETTINGS.db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(_SCHEMA)


def upsert_job(job: dict) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO jobs (
                title, company, source, url, description, location, remote,
                pay, posted_at, discovered_at, access_score, overall_score,
                applied, notes
            ) VALUES (
                :title, :company, :source, :url, :description, :location, :remote,
                :pay, :posted_at, :discovered_at, :access_score, :overall_score,
                :applied, :notes
            )
            ON CONFLICT(url) DO UPDATE SET
                title = excluded.title,
                company = excluded.company,
                source = excluded.source,
                description = excluded.description,
                location = excluded.location,
                remote = excluded.remote,
                pay = excluded.pay,
                posted_at = excluded.posted_at,
                access_score = excluded.access_score,
                overall_score = excluded.overall_score
            """,
            _job_row(job),
        )


def _job_row(job: dict) -> dict:
    now = _utcnow()
    return {
        "title": job.get("title", "").strip(),
        "company": job.get("company", "").strip(),
        "source": job.get("source", "").strip(),
        "url": job.get("url", "").strip(),
        "description": job.get("description", "").strip(),
        "location": job.get("location", "").strip(),
        "remote": int(bool(job.get("remote"))),
        "pay": job.get("pay", "").strip(),
        "posted_at": job.get("posted_at", "").strip(),
        "discovered_at": job.get("discovered_at") or now,
        "access_score": float(job.get("access_score", 0.0) or 0.0),
        "overall_score": float(job.get("overall_score", 0.0) or 0.0),
        "applied": int(bool(job.get("applied"))),
        "notes": job.get("notes", "").strip(),
    }


def get_jobs(filters: dict | None = None, sort: str | None = None, search: str | None = None) -> list[dict]:
    filters = filters or {}
    clauses: list[str] = []
    params: list = []

    source = filters.get("source")
    if source:
        clauses.append("source = ?")
        params.append(source)

    if filters.get("remote_only"):
        clauses.append("remote = 1")

    min_access = filters.get("min_access")
    if min_access is not None:
        clauses.append("access_score >= ?")
        params.append(float(min_access))

    applied = filters.get("applied")
    if applied is not None:
        clauses.append("applied = ?")
        params.append(int(bool(applied)))

    if search:
        clauses.append("(title LIKE ? OR company LIKE ? OR description LIKE ? OR pay LIKE ?)")
        like = f"%{search}%"
        params.extend([like, like, like, like])

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    order = {
        "access_score": "access_score DESC",
        "overall_score": "overall_score DESC",
        "discovered_at": "discovered_at DESC",
        "posted_at": "posted_at DESC",
        "title": "title ASC",
        "company": "company ASC",
        "source": "source ASC",
    }.get(sort, "overall_score DESC")

    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM jobs {where} ORDER BY {order}", params
        ).fetchall()
    return [dict(r) for r in rows]


def update_job(job_id: int, fields: dict) -> dict | None:
    allowed = {"applied", "notes"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return None
    assignments = ", ".join(f"{k} = ?" for k in updates)
    values = [int(bool(updates[k])) if k == "applied" else str(updates[k]) for k in updates]
    values.append(job_id)
    with get_conn() as conn:
        conn.execute(f"UPDATE jobs SET {assignments} WHERE id = ?", values)
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return dict(row) if row else None


def list_platforms() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM platforms ORDER BY name").fetchall()
    return [dict(r) for r in rows]


def update_platform(name: str, fields: dict) -> dict | None:
    allowed = {"ethiopia_accessible", "status", "notes", "url"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return None
    assignments = ", ".join(f"{k} = ?" for k in updates)
    values = [
        int(bool(updates[k])) if k == "ethiopia_accessible" else str(updates[k])
        for k in updates
    ]
    values.append(name)
    with get_conn() as conn:
        conn.execute(f"UPDATE platforms SET {assignments} WHERE name = ?", values)
        row = conn.execute("SELECT * FROM platforms WHERE name = ?", (name,)).fetchone()
    return dict(row) if row else None


def record_source_run(source: str, status: str, count_found: int = 0, error: str | None = None) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO source_runs (source, started_at, finished_at, status, count_found, error)
            VALUES (:source, :started_at, :finished_at, :status, :count_found, :error)
            """,
            {
                "source": source,
                "started_at": _utcnow(),
                "finished_at": _utcnow(),
                "status": status,
                "count_found": int(count_found),
                "error": error,
            },
        )


def get_source_status() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT source, started_at, finished_at, status, count_found, error
            FROM source_runs
            WHERE id IN (
                SELECT MAX(id) FROM source_runs GROUP BY source
            )
            ORDER BY source
            """
        ).fetchall()
    return [dict(r) for r in rows]
