import re
from urllib.parse import parse_qs, urlencode, urljoin, urlparse

from bs4 import BeautifulSoup

from config import SETTINGS
from scrapers.base import BaseScraper, ScraperError, fetch, fetch_camoufox, fetch_with_fallback, clean_text
from scrapers.registry import register


class SearchBoardScraper(BaseScraper):
    search_url = ""
    card_selector = ""
    page_param = "start"

    def fetch_jobs(self) -> list[dict]:
        jobs: list[dict] = []
        for term in SETTINGS.all_search_terms:
            for start in range(0, SETTINGS.max_results_per_term, 10):
                url = self._search_url(term, start)
                html = fetch_with_fallback(url)
                page_jobs = self._parse(html, term)
                jobs.extend(page_jobs)
                if len(page_jobs) < 10:
                    break
        return jobs

    def _search_url(self, term: str, start: int) -> str:
        return self.search_url.format(term=term.replace(" ", "+"), start=start)

    def _parse(self, html: str, term: str) -> list[dict]:
        raise NotImplementedError


class IndeedScraper(SearchBoardScraper):
    name = "indeed"
    search_url = "https://www.indeed.com/jobs?q={term}&start={start}"

    def _parse(self, html: str, term: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        results: list[dict] = []
        for card in soup.select("div.job_seen_beacon, li.result"):
            link = card.select_one("a[href*='/rc/clk'], a[href*='/viewjob'], a.jcs-JobTitle")
            if link is None:
                continue
            href = link.get("href", "")
            if not href:
                continue
            url = urljoin("https://www.indeed.com", href)
            title = clean_text(link.get_text(" "))
            company = clean_text(card.select_one("span[data-testid='company-name'], span.companyName").get_text(" ")) if card.select_one("span[data-testid='company-name'], span.companyName") else ""
            location = clean_text(card.select_one("div[data-testid='company_location'], div.companyLocation").get_text(" ")) if card.select_one("div[data-testid='company_location'], div.companyLocation") else ""
            pay = clean_text(card.select_one("div.salary-snippet-container, div.salary-snippet").get_text(" ")) if card.select_one("div.salary-snippet-container, div.salary-snippet") else ""
            results.append({
                "title": title or term,
                "company": company,
                "url": url,
                "location": location,
                "remote": "remote" in (title + " " + location).lower(),
                "pay": pay,
                "posted_at": "",
                "description": f"{title} at {company}. Location: {location}.",
            })
        return results


class LinkedInScraper(SearchBoardScraper):
    name = "linkedin"
    search_url = "https://www.linkedin.com/jobs/search/?keywords={term}&start={start}"

    def fetch_jobs(self) -> list[dict]:
        jobs: list[dict] = []
        for term in SETTINGS.all_search_terms:
            for start in range(0, SETTINGS.max_results_per_term, 10):
                url = self._search_url(term, start)
                for attempt in range(2):
                    html = fetch_camoufox(url)
                    page_jobs = self._parse(html, term)
                    if page_jobs or attempt == 1:
                        break
                jobs.extend(page_jobs)
                if len(page_jobs) < 10:
                    break
        return jobs

    def _parse(self, html: str, term: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        results: list[dict] = []
        seen: set[str] = set()
        for anchor in soup.select('a[href*="/jobs/view/"]'):
            href = anchor.get("href", "")
            url = href.split("?")[0]
            if not url or url in seen:
                continue
            seen.add(url)
            card = anchor
            for _ in range(4):
                parent = card.parent
                if parent is None:
                    break
                card = parent
                if card.select_one("h3.base-search-card__title"):
                    break
            title = clean_text(card.select_one("h3.base-search-card__title").get_text(" ")) if card.select_one("h3.base-search-card__title") else clean_text(anchor.get_text(" "))
            company = clean_text(card.select_one("h4.base-search-card__subtitle").get_text(" ")) if card.select_one("h4.base-search-card__subtitle") else ""
            loc_el = card.select_one(".job-search-card__location")
            location = clean_text(loc_el.get_text(" ")) if loc_el else ""
            date_el = card.select_one("time.job-search-card__listdate")
            posted = date_el.get("datetime", "") if date_el else ""
            results.append({
                "title": title or term,
                "company": company,
                "url": url,
                "location": location,
                "remote": "remote" in (title + " " + location).lower(),
                "pay": "",
                "posted_at": posted,
                "description": f"{title} at {company}. Location: {location}.",
            })
        return results


class WellfoundScraper(SearchBoardScraper):
    name = "wellfound"
    search_url = "https://wellfound.com/role/r/{term}?page={page}"
    page_param = "page"

    def _search_url(self, term: str, start: int) -> str:
        page = start // 10 + 1
        return self.search_url.format(term=term.replace(" ", "-"), page=page)

    def _parse(self, html: str, term: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        results: list[dict] = []
        for card in soup.select("div[data-testid='job-card'], li[data-job-card], .jobs-list a[href*='/job/']"):
            link = card if card.name == "a" else card.select_one("a[href*='/job/']")
            href = link.get("href", "") if link else ""
            if not href:
                continue
            url = urljoin("https://wellfound.com", href)
            title = clean_text(link.get_text(" "))
            text = clean_text(card.get_text(" "))
            company = text.split(" at ")[-1].split(" ")[0] if " at " in text else ""
            results.append({
                "title": title or term,
                "company": company,
                "url": url,
                "location": "",
                "remote": True,
                "pay": "",
                "posted_at": "",
                "description": text,
            })
        return results


register("indeed")(IndeedScraper)
register("linkedin")(LinkedInScraper)
register("wellfound")(WellfoundScraper)
