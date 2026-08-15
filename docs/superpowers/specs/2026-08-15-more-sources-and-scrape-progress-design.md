# More Sources + Scrape Progress Bar — Design

**Date:** 2026-08-15
**Status:** Approved
**Purpose:** Expand the number of working job sources (with Camoufox fallback for blocked ones) and add a dashboard "Scrape" button backed by a live, per-source progress bar.

## Goals

- Add six new sources that were verified reachable (three JSON APIs, three server-side HTML sites), bringing the total working source count from 3 to 9.
- For any source that fails a lightweight `requests` fetch, fall back to Playwright, then Camoufox (existing `fetch_with_fallback`).
- Give the dashboard a "Scrape" button that shows real-time per-source progress and auto-refreshes jobs/status when the run finishes.
- Keep every source independent: a blocked source never stops the others.

## New Sources

| Source | Name | Type | Endpoint | Notes |
|---|---|---|---|---|
| RemoteOK | `remoteok` | JSON API | `https://remoteok.com/api` | tags field; pay may be absent |
| Remotive | `remotive` | JSON API | `https://remotive.com/api/remote-jobs?search={term}` | filter to relevant categories |
| Working Nomads | `workingnomads` | JSON API | `https://www.workingnomads.com/api/exposed_jobs/` | tags include category |
| RemoteAfrica | `remoteafrica` | HTML | `https://remote4africa.com/` | Africa-focused; `/jobs/{slug}` links; filter to remote-capable titles |
| NodeSk | `nodesk` | HTML | `https://nodesk.co/remote-jobs/` | `/remote-jobs/{slug}` links |
| Freelancer | `freelancer` | HTML | `https://www.freelancer.com/jobs/data-entry/` | paginated project cards |

The three JSON APIs return clean structured data with no scraping. The three HTML sites render job listings server-side and are parseable with BeautifulSoup. All are reachable with plain `requests` today; if any regress, `fetch_with_fallback` upgrades to Playwright → Camoufox automatically.

## Architecture

```
scrapers/
  apis.py        # NEW: RemoteOK, Remotive, WorkingNomads (JSON)
  freelance.py   # NEW: Freelancer projects
  aggregators.py # ADD: RemoteAfrica, NodeSk (existing file)
  state.py       # NEW: module-level ScrapeState for live progress
  registry.py    # EDIT: run_all updates ScrapeState per source
dashboard/
  main.py        # EDIT: /api/scrape/status endpoint
  static/        # EDIT: Scrape button + progress bar UI
```

### ScrapeState (scrapers/state.py)

Module-level singleton holding:

```python
@dataclass
class SourceProgress:
    source: str
    status: str          # "pending" | "running" | "success" | "error"
    count_found: int
    error: str | None

@dataclass
class ScrapeState:
    running: bool
    started_at: str | None
    finished_at: str | None
    total_sources: int
    completed: int
    sources: list[SourceProgress]
```

- `registry.run_all` calls `state.begin(sources)` before the loop, `state.start_source(name)`/`state.finish_source(name, result)` per source, and `state.end()` after.
- `scrape.py` CLI calls `state.begin()` too (harmless; the dashboard reads the same state).
- The state object is guarded by a `threading.Lock`.

### API

- `GET /api/scrape/status` → serialized `ScrapeState`.
- `POST /api/refresh` → resets state, marks running, starts the background thread (existing pattern).

### Frontend

- Rename "Refresh now" → **"Scrape"**.
- While a scrape runs, the button is replaced/overlaid by a progress bar: one row per source with status chip (pending/running/done/error) and a bar that fills as `completed/total_sources` advances.
- Poll `/api/scrape/status` every 1s while running; when `running` flips false, stop polling and reload jobs + source status.
- `pollStatus` interval (10s) stays for normal refreshes.

## Camoufox fallback

The existing `fetch_with_fallback(url)` (requests → Playwright → Camoufox) is used by all new HTML scrapers. The JSON-API scrapers use plain `fetch` (a 403/block page raises `ScraperError`). No new anti-bot code is introduced.

## Testing

- Unit tests in `tests/test_parsers.py` for each new `_parse`: RemoteOK/Remotive/WorkingNomads parse a JSON fixture into the normalized job dict; RemoteAfrica/NodeSk/Freelancer parse a static HTML fixture.
- Integration test in `tests/test_api.py` for `GET /api/scrape/status` returning the expected shape.
- All 23 existing tests continue to pass.

## Files

- NEW: `scrapers/apis.py`, `scrapers/freelance.py`, `scrapers/state.py`
- EDIT: `scrapers/aggregators.py`, `scrapers/registry.py`, `scrape.py`, `dashboard/main.py`, `dashboard/static/index.html`, `dashboard/static/app.js`, `dashboard/static/style.css`, `tests/test_parsers.py`, `tests/test_api.py`, `README.md`
