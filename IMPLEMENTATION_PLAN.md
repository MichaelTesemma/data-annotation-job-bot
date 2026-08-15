# Data Annotation Job Bot — Implementation Plan

**Source spec:** `docs/superpowers/specs/2026-08-15-data-annotation-job-bot-design.md`
**Stack:** Python 3.11+, SQLite, FastAPI, requests + BeautifulSoup4, Playwright (fallback), pytest. All local.

This plan builds the job bot in dependency order: scaffold → database → ranking → scrapers → CLI → dashboard → scheduling → tests. Every file traces to the approved spec.

---

## Step 1: Scaffold + Config

Creates the project shell, dependency management, and shared configuration.

- [ ] **`pyproject.toml`** — Declare project metadata, Python `>=3.11`, dependencies: `fastapi`, `uvicorn`, `requests`, `beautifulsoup4`, `python-robots`, `playwright`, `schedule`, `pytest`, `httpx` (for tests). Configure pytest test paths. `pip install -e .[dev]` installs everything.
- [ ] **`config.py`** — Define `SEARCH_TERMS` list (from spec: "data annotation", "data labeling", "AI training", "AI tutor", "RLHF", "data analyst (annotation)"), `RATE_LIMIT_SECONDS` (default 2.0), `USER_AGENT` (a real browser UA), `DB_PATH` (default `data/jobs.db`), and `SCHEDULER_INTERVAL_HOURS` (default 4). Load overrides from `config.local.py` if present (gitignored). Export a singleton `SETTINGS`.
- [ ] **`.gitignore`** — Ignore `data/`, `__pycache__/`, `*.pyc`, `.venv/`, `config.local.py`, `node_modules/` (Playwright browser cache not needed here).

**Verify:** `python -c "import config"` runs; `pip install -e .[dev]` completes; `git status` shows `data/` ignored.

## Step 2: Database Schema + Helpers

