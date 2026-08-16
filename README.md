# Data Annotation Job Bot

A personal tool that crawls the internet for data annotation jobs, ranks opportunities by how accessible they are from Ethiopia, and serves a local web dashboard to browse, filter, and track them.

## Features

- **Crawls three source types**: dedicated AI/data platforms (tracked as reference entries, tagged by category), general job boards (Indeed, LinkedIn, Wellfound), and remote job aggregators (WeWorkRemotely, Remote.co, RemoteOK, Remotive, Working Nomads, RemoteAfrica, NodeSk, Freelancer).
- **10 granular job categories** (`categories.py` is the single source of truth): data annotation, AI training, content moderation, data entry, data collection, usability testing, online research, micro-task, user interviews, and translation. Each category defines its own search terms (what the scrapers query), filter keywords (what the dashboard filters on), and the job boards and dedicated platform websites that best match it.
- **Ethiopia-first ranking**: every job is scored 0–1 for Ethiopia accessibility (`access_score`) and overall desirability (`overall_score`). Nothing is dropped — low-access listings just sort lower and can be filtered out.
- **Relevance gate**: before a job is stored it must match at least one category's keywords; clearly-unrelated professions (sales, nursing, trades, etc.) are filtered out. Every job in the database passes this gate.
- **Local dashboard**: sort, filter by source/category/remote/score/applied, search, mark jobs as applied, edit notes, hit "Scrape" to re-crawl with a live per-source progress bar, and hit "Export CSV" to download the currently filtered results as a spreadsheet. Selecting a category shows its recommended sources and filters the dedicated-platforms table to that category.
- **Resilient scraping**: each source runs independently; a blocked or failing source never stops the others. Per-source status is shown on the dashboard.
- **Polite by default**: respects `robots.txt`, rate-limits requests, and falls back to a real browser (Playwright, then Camoufox) only when a lightweight fetch is blocked.

## Setup

Requires Python 3.11+.

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"

# install the Playwright browser (needed for the blocked job boards)
.venv/bin/python -m playwright install chromium

# install the Camoufox anti-detection browser (last-resort fallback for hard-blocked sources like Remote.co)
npm install -g camofox-browser   # the camofox CLI
camoufox-js fetch                # download the Camoufox engine
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
  apis.py          RemoteOK, Remotive, Working Nomads (JSON APIs)
  aggregators.py   WeWorkRemotely, Remote.co, RemoteAfrica, NodeSk
  freelance.py     Freelancer projects
  jobboards.py     Indeed, LinkedIn, Wellfound (best-effort)
  registry.py      source discovery + run_all()
  state.py         live per-source scrape progress tracking
categories.py      single source of truth: category search terms + filter keywords + sources
relevance.py       relevance gate (include/exclude keywords) applied in BaseScraper
data/seed_platforms.py  dedicated platform websites per category
dashboard/         FastAPI app
  main.py          API routes + refresh endpoint + scrape status
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
search_terms = ["data annotation", "data labeling"]   # extra terms merged in
translation_search_terms = ["amharic translation", "amharic english"]
max_results_per_term = 100
robots_enabled = False  # not recommended
```

Search terms come from `categories.py` by default (every category's search terms). `search_terms`/`translation_search_terms` in `config.local.py` are merged on top, so all 10 categories are always searched unless you change the code.

## Categories

`categories.py` is the single source of truth for job categorization. Each category defines three things:

- `search_terms` — the queries each scraper runs (this is where `SETTINGS.all_search_terms` comes from).
- `filter_keywords` — substring terms matched against title/company/location/description for dashboard filtering; they also feed `relevance.py`'s include list, so a job must match at least one category to be stored.
- `sources` — the job boards and dedicated platform websites best suited to that category, shown in the dashboard when you select it.

The default categories: **data annotation**, **AI training**, **content moderation**, **data entry**, **data collection**, **usability testing**, **online research**, **micro-task**, **user interviews**, and **translation** (Amharic/English, interpreter, አማርኛ). The dedicated-platform table (`data/seed_platforms.py`) holds ~47 platform websites (Scale AI, Appen, Outlier, Turing, MTurk, Prolific, UserTesting, Welocalize, Gengo, etc.), each tagged with its category and filterable from the dashboard.

## Troubleshooting

- **Sources returning 0 / failing**: Indeed and Wellfound hit interactive Cloudflare CAPTCHAs that even a stealth browser can't pass; they stay at 0. LinkedIn works via Camoufox but occasionally shows an auth wall (the scraper retries once automatically). Remote.co, WeWorkRemotely, RemoteOK, Remotive, Working Nomads, RemoteAfrica, NodeSk, and Freelancer are the most reliable. The dashboard's "Source status" panel shows which sources work and why the others fail, and the "Scrape" button shows live per-source progress while a run is in flight.
- **Scrapes are slow**: the 10 categories produce ~30 search terms, and each term costs one request per source (LinkedIn paginates five pages per term via Camoufox), so a full run can take ~20+ minutes. Reduce `max_results_per_term` in `config.local.py` (e.g. to 20) or run only the sources you need with `scrape.py --source`.
- **Playwright not found**: run `.venv/bin/python -m playwright install chromium`.
- **Camofox CLI not found**: install it with `npm install -g camofox-browser` and make sure `~/.npm-global/bin` (or wherever npm installs global bins) is on your `PATH`.
- **Reset everything**: delete `data/jobs.db` (the `data/` directory is local state, safe to remove; it's recreated on next run).

## Running tests

```bash
.venv/bin/python -m pytest
```
