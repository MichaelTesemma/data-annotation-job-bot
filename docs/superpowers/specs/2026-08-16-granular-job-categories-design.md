# Granular Job Categories with Single Source of Truth

Date: 2026-08-16

## Goal

Expand the job bot from 2 dashboard categories (`data annotation`, `translation`)
to a granular set of 10 low-barrier online job categories. Each category gains its
own search terms (so scrapers actively fetch those jobs) and filter keywords
(so the dashboard can filter on them). The category definitions become the single
source of truth for search terms, dashboard filtering, and relevance includes.

## Current State

- `categories.py` holds `CATEGORY_KEYWORDS: dict[str, list[str]]` with 2 entries.
  `categories()` returns sorted keys; `category_keywords(category)` returns the list.
- `config.py` holds two static lists: `search_terms` (6 annotation terms) and
  `translation_search_terms` (4 Amharic terms). `Settings.all_search_terms`
  concatenates them (10 terms total).
- Scrapers iterate `SETTINGS.all_search_terms` (aggregators.py:18, apis.py:55,
  jobboards.py:18, jobboards.py:73) to build per-term queries.
- `relevance.py` has a hand-maintained `INCLUDE_KEYWORDS` list (46 entries) used
  by `is_relevant(title, description)` inside `BaseScraper.run()`. `EXCLUDE_KEYWORDS`
  (83 entries) are title-only hard blocks.
- `db.get_jobs` filters by `category` using `category_keywords()`.
- `dashboard/main.py` exposes `/api/categories` and `/api/jobs?category=`.

## Design

### New `categories.py`

Replace `CATEGORY_KEYWORDS` with a `CATEGORIES` dict whose values carry both
search terms and filter keywords:

```python
CATEGORIES: dict[str, CategorySpec] = {
    "data annotation": CategorySpec(
        search_terms=["data annotation", "data labeling", "annotation", "labeling"],
        filter_keywords=["annotat", "data label", "labeler", "tagger"],
    ),
    ...
}
```

`CategorySpec` is a small dataclass:

```python
@dataclass(frozen=True)
class CategorySpec:
    search_terms: list[str]
    filter_keywords: list[str]
```

Helper functions:

- `categories() -> list[str]` — sorted keys (unchanged signature).
- `category_keywords(category) -> list[str]` — returns `filter_keywords` (unchanged signature).
- `category_search_terms(category) -> list[str]` — returns `search_terms` (new).
- `all_search_terms() -> list[str]` — union of every category's `search_terms` (new).
- `all_filter_keywords() -> list[str]` — union of every category's `filter_keywords` (new).

### The 10 categories

| Category | search_terms | filter_keywords |
|---|---|---|
| data annotation | data annotation, data labeling, annotation, labeling | annotat, data label, labeler, tagger |
| ai training | AI training, AI tutor, prompt engineer, RLHF | ai trainer, ai tutor, ai teacher, prompt, rlhf, model training, ai training |
| content moderation | content moderation, content reviewer | content moderation, content review, content reviewer, content moderator |
| data entry | data entry, data entry clerk | data entry, data entr, data clerk |
| data collection | data collection, search evaluator, online data analyst | data collection, search evaluator, search evaluation, rater, online data analyst |
| usability testing | usability testing, user testing, website testing | usability, user testing, usertesting, userlytics, website testing, app testing |
| online research | web research, online research, research assistant | web research, online research, research assistant, researcher |
| micro task | micro task, microtasks, online surveys, survey | micro task, mturk, prolific, clickworker, survey |
| user interviews | user interviews, research panel, respondent | user interview, respondent, panel, participant |
| translation | amharic translation, amharic english, english amharic translator, amharic to english | amharic, translat, translator, english to amharic, amharic to english, interpreter, አማርኛ, language specialist |

### New `config.py`

- Remove `DEFAULT_SEARCH_TERMS` and `TRANSLATION_SEARCH_TERMS` static lists.
- Keep `Settings.search_terms` and `Settings.translation_search_terms` as
  overridable dataclass fields for backwards compatibility / local overrides, but
  change `all_search_terms` to fall back to `categories.all_search_terms()` when
  the fields are empty; when overridden, use the explicit lists.
- Simplest correct behavior: `all_search_terms` returns
  `categories.all_search_terms()` (source of truth), with no override path
  needed for the default flow. Local overrides via `config.local.py` can still
  set `search_terms`/`translation_search_terms`, which merge into the union.

### New `relevance.py`

- Replace the hand-maintained `INCLUDE_KEYWORDS` literal with
  `from categories import all_filter_keywords` and set
  `INCLUDE_KEYWORDS = all_filter_keywords()`.
- `EXCLUDE_KEYWORDS` stays as-is, except reconcile the earlier noise-blocking
  entries that conflict with the new categories:
  - `micro task` is currently an EXCLUDE (added to kill Freelancer VA gigs).
    It must be removed from EXCLUDE so real micro-task/survey platform jobs pass.
    The Freelancer VA leak is better handled by the `virtual assistant` /
    `administrative assistant` / `on-site` excludes that remain.
- `is_relevant()` logic unchanged.

### No changes needed

- `db.py` — already uses `category_keywords()`.
- `dashboard/main.py` — already uses `categories()`.
- Tests: update `tests/test_relevance.py` expectations if keyword membership
  changes; `test_api.py` category test still valid (categories still include
  `data annotation` and `translation`).

## Scrape Impact

Search terms grow from ~10 to ~30. Each source performs one request per term
(rate-limited by `Settings.rate_limit_seconds`), so total scrape time roughly
triples. LinkedIn (Camoufox, slow) dominates. Mitigation: term lists are kept
lean (2-4 terms per category), and LinkedIn's own filter dedups.

## Testing

- Unit tests for `all_search_terms()` and `all_filter_keywords()` union behavior.
- Unit tests that each category's `category_keywords()` returns non-empty lists.
- `relevance.is_relevant` still keeps annotation/translation/data jobs and
  blocks sales/nursing/machinist/etc.
- Full suite (`pytest`) passes.

## Open Questions

- Whether to bump `rate_limit_seconds` given more requests — deferred; measure
  first scrape time after the change.
