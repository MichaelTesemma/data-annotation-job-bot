# Data Annotation Job Bot

A personal tool that crawls the internet for data annotation jobs, ranks opportunities by how accessible they are from Ethiopia, and serves a local web dashboard to browse, filter, and track them.

## Features

- **Crawls three source types**: dedicated AI/data platforms (tracked as reference entries), general job boards (Indeed, LinkedIn, Wellfound), and remote job aggregators (WeWorkRemotely, Remote.co).
- **Ethiopia-first ranking**: every job is scored 0–1 for Ethiopia accessibility (`access_score`) and overall desirability (`overall_score`). Nothing is dropped — low-access listings just sort lower and can be filtered out.
- **Local dashboard**: sort, filter by source/remote/score/applied, search, mark jobs as applied, edit notes, and hit "Refresh now" to re-crawl. All data lives in a local SQLite database.
- **Resilient scraping**: each source runs independently; a blocked or failing source never stops the others. Per-source status is shown on the dashboard.
- **Polite by default**: respects `robots.txt`, rate-limits requests, and only falls back to a real browser (Playwright) when a lightweight fetch is blocked.

## Setup

Requires Python 3.11+.

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"

# install the Playwright browser (needed for the blocked job boards)
.venv/bin/python -m playwright install chromium
```

## Usage

```bash
# seed the dedicated-platforms reference table (once)
.venv/bin/python scrape.py --seed-platforms

# crawl all sources
.venv/bin/python scrape.py

# crawl just one source
.venv/bin/python scrape.py --source weworkremotely

# start the dashboard
.venv/bin/python run_dashboard.py          # opens at http://127.0.0.1:8000

# optional: run on a schedule (off by default)
.venv/bin/python scheduler.py              # every 4 hours
.venv/bin/python scheduler.py --interval 2 # every 2 hours
```

## Project layout

```
scrapers/          one module per source
  base.py          shared fetch/robots/rate-limit helpers + BaseScraper
  aggregators.py   WeWorkRemotely, Remote.co
  jobboards.py     Indeed, LinkedIn, Wellfound (best-effort)
  registry.py      source discovery + run_all()
dashboard/         FastAPI app
  main.py          API routes + refresh endpoint
  static/          HTML/CSS/JS dashboard
db.py              SQLite schema + read/write helpers
rank.py            Ethiopia-accessibility and desirability scoring
scrape.py          CLI entry point
run_dashboard.py   dashboard server entry point
scheduler.py       optional scheduled runs
tests/             unit + integration tests (pytest)
```

## Configuration

Copy the defaults in `config.py` into a gitignored `config.local.py` to override them, e.g.:

```python
rate_limit_seconds = 1.0
scheduler_interval_hours = 6
search_terms = ["data annotation", "data labeling"]
max_results_per_term = 100
robots_enabled = False  # not recommended
```

## Troubleshooting

- **Sources returning 0 / failing**: Indeed, LinkedIn, Wellfound, and Remote.co actively block scrapers. The dashboard's "Source status" panel shows which sources work and why the others fail. WeWorkRemotely is the most reliable.
- **Playwright not found**: run `.venv/bin/python -m playwright install chromium`.
- **Reset everything**: delete `data/jobs.db` (the `data/` directory is local state, safe to remove; it's recreated on next run).

## Running tests

```bash
.venv/bin/python -m pytest
```
