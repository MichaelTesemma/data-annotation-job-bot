import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from config import SETTINGS
from scrapers.base import BaseScraper
from scrapers.registry import register, run_all

STUB_HTML = """
<html><body>
<section class="jobs"><ul>
  <li class="new-listing-container">
    <a class="listing-link--unlocked" href="/remote-jobs/stub-annotation-1">
      <h3 class="new-listing__header__title"><span class="new-listing__header__title__text">Stub Annotation Job</span></h3>
      <p class="new-listing__company-name">Toloka</p>
      <p class="new-listing__company-headquarters">Worldwide</p>
      <p class="new-listing__header__icons__date">1d</p>
      <div class="new-listing__categories"><p class="new-listing__categories__category">Worldwide</p></div>
    </a>
  </li>
</ul></section>
</body></html>
"""


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(STUB_HTML.encode())
        self.wfile.write(f"<!--{self.path}-->".encode())

    def log_message(self, *args):
        pass


@pytest.fixture()
def stub_server():
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


@pytest.fixture()
def stub_sources(stub_server, monkeypatch):
    monkeypatch.setattr(SETTINGS, "robots_enabled", False)
    monkeypatch.setattr(SETTINGS, "rate_limit_seconds", 0.0)
    import scrapers.registry as reg

    @register("stub_integration")
    def stub_integration():
        class Stub(BaseScraper):
            name = "stub_integration"

            def fetch_jobs(self):
                return [{
                    "title": "Stub Annotation Job",
                    "company": "Toloka",
                    "url": f"{stub_server}/remote-jobs/stub-annotation-1",
                    "location": "Worldwide",
                    "remote": True,
                    "pay": "$18/hr",
                    "description": "A global stub annotation job open worldwide",
                }]
        return Stub()

    @register("stub_failing")
    def stub_failing():
        class Failing(BaseScraper):
            name = "stub_failing"

            def fetch_jobs(self):
                raise RuntimeError("boom")
        return Failing()

    yield reg


def test_pipeline_runs_without_crash_and_failure_is_isolated(db_session, stub_sources):
    results = run_all(["stub_integration", "stub_failing"])
    statuses = {r["source"]: r["status"] for r in results}
    assert statuses["stub_integration"] == "success"
    assert statuses["stub_failing"] == "error"

    jobs = db_session.get_jobs()
    assert len(jobs) == 1
    assert jobs[0]["company"] == "Toloka"
    assert jobs[0]["access_score"] > 0.7


def test_source_status_records_runs(db_session, stub_sources):
    run_all(["stub_integration", "stub_failing"])
    status = {s["source"]: s for s in db_session.get_source_status()}
    assert status["stub_integration"]["status"] == "success"
    assert status["stub_integration"]["count_found"] == 1
    assert status["stub_failing"]["status"] == "error"
    assert "boom" in status["stub_failing"]["error"]
