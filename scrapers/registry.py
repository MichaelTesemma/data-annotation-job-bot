import logging
from collections.abc import Callable

from scrapers.base import BaseScraper
from scrapers.state import state

logger = logging.getLogger("scrapers")

SOURCE_REGISTRY: dict[str, Callable[[], BaseScraper]] = {}


def register(name: str):
    def decorator(factory: Callable[[], BaseScraper]):
        SOURCE_REGISTRY[name] = factory
        return factory

    return decorator


def run_source(name: str) -> dict:
    factory = SOURCE_REGISTRY.get(name)
    if factory is None:
        return {"source": name, "status": "error", "error": f"unknown source: {name}"}
    return factory().run()


def run_all(sources: list[str] | None = None) -> list[dict]:
    names = sources or list(SOURCE_REGISTRY.keys())
    state.begin(names)
    results = []
    try:
        for name in names:
            state.start_source(name)
            result = run_source(name)
            results.append(result)
            state.finish_source(name, result)
    finally:
        state.end()
    return results
