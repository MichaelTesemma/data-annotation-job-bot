from fastapi.testclient import TestClient

from dashboard.main import app
import db


def _make_job(db_session, url="https://example.com/jobs/api-1", title="API Test Job", description="global"):
    job = {
        "title": title, "company": "Toloka", "source": "stub_api",
        "url": url, "description": description, "location": "Worldwide", "remote": True,
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


def test_jobs_category_filter(db_session):
    _make_job(db_session, url="https://example.com/jobs/annotation-1", title="AI Data Annotator", description="labeling training data")
    _make_job(db_session, url="https://example.com/jobs/translation-2", title="Amharic English Translator", description="translate english to amharic")
    with TestClient(app) as client:
        res = client.get("/api/categories")
        assert res.status_code == 200
        assert "translation" in res.json()
        assert "data annotation" in res.json()

        annotation = client.get("/api/jobs", params={"category": "data annotation"}).json()
        translation = client.get("/api/jobs", params={"category": "translation"}).json()
        assert len(annotation) == 1
        assert annotation[0]["title"] == "AI Data Annotator"
        assert len(translation) == 1
        assert translation[0]["title"] == "Amharic English Translator"


def test_export_csv(db_session):
    _make_job(db_session, url="https://example.com/jobs/csv-1")
    with TestClient(app) as client:
        res = client.get("/api/jobs/export")
        assert res.status_code == 200
        assert "text/csv" in res.headers["content-type"]
        assert "filename=" in res.headers["content-disposition"]
        body = res.text
        assert body.startswith("\ufeff")  # UTF-8 BOM for Excel
        assert "title,company,source,url" in body
        assert "API Test Job" in body


def test_index_serves_dashboard():
    with TestClient(app) as client:
        res = client.get("/")
        assert res.status_code == 200
        assert "Data Annotation Job Bot" in res.text