- [ ] **`db.py`** — Open SQLite at `SETTINGS.DB_PATH`, create parent dir, enable WAL and foreign keys. `init_db()` creates tables:
  - `jobs` — columns exactly per spec data model (id PK, title, company, source, url, description, location, remote, pay, posted_at, discovered_at, access_score, overall_score, applied, notes).
  - `platforms` — name, url, ethiopia_accessible, status, notes.
  - `source_runs` — source, started_at, finished_at, status, count_found, error (for the dashboard's per-source status panel).
- [ ] **`db.py`** (same module) — CRUD helpers: `upsert_job(job)` keyed on unique `url` (keeps first `discovered_at`), `get_jobs(filters, sort, search)`, `update_job(id, fields)`, `list_platforms()`, `update_platform(fields)`, `record_source_run(...)`, `get_source_status()`.
- [ ] **`data/seed_platforms.py`** — Seed the `platforms` table with the 11 portals from the spec (DataAnnotation.tech, Outlier, Scale AI, Remotasks, Appen, Clickworker, Toloka, Mercor, Invisible, Alignerr, Prolific), each with url, a sensible default `ethiopia_accessible` value, and `status='not_applied'`.

**Verify:** `python -c "import db; db.init_db()"` creates `data/jobs.db`; a seeded query returns the 11 platforms; upserting the same URL twice does not duplicate.

## Step 3: Ranking Logic

- [ ] **`rank.py`** — Pure functions (no I/O):
  - `access_score(platform, location_text, remote, description)` → float 0..1. Signals per spec: platform reputation map (Remotasks/Toloka/Mercor/Clickworker high) has the most weight; "global"/"worldwide"/"remote anywhere" keywords raise; explicit region restrictions ("US only", "EU only", "UK only", "US-based") lower.
  - `overall_score(access, remote, pay_text, description)` → float 0..1, composite of access + remote-friendliness + pay mention + description length (proxy for real listing).
  - `PLATFORM_ACCESS` module-level dict of platform → base access weight, shared with the scrapers.
- [ ] **`rank.py`** — `score_job(job_dict, platform)` convenience that fills `access_score` and `overall_score` into the job dict.

**Verify:** `python -c` snippet scoring a US-only job vs. a global Remotasks job gives higher scores to the global one; unit tests in Step 8 confirm.

## Step 4: Scraper Foundation

- [ ] **`scrapers/__init__.py`** — Empty package marker; also exports `ALL_SOURCES` list for discovery (populated as scrapers register).
- [ ] **`scrapers/base.py`** — Shared infrastructure:
  - `fetch(url, use_playwright=False)` — requests with `SETTINGS.USER_AGENT`, retries (2), timeout, respects `robots.txt` via `python-robots` (skip + log if disallowed), and rate-limits using `SETTINGS.RATE_LIMIT_SECONDS`. When `use_playwright=True`, falls back to a headless-Chromium fetch.
  - `parse` helper utilities: `clean_text()`, `extract_jobs_from_html(html, selectors, transformer)`.
  - `ScraperError` exception type; `normalize_job()` that produces the spec's canonical job dict with defaults for missing fields.
  - `class BaseScraper` — abstract with `name`, `fetch_jobs() -> list[job]`, and a concrete `run()` that calls `fetch_jobs()`, scores each job via `rank.score_job`, upserts via `db.upsert_job`, records a `source_runs` entry, and catches per-run exceptions so a failure never propagates to other scrapers.
- [ ] **`scrapers/registry.py`** — Maintains `SOURCE_REGISTRY` mapping source name → scraper class; `run_all()` executes each registered scraper in its own try/except and returns per-source results.

**Verify:** A stub scraper registered in the registry runs through `run_all()` without crashing and writes a `source_runs` row.

## Step 5: Platform + Aggregator Scrapers

Easy, scrapeable sources first. Each module defines one or more `BaseScraper` subclasses and registers them.

- [ ] **`scrapers/aggregators.py`** — Scrapers for:
  - `WeWorkRemotely` — parse the "Remote AI / ML" and general listings pages; extract title, company, location/remote, description, pay, url, posted date. Simple HTML, no auth.
  - `Remote.co` — parse remote data-entry / AI-training listings similarly.
- [ ] **`scrapers/jobboards.py`** — Scrapers for the harder boards:
  - `Indeed` — best-effort: query for each search term; try lightweight parser first, transparently fall back to Playwright (`fetch(..., use_playwright=True)`); on failure, log and return empty list (no crash).
  - `LinkedIn` — best-effort, same fallback pattern as Indeed.
  - `Wellfound` — best-effort, same fallback pattern.
  - These iterate `SETTINGS.SEARCH_TERMS`, cap results per term (e.g., 50) to stay polite.

**Verify:** Running `python scrape.py --source wwremotely` (once Step 7 exists) or a direct unit run returns listings and upserts them with scores. Aggregators work reliably; boards may return zero — that's expected and logged, not fatal.

## Step 6: CLI Entry Point

- [ ] **`scrape.py`** — CLI using `argparse`: `python scrape.py` runs all sources; `--source NAME` runs one; `--seed-platforms` seeds the `platforms` table; `--no-verify` skips robots check for a single explicit run (off by default). Prints a per-source summary table (source, status, count) to stdout after `run_all()`.

**Verify:** `python scrape.py --source aggregator` runs only that source and prints a summary; `python scrape.py` runs everything.

## Step 7: Dashboard Backend (FastAPI)

- [ ] **`dashboard/__init__.py`** — Package marker.
- [ ] **`dashboard/main.py`** — FastAPI app:
  - `GET /` → serves the static dashboard HTML.
  - `GET /api/jobs` → query params `sort`, `source`, `remote_only`, `min_access`, `applied`, `search` → `db.get_jobs(...)`; returns JSON.
  - `PATCH /api/jobs/{id}` → update `applied` / `notes`.
  - `GET /api/platforms` → list platforms; `PATCH /api/platforms/{name}` → update `status` / `notes`.
  - `GET /api/source-status` → per-source `source_runs` summary.
  - `POST /api/refresh` → runs `scrapers.registry.run_all()` in a background thread, returns immediately with `{"started": true}`; status viewable via `/api/source-status`.
  - Mount `dashboard/static/` for the frontend assets.
- [ ] **`run_dashboard.py`** — CLI: `python run_dashboard.py` starts uvicorn on `127.0.0.1:8000` (port configurable via `--port`).

**Verify:** `python run_dashboard.py` serves `GET /api/jobs` returning seeded jobs; `POST /api/refresh` triggers a crawl and `GET /api/source-status` shows progress.

## Step 8: Dashboard Frontend

- [ ] **`dashboard/static/index.html`** — Single page layout: jobs table, filter bar (source, remote-only, min-access slider, applied toggle, search box), sortable column headers, a "Refresh now" button, a per-source status panel, and a platforms panel.
- [ ] **`dashboard/static/style.css`** — Clean, minimal, local-first styling; no external CDNs (works offline). Score shown as a small badge, color-coded by value.
- [ ] **`dashboard/static/app.js`** — Fetch `/api/jobs` with current filters, render rows, column sort, client-side interactions for applying filters and marking jobs applied / editing notes (PATCH), "Refresh now" → `POST /api/refresh` + polls `/api/source-status` until done, renders both status panel and platforms panel.

**Verify:** Open `http://127.0.0.1:8000/` — sort/filter/search work, refresh updates the table, platforms panel editable.

## Step 9: Scheduling

- [ ] **`scheduler.py`** — Optional loop using `schedule` lib: runs `run_all()` every `SETTINGS.SCHEDULER_INTERVAL_HOURS`. Off by default; only active when invoked as `python scheduler.py`. Guard so it exits cleanly on Ctrl+C.

**Verify:** `python scheduler.py --interval 1` (test override) runs `run_all()` on the hour without error; default runs only when explicitly started.

## Step 10: Tests

- [ ] **`tests/test_rank.py`** — Unit tests for `access_score` / `overall_score`: US-only vs global ordering, platform reputation weights, remote keyword effects, region-restriction penalties, range bounds 0..1.
- [ ] **`tests/test_parsers.py`** — Feed sample HTML fixtures (in-memory strings) for WeWorkRemotely and Remote.co through their parsers; assert clean normalized jobs (title, url, remote flag, pay extraction). Assert dedup via `upsert_job` keyed on URL.
- [ ] **`tests/test_integration.py`** — Fake-source test: spin a local stub HTTP server (httpx/`http.server`) serving sample listings, register a stub scraper pointing at it, run the pipeline, assert jobs land in SQLite with scores, and a failing stub source does not block the others.
- [ ] **`tests/test_api.py`** — FastAPI `TestClient`: `GET /api/jobs` with filters, `PATCH /api/jobs/{id}`, `GET /api/source-status`, `POST /api/refresh`.
- [ ] **`tests/conftest.py`** — Fixtures: temp SQLite DB (monkeypatched `SETTINGS.DB_PATH`), seeded platforms, a registered stub scraper.

**Verify:** `pytest` passes with all tests green.

## Step 11: Productionize + Docs

- [ ] **`README.md`** — Setup (install, Playwright browser install command), usage (`python scrape.py`, `python run_dashboard.py`, `python scheduler.py`), project layout, troubleshooting (blocked sources, robots). 
- [ ] **`data/README.md`** — Notes that `data/` is gitignored local state and can be deleted to reset.
- [ ] **`.gitignore`** final check — confirm `data/` and `config.local.py` are ignored before first real run.

**Verify:** A fresh checkout with `pip install -e .[dev]`, `python scrape.py --seed-platforms`, `python scrape.py`, then `python run_dashboard.py` works end-to-end per the README.

---

## Progress Summary

| Step | Contents | Files |
|---|---|---|
| 1 | Scaffold + Config | 3 |
| 2 | Database Schema + Helpers | 2 |
| 3 | Ranking Logic | 1 |
| 4 | Scraper Foundation | 3 |
| 5 | Platform + Aggregator Scrapers | 2 |
| 6 | CLI Entry Point | 1 |
| 7 | Dashboard Backend (FastAPI) | 3 |
| 8 | Dashboard Frontend | 3 |
| 9 | Scheduling | 1 |
| 10 | Tests | 5 |
| 11 | Productionize + Docs | 2 |
| **Total** | | **26 files** |

## Key Decisions

- **Best-effort scraping, never fatal.** Indeed/LinkedIn/Wellfound can return zero results; that is logged as a source status and never blocks other sources (per spec Non-Goals).
- **Dedicated platforms are reference data**, not scraped listings — seeded in `platforms`, managed in the dashboard, never crawled (per spec).
- **One `jobs` table, URL-keyed dedup.** First `discovered_at` wins; refreshes update scores/descriptions without duplicating rows.
- **Ranking is additive, not filtering.** Nothing is dropped; access/overall scores only reorder and power the optional min-access filter (per spec).
- **Playwright is a fallback, not a default.** Lightweight requests-based parsing first; Playwright only for blocked boards, so the happy path has no browser dependency.
- **Scheduling off by default**, added without new architecture so it can be enabled later (per spec).
