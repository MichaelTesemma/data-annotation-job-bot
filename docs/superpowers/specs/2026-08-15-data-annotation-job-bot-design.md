# Data Annotation Job Bot — Design

**Date:** 2026-08-15
**Status:** Approved
**Purpose:** Personal tool for finding data annotation jobs. Crawls dedicated AI/data platforms, general job boards, and remote job aggregators; stores results locally; serves an interactive local web dashboard. Ranks Ethiopia-accessible opportunities higher without dropping anything.

## Goals

- Find data annotation jobs across three source categories: dedicated AI/data platforms, general job boards, and remote job aggregators.
- Store every listing found locally — nothing is dropped.
- Rank jobs/platforms that can be accessed from Ethiopia higher, so they appear on top; still keep everything for later sorting.
- Provide a local web dashboard to browse, sort, filter, search, and mark progress (applied/notes).
- Run manually on demand, but make scheduled/automated runs easy to enable later.

## Non-Goals

- No automated application or account signup.
- No login-based scraping of behind-auth portals (e.g., scraping inside Outlier's authenticated dashboard). Dedicated platforms are tracked as reference entries only.
- No cloud deployment or shared multi-user access.
- No aggressive scraping or CAPTCHA/anti-bot bypass. Politely crawl what is publicly available; gracefully skip what blocks us.

## Architecture

Scrapers + FastAPI server + SQLite dashboard. All local.

```
scrapers/          # one module per source
  base.py          # shared fetch/parse helpers, robots-aware, throttling
  platforms.py     # DataAnnotation.tech, Outlier, Scale AI, Remotasks, Appen...
  jobboards.py     # Indeed, LinkedIn, WeWorkRemotely, Remote.co, Wellfound...
dashboard/         # FastAPI app
  main.py          # serves web UI + /api routes + refresh endpoint
  static/          # HTML/CSS/JS dashboard
db.py              # SQLite schema + write/read helpers
rank.py            # Ethiopia-accessibility scoring
scrape.py          # CLI entry: `python scrape.py` crawls all sources
scheduler.py       # optional scheduled runs (off by default)
run_dashboard.py   # CLI entry: starts the local server
```

### Data flow

1. Each scraper fetches its source, parses listings, normalizes them into a common shape, and upserts into SQLite (dedup by URL).
2. The dashboard reads from SQLite.
3. A "Refresh" button triggers re-crawling of all sources via the API.
4. Scrapers run independently; one failing source never blocks the others (errors logged, partial results kept).

## Data model

Single `jobs` table:

| Column | Type | Notes |
|---|---|---|
| `id` | integer | PK |
| `title` | text | |
| `company` | text | company or platform name |
| `source` | text | which site it came from |
| `url` | text | unique per listing; dedup key |
| `description` | text | truncated/full description |
| `location` | text | free text |
| `remote` | bool | is it remote |
| `pay` | text | often unstructured, kept as text |
| `posted_at` | text | original post date if available |
| `discovered_at` | text | when we first found it |
| `access_score` | real | Ethiopia-accessibility score 0..1 |
| `overall_score` | real | composite desirability score |
| `applied` | bool | user progress flag, default false |
| `notes` | text | user notes |

Plus a `platforms` table for dedicated portals (DataAnnotation, Outlier, Scale AI, Remotasks, Appen, etc.). These are signup gateways rather than job listing feeds, so they are tracked as reference entries with fields: `name`, `url`, `ethiopia_accessible` (bool), `status` (e.g., applied / pending / not_applied), `notes`.

## Sources

### Dedicated platforms (reference entries, not scraped listings)
DataAnnotation.tech, Outlier, Scale AI, Remotasks, Appen, Clickworker, Toloka, Mercor, Invisible, Alignerr, Prolific.

### Job boards (scraped)
- Indeed — best-effort; heavy anti-bot. Fall back to Playwright if lightweight parser fails.
- LinkedIn — best-effort; heavy anti-bot. Fall back to Playwright if lightweight parser fails.
- WeWorkRemotely — scrapeable.
- Remote.co — scrapeable.
- Wellfound (formerly AngelList) — best-effort.

Search terms: "data annotation", "data labeling", "AI training", "AI tutor", "RLHF", "data analyst (annotation)".

## Ethiopia ranking

`rank.py` computes two scores per job, 0..1:

- **access_score** — how likely a person in Ethiopia can actually use this. Signals:
  - Platform reputation and known Ethiopia-accessible status (highest weight, e.g., Remotasks/Toloka/Mercor/Clickworker are commonly accessible from Ethiopia).
  - Listing language: "global", "worldwide", "remote anywhere" → high; explicit region restrictions (e.g., "US only", "EU only") → low.
- **overall_score** — composite of access_score plus desirability signals (remote-friendly, pay mention, platform reputation).

**Nothing is dropped.** Every job appears in the dashboard, sorted by score (high-access first). A filter lets the user hide low-access listings if desired.

## Dashboard

Local FastAPI server serving:
- Table of all jobs with columns: title, company, source, remote, pay, access score, overall score, applied.
- Sort by any column; filter by source, remote-only, score thresholds, applied state; text search.
- "Refresh now" button triggering a re-crawl.
- Per-source status panel: last run time, success/error state, count found.
- Platforms panel listing dedicated portals and their Ethiopia-accessibility/status.
- Apply/notes editing for each job.

## Error handling & reliability

- Per-source try/except; a failure logs and continues with the rest.
- Polite crawling: respect `robots.txt`, rate-limit requests, browser-like headers, minimal concurrency.
- Scrape-blocked sites: try lightweight parser → fall back to Playwright → if both fail, log and move on.
- Dashboard exposes per-source status so the user knows what is actually working.

## Testing

- Unit tests for parser/normalization (sample HTML in, clean structured output asserted).
- Unit tests for ranking logic.
- A fake-source integration test running the full pipeline against a local stub server.
- FastAPI endpoint tests for the dashboard API.

## Scheduling

Default: manual `python scrape.py`. `scheduler.py` with `schedule` support (e.g., every 4 hours) included but off by default, enabling automated refresh later without new architecture.

## Out of scope / future

- Notifications (email/Discord/Telegram alerts) — could be added later.
- Cloud deployment — could be added later.
- Application automation.
