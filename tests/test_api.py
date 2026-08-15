from fastapi.testclient import TestClient

from dashboard.main import app
import db


def _make_job(db_session, url="https://example.com/jobs/api-1"):
    job = {
        "title": "API Test Job", "company": "Toloka", "source": "stub_api",
        "url": url, "description": "global", "location": "Worldwide", "remote": True,
        "pay": "$20/hr", "access_score": 0.9, "overall_score": 0.9,
    }
    db_session.upsert_job(job)


def test_get_jobs(db_session):
    _make_job(db_session)
    with TestClient(app) as client:
        res = client.get("/api/jobs")
        assert res.status_code == 200
        assert len(res.json()) == 1
        assert res.json()[0]["title"] == "API Test Job"


def test_get_jobs_filters(db_session):
    _make_job(db_session)
    _make_job(db_session, url="https://example.com/jobs/api-2")
    with TestClient(app) as client:
        res = client.get("/api/jobs", params={"remote_only": True})
        assert res.status_code == 200
        assert len(res.json()) == 2

        res = client.get("/api/jobs", params={"min_access": 0.95})
        assert res.status_code == 200
        assert res.json() == []

        res = client.get("/api/jobs", params={"search": "API Test"})
        assert len(res.json()) == 2


def test_patch_job(db_session):
    _make_job(db_session)
    with TestClient(app) as client:
        job_id = client.get("/api/jobs").json()[0]["id"]
        res = client.patch(f"/api/jobs/{job_id}", json={"applied": True, "notes": "n"})
        assert res.status_code == 200
        assert res.json()["applied"] is True
        assert res.json()["notes"] == "n"


def test_patch_job_missing_returns_404(db_session):
    with TestClient(app) as client:
        res = client.patch("/api/jobs/999999", json={"applied": True})
        assert res.status_code == 404


def test_platforms_crud(db_session):
    with TestClient(app) as client:
        res = client.patch("/api/platforms/Toloka", json={"status": "applied"})
        assert res.status_code == 404  # not seeded in test db

        db_session.update_platform("Toloka", {})  # no-op ok


def test_source_status(db_session):
    db_session.record_source_run("stub", "success", 2)
    with TestClient(app) as client:
        res = client.get("/api/source-status")
        assert res.status_code == 200
        assert res.json()[0]["source"] == "stub"


def test_refresh_starts_background_job():
    with TestClient(app) as client:
        res = client.post("/api/refresh")
        assert res.status_code == 200
        assert res.json() == {"started": True}


def test_scrape_status_endpoint_shape():
    with TestClient(app) as client:
        res = client.get("/api/scrape/status")
        assert res.status_code == 200
        body = res.json()
        for key in ("running", "started_at", "finished_at", "total_sources", "completed", "sources"):
            assert key in body
        assert isinstance(body["sources"], list)


def test_index_serves_dashboard():
    with TestClient(app) as client:
        res = client.get("/")
        assert res.status_code == 200
        assert "Data Annotation Job Bot" in res.text
