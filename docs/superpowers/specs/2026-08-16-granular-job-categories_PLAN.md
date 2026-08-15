# Implementation Plan: Granular Job Categories

Refactor of the data-annotation job bot to derive search terms, dashboard
filtering, and relevance includes from a single `CATEGORIES` source of truth,
expanding from 2 to 10 low-barrier online job categories.

Stack: Python 3.13, FastAPI + SQLite, BeautifulSoup scrapers, pytest.

## Step 1: Single-source `categories.py`

- [ ] **`categories.py`** — Replace `CATEGORY_KEYWORDS` with `CATEGORIES: dict[str, CategorySpec]`
  plus a frozen `CategorySpec` dataclass (`search_terms`, `filter_keywords`).
  Define all 10 categories with the terms/keywords from the spec table
  (data annotation, ai training, content moderation, data entry, data collection,
  usability testing, online research, micro task, user interviews, translation).
  Keep `categories()` and `category_keywords()` signatures; add
  `category_search_terms()`, `all_search_terms()`, `all_filter_keywords()`.
- [ ] Verify: `python -c "import categories; print(categories.categories()); print(len(categories.all_search_terms()))"`
  → 10 sorted names, ~30 terms.

## Step 2: Derive `config.py` search terms

- [ ] **`config.py`** — Change `Settings.all_search_terms` to return
  `categories.all_search_terms()` (single source of truth). Keep the dataclass
  fields for local-override compat: if `search_terms`/`translation_search_terms`
  are overridden non-empty in `config.local.py`, merge them into the union
  (dedupe, preserve order).
- [ ] Verify: `python -c "from config import SETTINGS; print(len(SETTINGS.all_search_terms))"` → ~30.

## Step 3: Derive `relevance.py` includes

- [ ] **`relevance.py`** — Set `INCLUDE_KEYWORDS = all_filter_keywords()` from
  `categories`. Remove `micro task` from `EXCLUDE_KEYWORDS` (no longer a block;
  Freelancer VA leak stays covered by `virtual assistant`/`administrative assistant`/`on-site`).
  Keep `is_relevant()` unchanged.
- [ ] Verify: `python -c "from relevance import is_relevant; print(is_relevant('MTurk survey taker','take surveys')); print(is_relevant('Sales Manager','sell'))"`
  → True, False.

## Step 4: Update tests

- [ ] **`tests/test_relevance.py`** — Add cases for new categories (usability
  testing, micro-task/survey, user interview/respondent, content moderation,
  online research). Ensure `is_relevant("Micro task specialist", ...)` now passes.
- [ ] **`tests/test_categories.py`** (new) — Assert `all_search_terms()`/`all_filter_keywords()`
  are unions, `category_keywords()` non-empty per category, `translation` still present.
- [ ] Verify: `pytest -q` → all pass.

## Step 5: Re-scrape and verify

- [ ] Drop `data/jobs.db` (not the `data/` package), re-seed platforms, run
  `python scrape.py` with the new ~30-term config.
- [ ] Verify per-source counts, translation category count, and no off-topic
  jobs leak in (spot-check titles).
- [ ] Verify dashboard `/api/categories` returns 10 names and `/api/jobs?category=...`
  filters work.

## Step 6: Commit

- [ ] Commit all changes and push to `origin/main`.

## Progress

| Step | Files | Status |
|------|-------|--------|
| 1. categories.py | categories.py | ☐ |
| 2. config.py | config.py | ☐ |
| 3. relevance.py | relevance.py | ☐ |
| 4. tests | tests/test_relevance.py, tests/test_categories.py | ☐ |
| 5. re-scrape | data/jobs.db (regenerated) | ☐ |
| 6. commit | git | ☐ |
