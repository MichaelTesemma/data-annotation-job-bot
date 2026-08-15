from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

DEFAULT_SEARCH_TERMS = [
    "data annotation",
    "data labeling",
    "AI training",
    "AI tutor",
    "RLHF",
    "data analyst annotation",
]

TRANSLATION_SEARCH_TERMS = [
    "amharic translation",
    "amharic english",
    "english amharic translator",
    "amharic to english",
]


@dataclass
class Settings:
    search_terms: list[str] = field(default_factory=lambda: list(DEFAULT_SEARCH_TERMS))
    translation_search_terms: list[str] = field(default_factory=lambda: list(TRANSLATION_SEARCH_TERMS))
    rate_limit_seconds: float = 2.0

    @property
    def all_search_terms(self) -> list[str]:
        return list(self.search_terms) + list(self.translation_search_terms)
    user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    )
    db_path: Path = PROJECT_ROOT / "data" / "jobs.db"
    scheduler_interval_hours: int = 4
    max_results_per_term: int = 50
    request_timeout_seconds: int = 20
    robots_enabled: bool = True
    camoufox_wait_seconds: float = 6.0
    camoufox_timeout_seconds: int = 120


def _load_local_overrides() -> Settings:
    settings = Settings()
    local_file = PROJECT_ROOT / "config.local.py"
    if local_file.exists():
        import runpy

        namespace = runpy.run_path(str(local_file))
        for key, value in namespace.items():
            if key.startswith("_") or key not in settings.__dataclass_fields__:
                continue
            setattr(settings, key, value)
    return settings


SETTINGS = _load_local_overrides()
