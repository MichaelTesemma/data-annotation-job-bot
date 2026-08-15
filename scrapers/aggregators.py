import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import SETTINGS
from scrapers.base import BaseScraper, ScraperError, fetch, clean_text
from scrapers.registry import register


class WeWorkRemotelyScraper(BaseScraper):
    name = "weworkremotely"
    base_url = "https://weworkremotely.com"
    search_url = "https://weworkremotely.com/remote-jobs/search?term={term}"

    def fetch_jobs(self) -> list[dict]:
        jobs: list[dict] = []
        for term in SETTINGS.search_terms:
            html = fetch(self.search_url.format(term=self._quote(term)))
            jobs.extend(self._parse(html, term))
        return jobs

    @staticmethod
    def _quote(term: str) -> str:
        return term.replace(" ", "+")

    def _parse(self, html: str, term: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        results: list[dict] = []
        for li in soup.select("section.jobs li.new-listing-container:not(.listing-ad)"):
            link = li.select_one("a.listing-link--unlocked")
            if link is None:
                continue
            href = link.get("href", "")
            if not href:
                continue
            url = urljoin(self.base_url, href)
            title = clean_text(li.select_one(".new-listing__header__title__text").get_text(" ")) if li.select_one(".new-listing__header__title__text") else ""
            company = clean_text(li.select_one(".new-listing__company-name").get_text(" ")) if li.select_one(".new-listing__company-name") else ""
            hq = clean_text(li.select_one(".new-listing__company-headquarters").get_text(" ")) if li.select_one(".new-listing__company-headquarters") else ""
            posted = clean_text(li.select_one(".new-listing__header__icons__date").get_text(" ")) if li.select_one(".new-listing__header__icons__date") else ""
            chips = [clean_text(c.get_text(" ")) for c in li.select(".new-listing__categories__category")]
            region = ", ".join(c for c in chips if not c.startswith("$") and "featured" not in c.lower())
            pay = next((c for c in chips if c.startswith("$")), "")
            results.append({
                "title": title or term,
                "company": company,
                "url": url,
                "location": region or hq,
                "remote": True,
                "pay": pay,
                "posted_at": posted,
                "description": f"{title} at {company}. Regions: {region}.",
            })
        return results


class RemoteCoScraper(BaseScraper):
    name = "remoteco"
    base_url = "https://remote.co"
    category_url = "https://remote.co/remote-jobs/{category}/"

    def fetch_jobs(self) -> list[dict]:
        jobs: list[dict] = []
        seen_urls: set[str] = set()
        for category in ("data-entry", "customer-service", "virtual-assistant"):
            try:
                html = fetch(self.category_url.format(category=category))
            except ScraperError:
                html = fetch(self.category_url.format(category=category), use_playwright=True)
            for job in self._parse(html, category):
                if job["url"] not in seen_urls:
                    seen_urls.add(job["url"])
                    jobs.append(job)
        return jobs

    def _parse(self, html: str, category: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        results: list[dict] = []
        for card in soup.select("div.job-card"):
            link = card.select_one("a")
            if link is None:
                continue
            href = link.get("href", "")
            if not href:
                continue
            url = urljoin(self.base_url, href)
            title_el = card.select_one(".font-weight-bold.larger")
            title = clean_text(title_el.get_text(" ")) if title_el else ""
            meta = clean_text(card.select_one(".text-secondary").get_text(" ")) if card.select_one(".text-secondary") else ""
            company = meta.split("|")[0].strip() if meta else ""
            tags = [t.strip() for t in meta.split("|")[1:]]
            location = ", ".join(tags)
            results.append({
                "title": title,
                "company": company,
                "url": url,
                "location": location,
                "remote": True,
                "pay": "",
                "posted_at": "",
                "description": f"{title} at {company}. Source: remote.co {category}.",
            })
        return results


register("weworkremotely")(WeWorkRemotelyScraper)
register("remoteco")(RemoteCoScraper)
