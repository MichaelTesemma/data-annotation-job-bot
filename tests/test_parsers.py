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


REMOTEAFRICA_HTML = """
<html><body>
<div>
  <div>
    <p>GLOBO Language Solutions</p>
    <a href="/jobs/globo-twi-english-interpreter">Twi English Interpreter</a>
    <div>
      <span>100% Remote</span>
      <span>contract</span>
      <span>Anywhere in the World</span>
    </div>
  </div>
</div>
<div>
  <div>
    <p>Some Remote Co</p>
    <a href="/jobs/some-remote-co-data-annotator">Data Annotator</a>
    <div>
      <span>100% Remote</span>
      <span>Full-time</span>
      <span>Africa</span>
    </div>
  </div>
</div>
</body></html>
"""

NODESK_HTML = """
<html><body>
<ul>
  <li class="dt-s">
    <h2><a href="/remote-jobs/apollo-senior-product-designer-2/">Senior Product Designer</a></h2>
    <h3>Apollo</h3>
    <div>Remote: United States Design Full-Time $173.4K - $249.3K</div>
  </li>
  <li class="dt-s">
    <h2><a href="/remote-jobs/scale-ai-data-annotator-5/">Data Annotator</a></h2>
    <h3>Scale AI</h3>
    <div>Remote: Worldwide AI Full-Time</div>
  </li>
</ul>
</body></html>
"""

FREELANCER_HTML = """
<html><body>
<div class="ProjectSearch-content">
  <div class="JobSearchCard-list">
    <div class="JobSearchCard-item">
      <div class="JobSearchCard-item-inner" data-project-card="true">
        <div class="JobSearchCard-primary">
          <div class="JobSearchCard-primary-heading">
            <a class="JobSearchCard-primary-heading-link" href="/projects/data-collection/mobile-survey-form">Mobile Survey Form Bharai</a>
            <div class="JobSearchCard-primary-heading-daystatus">
              <span class="JobSearchCard-primary-heading-days">6 days left</span>
            </div>
          </div>
          <p class="JobSearchCard-primary-description">Need help filling online survey forms.</p>
          <div class="JobSearchCard-primary-price">$10 / hr Average bid</div>
        </div>
      </div>
    </div>
    <div class="JobSearchCard-item">
      <div class="JobSearchCard-item-inner" data-project-card="true">
        <div class="JobSearchCard-primary">
          <div class="JobSearchCard-primary-heading">
            <a class="JobSearchCard-primary-heading-link" href="/projects/data-entry/spreadsheet-entry">Spreadsheet Data Entry</a>
            <div class="JobSearchCard-primary-heading-daystatus">
              <span class="JobSearchCard-primary-heading-days">2 days left</span>
            </div>
          </div>
          <p class="JobSearchCard-primary-description">Enter rows into Excel.</p>
          <div class="JobSearchCard-primary-price">$5 / hr Average bid</div>
        </div>
      </div>
    </div>
  </div>
</div>
</body></html>
"""

REMOTEOK_JSON = [
    {"position": "Anchorman", "company": "TV", "tags": ["media"], "url": "https://remoteok.com/a"},
    {
        "position": "Data Annotator", "company": "Annotation Co", "url": "https://remoteok.com/remote-jobs/data-annotator-1",
        "date": "2026-08-14T00:00:00+00:00", "location": "Anywhere", "salary_min": 30000, "salary_max": 50000,
        "tags": ["data annotation", "ai training", "full time"],
    },
]

REMOTIVE_JSON = {
    "jobs": [
        {
            "title": "AI Trainer", "company_name": "Scale AI", "url": "https://remotive.com/remote-jobs/ai-trainer-1",
            "candidate_required_location": "Anywhere", "salary": "Pay per task", "publication_date": "2026-08-10",
            "description": "<p>Train models on data.</p>", "category": "All others", "job_type": "part_time",
        },
        {
            "title": "Data Entry Clerk", "company_name": "Aquent", "url": "https://remotive.com/remote-jobs/data-entry-2",
            "candidate_required_location": "USA", "salary": "$18/hr", "publication_date": "2026-08-09",
            "description": "Enter data into systems.",
        },
    ]
}

WORKINGNOMADS_JSON = [
    {
        "url": "https://www.workingnomads.com/job/go/1/", "title": "Senior Data Engineer",
        "company_name": "Lemon.io", "location": "Worldwide", "pub_date": "2026-08-08",
        "category_name": "Data Engineering",
        "description": "<p>Build pipelines.</p>",
    },
    {
        "url": "https://www.workingnomads.com/job/go/2/", "title": "AI Tutor for Data Annotation",
        "company_name": "Edu Co", "location": "Anywhere", "pub_date": "2026-08-07",
        "category_name": "Data Annotation",
        "description": "<p>Tutor and annotate.</p>",
    },
]


def test_remoteafrica_parses_jobs():
    from scrapers.aggregators import RemoteAfricaScraper

    scraper = RemoteAfricaScraper()
    jobs = scraper._parse(REMOTEAFRICA_HTML, "remoteafrica")
    assert len(jobs) == 2
    first = jobs[0]
    assert first["title"] == "Twi English Interpreter"
    assert first["company"] == "GLOBO Language Solutions"
    assert first["remote"] is True
    assert first["url"] == "https://remote4africa.com/jobs/globo-twi-english-interpreter"


def test_nodesk_parses_jobs():
    from scrapers.aggregators import NodeSkScraper

    scraper = NodeSkScraper()
    jobs = scraper._parse(NODESK_HTML, "ai")
    assert len(jobs) == 2
    first = jobs[0]
    assert first["title"] == "Senior Product Designer"
    assert first["company"] == "Apollo"
    assert first["url"] == "https://nodesk.co/remote-jobs/apollo-senior-product-designer-2/"


def test_freelancer_parses_jobs():
    from scrapers.freelance import FreelancerScraper

    scraper = FreelancerScraper()
    jobs = scraper._parse(FREELANCER_HTML, "data-entry")
    assert len(jobs) == 2
    first = jobs[0]
    assert first["title"] == "Mobile Survey Form Bharai"
    assert first["pay"] == "$10 / hr Average bid"
    assert first["url"] == "https://www.freelancer.com/projects/data-collection/mobile-survey-form"


def test_remoteok_parses_jobs():
    import json
    from scrapers.apis import RemoteOkScraper

    scraper = RemoteOkScraper()
    jobs = scraper._parse(json.dumps(REMOTEOK_JSON), "term")
    assert len(jobs) == 1
    job = jobs[0]
    assert job["title"] == "Data Annotator"
    assert job["company"] == "Annotation Co"
    assert job["pay"] == "$30,000 - $50,000"


def test_remotive_parses_jobs():
    import json
    from scrapers.apis import RemotiveScraper

    scraper = RemotiveScraper()
    jobs = scraper._parse(json.dumps(REMOTIVE_JSON), "term")
    assert len(jobs) == 2
    assert jobs[0]["title"] == "AI Trainer"
    assert jobs[0]["company"] == "Scale AI"
    assert jobs[0]["pay"] == "Pay per task"
    assert jobs[1]["location"] == "USA"


def test_workingnomads_parses_jobs():
    import json
    from scrapers.apis import WorkingNomadsScraper

    scraper = WorkingNomadsScraper()
    jobs = scraper._parse(json.dumps(WORKINGNOMADS_JSON), "term")
    assert len(jobs) == 1
    job = jobs[0]
    assert job["title"] == "AI Tutor for Data Annotation"
    assert job["company"] == "Edu Co"
    assert job["url"] == "https://www.workingnomads.com/job/go/2/"
