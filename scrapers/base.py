import json
import logging
import re
import subprocess
import time
import urllib.robotparser
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

import db
import rank
from config import SETTINGS

logger = logging.getLogger("scrapers")

_ROBOTS_CACHE: dict[str, bool | None] = {}


class ScraperError(Exception):
    pass


def robots_allows(url: str) -> bool:
    if not SETTINGS.robots_enabled:
        return True
    parsed = urlparse(url)
    cache_key = f"{parsed.scheme}://{parsed.netloc}"
    if cache_key in _ROBOTS_CACHE:
        return _ROBOTS_CACHE[cache_key] is True
    robots_url = f"{cache_key}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        allowed = rp.can_fetch(SETTINGS.user_agent, url)
    except Exception:
        allowed = True
    _ROBOTS_CACHE[cache_key] = allowed
    return allowed


def fetch(url: str, use_playwright: bool = False) -> str:
    if not robots_allows(url):
        logger.info("Blocked by robots.txt: %s", url)
        raise ScraperError(f"robots.txt disallows {url}")

    if use_playwright:
        return _fetch_playwright(url)

    headers = {"User-Agent": SETTINGS.user_agent, "Accept-Language": "en-US,en;q=0.9"}
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            time.sleep(SETTINGS.rate_limit_seconds)
            resp = requests.get(url, headers=headers, timeout=SETTINGS.request_timeout_seconds)
            resp.raise_for_status()
            return resp.text
        except Exception as exc:
            last_error = exc
            logger.warning("Attempt %d failed for %s: %s", attempt + 1, url, exc)
    raise ScraperError(f"failed to fetch {url}: {last_error}")


def _fetch_playwright(url: str) -> str:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise ScraperError("playwright not installed; run `playwright install`") from exc

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page(user_agent=SETTINGS.user_agent)
                page.goto(url, timeout=SETTINGS.request_timeout_seconds * 1000, wait_until="domcontentloaded")
                page.wait_for_timeout(3000)
                return page.content()
            finally:
                browser.close()
    except ScraperError:
        raise
    except Exception as exc:
        raise ScraperError(f"playwright failed for {url}: {exc}") from exc


def fetch_camoufox(url: str) -> str:
    """Fetch a page through the camofox CLI (anti-detection Firefox)."""
    try:
        opened = _camoufox_cli(["open", url])
        tab_id = opened.get("tabId")
    except ScraperError:
        raise
    if not tab_id:
        raise ScraperError(f"camofox open returned no tab for {url}")

    try:
        time.sleep(SETTINGS.camoufox_wait_seconds)
        result = _camoufox_cli(["eval", "document.documentElement.outerHTML"])
        html = result.get("result", "")
        if not html:
            raise ScraperError(f"camofox eval returned empty content for {url}")
        return html
    finally:
        try:
            _camoufox_cli(["close", tab_id])
        except ScraperError:
            logger.warning("camofox close failed for tab %s", tab_id)


def _camoufox_cli(args: list[str]) -> dict:
    try:
        proc = subprocess.run(
            ["camofox", "--format", "json", *args],
            capture_output=True,
            text=True,
            timeout=SETTINGS.camoufox_timeout_seconds,
        )
    except FileNotFoundError as exc:
        raise ScraperError("camofox CLI not found on PATH") from exc
    except subprocess.TimeoutExpired as exc:
        raise ScraperError(f"camofox timed out: {' '.join(args[:2])}") from exc
    if proc.returncode != 0:
        raise ScraperError(f"camofox failed ({proc.returncode}): {proc.stderr.strip() or proc.stdout.strip()}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise ScraperError(f"camofox returned non-JSON output: {proc.stdout[:200]}") from exc


def fetch_with_fallback(url: str) -> str:
    """Try lightweight requests, then Playwright, then Camoufox."""
    errors: list[str] = []
    try:
        return fetch(url)
    except ScraperError as exc:
        errors.append(str(exc))
    try:
        return _fetch_playwright(url)
    except ScraperError as exc:
        errors.append(str(exc))
    return fetch_camoufox(url)


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def get_text(soup: BeautifulSoup, selector: str) -> str:
    node = soup.select_one(selector)
    return clean_text(node.get_text(" ", strip=True)) if node else ""


def normalize_job(**kwargs) -> dict:
    return {
        "title": kwargs.get("title", ""),
        "company": kwargs.get("company", ""),
        "source": kwargs.get("source", ""),
        "url": kwargs.get("url", ""),
        "description": kwargs.get("description", ""),
        "location": kwargs.get("location", ""),
        "remote": bool(kwargs.get("remote")),
        "pay": kwargs.get("pay", ""),
        "posted_at": kwargs.get("posted_at", ""),
        "discovered_at": kwargs.get("discovered_at", ""),
        "access_score": 0.0,
        "overall_score": 0.0,
        "applied": False,
        "notes": "",
    }


class BaseScraper:
    name = "base"

    def fetch_jobs(self) -> list[dict]:
        raise NotImplementedError

    def run(self) -> dict:
        started = time.time()
        try:
            jobs = self.fetch_jobs()
            count = 0
            for raw_job in jobs:
                job = normalize_job(**{**raw_job, "source": self.name})
                job = rank.score_job(job)
                db.upsert_job(job)
                count += 1
            db.record_source_run(self.name, "success", count)
            logger.info("%s: %d jobs", self.name, count)
            return {"source": self.name, "status": "success", "count_found": count, "elapsed": round(time.time() - started, 2)}
        except Exception as exc:
            db.record_source_run(self.name, "error", 0, str(exc))
            logger.error("%s failed: %s", self.name, exc)
            return {"source": self.name, "status": "error", "count_found": 0, "error": str(exc)}
