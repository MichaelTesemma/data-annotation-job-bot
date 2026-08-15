from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, fetch_with_fallback, clean_text
from scrapers.registry import register

FREELANCER_CATEGORIES = ["data-entry", "data-collection", "virtual-assistant", "data-analytics"]


class FreelancerScraper(BaseScraper):
    name = "freelancer"
    base_url = "https://www.freelancer.com"
    category_url = "https://www.freelancer.com/jobs/{category}/"

    def fetch_jobs(self) -> list[dict]:
        jobs: list[dict] = []
        seen: set[str] = set()
        for category in FREELANCER_CATEGORIES:
            html = fetch_with_fallback(self.category_url.format(category=category))
            for job in self._parse(html, category):
                if job["url"] not in seen:
                    seen.add(job["url"])
                    jobs.append(job)
        return jobs

    def _parse(self, html: str, category: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        results: list[dict] = []
        for card in soup.select('.JobSearchCard-item-inner[data-project-card="true"]'):
            link = card.select_one("a[data-heading-link='true'], a.JobSearchCard-primary-heading-link")
            href = link.get("href", "") if link else ""
            if not href:
                continue
            url = urljoin(self.base_url, href)
            title = clean_text(link.get_text(" ")) if link else ""
            if not title:
                continue
            desc_el = card.select_one(".JobSearchCard-primary-description")
            description = clean_text(desc_el.get_text(" ")) if desc_el else ""
            price = clean_text(card.select_one(".JobSearchCard-primary-price").get_text(" ")) if card.select_one(".JobSearchCard-primary-price") else ""
            days = clean_text(card.select_one(".JobSearchCard-primary-heading-days").get_text(" ")) if card.select_one(".JobSearchCard-primary-heading-days") else ""
            results.append({
                "title": title,
                "company": "",
                "url": url,
                "location": "Freelance",
                "remote": True,
                "pay": price,
                "posted_at": days,
                "description": description or title,
            })
        return results


register("freelancer")(FreelancerScraper)
