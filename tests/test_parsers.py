from bs4 import BeautifulSoup

import db
from scrapers.aggregators import WeWorkRemotelyScraper, RemoteCoScraper

WWR_HTML = """
<html><body>
<section class="jobs">
  <ul>
    <li class="listing-ad feature--ad"><a class="listing-ad-url--main" href="/ads/1">Sponsored</a></li>
    <li class="new-listing-container feature">
      <a class="listing-link--unlocked" href="/remote-jobs/toloka-annotation-1">
        <h3 class="new-listing__header__title"><span class="new-listing__header__title__text">AI Annotation Specialist</span></h3>
        <p class="new-listing__company-name">Toloka</p>
        <p class="new-listing__company-headquarters">Berlin, DE</p>
        <p class="new-listing__header__icons__date">3d</p>
        <div class="new-listing__categories">
          <p class="new-listing__categories__category">Contract</p>
          <p class="new-listing__categories__category">Worldwide</p>
          <p class="new-listing__categories__category">$20/hr</p>
        </div>
      </a>
    </li>
    <li class="new-listing-container feature">
      <a class="listing-link--unlocked" href="/remote-jobs/dataannotation-us-only-2">
        <h3 class="new-listing__header__title"><span class="new-listing__header__title__text">Prompt Engineer</span></h3>
        <p class="new-listing__company-name">DataAnnotation.tech</p>
        <p class="new-listing__company-headquarters">New York, NY</p>
        <p class="new-listing__header__icons__date">11d</p>
        <div class="new-listing__categories">
          <p class="new-listing__categories__category">Contract</p>
          <p class="new-listing__categories__category">North America Only</p>
        </div>
      </a>
    </li>
  </ul>
</section>
</body></html>
"""

REMOTECO_HTML = """
<html><body>
<div>
  <div>
    <div>
      <a href="/job-details/data-annotator-1-abc123">
        <span class="date">Today</span><h3>Remote Data Annotator</h3>
      </a>
    </div>
  </div>
  <strong id="company-name-abc123">Clickworker</strong>
  <ul>
    <li>100% Remote Work</li>
    <li>Full-Time</li>
    <li>$15 - $20/hr</li>
  </ul>
</div>
<div>
  <div>
    <div>
      <a href="/job-details/ai-trainer-2-def456">
        <span class="date">2d</span><h3>AI Trainer</h3>
      </a>
    </div>
  </div>
  <strong id="company-name-def456">US Corp</strong>
  <ul>
    <li>100% Remote Work</li>
    <li>Full-Time</li>
  </ul>
</div>
</body></html>
"""

LINKEDIN_HTML = """
<html><body>
<div>
  <div>
    <a href="https://www.linkedin.com/jobs/view/data-annotator-at-toloka-12345?position=1&pageNum=0">
      <h3 class="base-search-card__title">Data Annotator</h3>
    </a>
    <h4 class="base-search-card__subtitle"><a href="https://www.linkedin.com/company/toloka">Toloka</a></h4>
    <div class="base-search-card__metadata">
      <span class="job-search-card__location">Worldwide</span>
      <time class="job-search-card__listdate" datetime="2026-08-01">1 week ago</time>
    </div>
  </div>
</div>
</body></html>
"""


def test_wwr_parses_jobs_and_skips_ads():
    scraper = WeWorkRemotelyScraper()
    jobs = scraper._parse(WWR_HTML, "data annotation")
    assert len(jobs) == 2
    first = jobs[0]
    assert first["title"] == "AI Annotation Specialist"
    assert first["company"] == "Toloka"
    assert first["pay"] == "$20/hr"
    assert first["remote"] is True
    assert "Worldwide" in first["location"]
    assert first["url"] == "https://weworkremotely.com/remote-jobs/toloka-annotation-1"


def test_wwr_parser_survives_empty_page():
    scraper = WeWorkRemotelyScraper()
    assert scraper._parse("<html><body></body></html>", "term") == []


def test_remoteco_parses_jobs():
    scraper = RemoteCoScraper()
    jobs = scraper._parse(REMOTECO_HTML, "online-data-entry")
    assert len(jobs) == 2
    assert jobs[0]["title"] == "Remote Data Annotator"
    assert jobs[0]["company"] == "Clickworker"
    assert jobs[0]["pay"] == "$15 - $20/hr"
    assert "100% Remote Work" in jobs[0]["location"]
    assert jobs[0]["url"] == "https://remote.co/job-details/data-annotator-1-abc123"


def test_linkedin_parses_jobs():
    from scrapers.jobboards import LinkedInScraper

    scraper = LinkedInScraper()
    jobs = scraper._parse(LINKEDIN_HTML, "data annotation")
    assert len(jobs) == 1
    job = jobs[0]
    assert job["title"] == "Data Annotator"
    assert job["company"] == "Toloka"
    assert job["location"] == "Worldwide"
    assert job["posted_at"] == "2026-08-01"
    assert job["url"] == "https://www.linkedin.com/jobs/view/data-annotator-at-toloka-12345"


def test_upsert_dedups_by_url(db_session):
    job = {
        "title": "AI Annotation Specialist", "company": "Toloka", "source": "weworkremotely",
        "url": "https://weworkremotely.com/remote-jobs/toloka-annotation-1",
        "description": "first", "location": "Worldwide", "remote": True,
        "pay": "$20/hr", "posted_at": "3d",
        "access_score": 0.9, "overall_score": 0.9,
    }
    db_session.upsert_job(job)
    job["description"] = "updated"
    db_session.upsert_job(job)
    jobs = db_session.get_jobs()
    assert len(jobs) == 1
    assert jobs[0]["description"] == "updated"
    assert jobs[0]["title"] == "AI Annotation Specialist"


def test_soup_parse_smoke():
    soup = BeautifulSoup(WWR_HTML, "html.parser")
    assert len(soup.select("li.new-listing-container:not(.listing-ad)")) == 2
