import json

from bs4 import BeautifulSoup

from config import SETTINGS
from scrapers.base import BaseScraper, ScraperError, fetch, clean_text
from scrapers.registry import register

REMOTE_TERMS = ["data annotation", "data labeling", "AI training", "AI tutor", "RLHF", "data entry", "virtual assistant", "amharic", "translat"]
WORKINGNOMADS_TERMS = ["data annotat", "data label", "ai training", "ai tutor", "rlhf", "data entr", "virtual assistant", "data analyst", "ai content", "online data", "amharic", "translat"]


class RemoteOkScraper(BaseScraper):
    name = "remoteok"
    api_url = "https://remoteok.com/api"

    def fetch_jobs(self) -> list[dict]:
        html = fetch(self.api_url)
        return self._parse(html, "remoteok")

    def _parse(self, html: str, term: str) -> list[dict]:
        data = json.loads(html)
        if not isinstance(data, list):
            raise ScraperError(f"remoteok API returned unexpected shape: {type(data)}")
        jobs: list[dict] = []
        for item in data:
            if not isinstance(item, dict) or "position" not in item:
                continue
            tag_text = " ".join(item.get("tags", [])).lower()
            blob = (item.get("position", "") + " " + tag_text).lower()
            if not any(t in blob for t in REMOTE_TERMS):
                continue
            salary = _salary_from_numbers(item.get("salary_min"), item.get("salary_max"))
            title = clean_text(item.get("position", ""))
            jobs.append({
                "title": title or "Remote position",
                "company": clean_text(item.get("company", "")),
                "url": item.get("url", ""),
                "location": clean_text(item.get("location", "")),
                "remote": True,
                "pay": salary,
                "posted_at": clean_text(item.get("date", "")),
                "description": f"Tags: {', '.join(item.get('tags', []))}.",
            })
        return jobs


class RemotiveScraper(BaseScraper):
    name = "remotive"
    api_url = "https://remotive.com/api/remote-jobs?search={term}"

    def fetch_jobs(self) -> list[dict]:
        jobs: list[dict] = []
        seen: set[str] = set()
        for term in SETTINGS.all_search_terms:
            html = fetch(self.api_url.format(term=self._quote(term)))
            for job in self._parse(html, term):
                if job["url"] not in seen:
                    seen.add(job["url"])
                    jobs.append(job)
        return jobs

    @staticmethod
    def _quote(term: str) -> str:
        return term.replace(" ", "+")

    def _parse(self, html: str, term: str) -> list[dict]:
        data = json.loads(html)
        jobs: list[dict] = []
        for item in data.get("jobs", []):
            jobs.append(self._to_job(item))
        return jobs

    def _to_job(self, item: dict) -> dict:
        title = clean_text(item.get("title", ""))
        company = clean_text(item.get("company_name", ""))
        location = clean_text(item.get("candidate_required_location", ""))
        description = clean_text(item.get("description", ""))
        return {
            "title": title,
            "company": company,
            "url": item.get("url", ""),
            "location": location,
            "remote": True,
            "pay": clean_text(item.get("salary", "")),
            "posted_at": clean_text(item.get("publication_date", "")),
            "description": description or f"{title} at {company}.",
        }


class WorkingNomadsScraper(BaseScraper):
    name = "workingnomads"
    api_url = "https://www.workingnomads.com/api/exposed_jobs/"

    def fetch_jobs(self) -> list[dict]:
        html = fetch(self.api_url)
        jobs: list[dict] = []
        seen: set[str] = set()
        for job in self._parse(html, "workingnomads"):
            if job["url"] not in seen:
                seen.add(job["url"])
                jobs.append(job)
        return jobs

    def _parse(self, html: str, term: str) -> list[dict]:
        data = json.loads(html)
        if not isinstance(data, list):
            raise ScraperError(f"workingnomads API returned unexpected shape: {type(data)}")
        jobs: list[dict] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            url = item.get("url", "")
            if not url:
                continue
            title = clean_text(item.get("title", ""))
            blob = (title + " " + clean_text(item.get("category_name", ""))).lower()
            if not any(t in blob for t in WORKINGNOMADS_TERMS):
                continue
            soup = BeautifulSoup(item.get("description", ""), "html.parser")
            jobs.append({
                "title": title,
                "company": clean_text(item.get("company_name", "")),
                "url": url,
                "location": clean_text(item.get("location", "")),
                "remote": True,
                "pay": "",
                "posted_at": clean_text(item.get("pub_date", "")),
                "description": clean_text(soup.get_text(" ")) or title,
            })
        return jobs


def _salary_from_numbers(lo, hi) -> str:
    try:
        lo = float(lo or 0)
        hi = float(hi or 0)
    except (TypeError, ValueError):
        return ""
    if lo <= 0 and hi <= 0:
        return ""
    return f"${lo:,.0f} - ${hi:,.0f}"


register("remoteok")(RemoteOkScraper)
register("remotive")(RemotiveScraper)
register("workingnomads")(WorkingNomadsScraper)
