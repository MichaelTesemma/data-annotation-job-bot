import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import SETTINGS
from scrapers.base import BaseScraper, ScraperError, fetch, fetch_camoufox, fetch_with_fallback, clean_text
from scrapers.registry import register


class WeWorkRemotelyScraper(BaseScraper):
    name = "weworkremotely"
    base_url = "https://weworkremotely.com"
    search_url = "https://weworkremotely.com/remote-jobs/search?term={term}"

    def fetch_jobs(self) -> list[dict]:
        jobs: list[dict] = []
        for term in SETTINGS.all_search_terms:
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
    category_url = "https://remote.co/remote-jobs/{category}"

    def fetch_jobs(self) -> list[dict]:
        jobs: list[dict] = []
        seen_urls: set[str] = set()
        for category in ("online-data-entry", "customer-service", "virtual-assistant"):
            html = fetch_camoufox(self.category_url.format(category=category))
            for job in self._parse(html, category):
                if job["url"] not in seen_urls:
                    seen_urls.add(job["url"])
                    jobs.append(job)
        return jobs

    def _parse(self, html: str, category: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        results: list[dict] = []
        for link in soup.select('a[href*="/job-details/"]'):
            href = link.get("href", "")
            if not href:
                continue
            url = urljoin(self.base_url, href)
            title = clean_text(link.select_one("h3").get_text(" ")) if link.select_one("h3") else ""
            if not title:
                continue
            card = link
            for _ in range(4):
                parent = card.parent
                if parent is None:
                    break
                card = parent
                if card.select_one("strong[id^='company-name-']"):
                    break
            company = clean_text(card.select_one("strong[id^='company-name-']").get_text(" ")) if card.select_one("strong[id^='company-name-']") else ""
            meta_items = [clean_text(li.get_text(" ")) for li in card.select("ul li")]
            pay = next((m for m in meta_items if "$" in m), "")
            work = ", ".join(m for m in meta_items if m not in (pay,))
            date_el = link.select_one("span")
            posted = clean_text(date_el.get_text(" ")) if date_el else ""
            results.append({
                "title": title,
                "company": company,
                "url": url,
                "location": work,
                "remote": True,
                "pay": pay,
                "posted_at": posted,
                "description": f"{title} at {company}. {work}. Source: remote.co {category}.",
            })
        return results


register("weworkremotely")(WeWorkRemotelyScraper)
register("remoteco")(RemoteCoScraper)


class RemoteAfricaScraper(BaseScraper):
    name = "remoteafrica"
    base_url = "https://remote4africa.com"
    list_url = "https://remote4africa.com/"

    def fetch_jobs(self) -> list[dict]:
        html = fetch_with_fallback(self.list_url)
        return self._parse(html, "remoteafrica")

    def _parse(self, html: str, term: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        results: list[dict] = []
        for a in soup.select('a[href^="/jobs/"]'):
            href = a.get("href", "")
            if not href or href == "/jobs/":
                continue
            url = urljoin(self.base_url, href)
            title = clean_text(a.get_text(" "))
            if not title:
                continue
            card = a
            for _ in range(4):
                parent = card.parent
                if parent is None:
                    break
                card = parent
                if card.select_one("img"):
                    break
            company_el = card.select_one("p")
            company = clean_text(company_el.get_text(" ")) if company_el else ""
            meta = [clean_text(s.get_text(" ")) for s in card.select("span")]
            location = ", ".join(m for m in meta if m and "remote" not in m.lower() and m.lower() != "contract")
            results.append({
                "title": title,
                "company": company,
                "url": url,
                "location": location,
                "remote": True,
                "pay": "",
                "posted_at": "",
                "description": f"{title} at {company}. Location: {location}.",
            })
        return results


class NodeSkScraper(BaseScraper):
    name = "nodesk"
    base_url = "https://nodesk.co"
    category_url = "https://nodesk.co/remote-jobs/{category}"

    def fetch_jobs(self) -> list[dict]:
        jobs: list[dict] = []
        seen: set[str] = set()
        for category in ("ai", "customer-support", "entry-level", "data"):
            html = fetch_with_fallback(self.category_url.format(category=category))
            for job in self._parse(html, category):
                if job["url"] not in seen:
                    seen.add(job["url"])
                    jobs.append(job)
        return jobs

    def _parse(self, html: str, category: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        results: list[dict] = []
        for li in soup.select("li"):
            link = li.select_one("h2 a[href*='/remote-jobs/'], h2 a")
            if link is None:
                continue
            href = link.get("href", "")
            if "/remote-jobs/" not in href or href.rstrip("/").endswith("/remote-jobs"):
                continue
            url = urljoin(self.base_url, href)
            title = clean_text(link.get_text(" "))
            company = clean_text(li.select_one("h3").get_text(" ")) if li.select_one("h3") else ""
            text = clean_text(li.get_text(" "))
            pay = ""
            for token in text.split():
                if token.startswith("$"):
                    pay = token
                    break
            location = clean_text(li.select_one(".grey-800").get_text(" ")) if li.select_one(".grey-800") else ""
            if location == company:
                location = ""
            results.append({
                "title": title,
                "company": company,
                "url": url,
                "location": location,
                "remote": True,
                "pay": pay,
                "posted_at": "",
                "description": f"{title} at {company}. Source: nodesk {category}.",
            })
        return results


register("remoteafrica")(RemoteAfricaScraper)
register("nodesk")(NodeSkScraper)
