"""Granular job categories: the single source of truth for search terms,
dashboard filters, relevance includes, and relevant job sources."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CategorySpec:
    search_terms: list[str]
    filter_keywords: list[str]
    sources: list[str]


CATEGORIES: dict[str, CategorySpec] = {
    "data annotation": CategorySpec(
        search_terms=["data annotation", "data labeling", "annotation", "labeling"],
        filter_keywords=[
            "annotat",
            "data label",
            "labeling",
            "labeler",
            "tagger",
            "tagging",
            "ml data",
            "ai data",
        ],
        sources=[
            "linkedin", "nodesk", "remoteco", "remoteok", "remotive",
            "weworkremotely", "workingnomads", "freelancer",
        ],
    ),
    "ai training": CategorySpec(
        search_terms=["AI training", "AI tutor", "prompt engineer", "RLHF"],
        filter_keywords=[
            "ai training",
            "ai trainer",
            "ai tutor",
            "ai teacher",
            "ai coach",
            "rlhf",
            "prompt",
            "model training",
            "model evaluation",
            "model validation",
            "evaluator",
            "training data",
            "training dataset",
            "ai content",
            "ai content analyst",
            "ai/ml",
            "ai ml",
        ],
        sources=[
            "linkedin", "nodesk", "remoteok", "remotive",
            "weworkremotely", "workingnomads",
        ],
    ),
    "content moderation": CategorySpec(
        search_terms=["content moderation", "content reviewer"],
        filter_keywords=[
            "content moderation",
            "content review",
            "content reviewer",
            "content moderator",
        ],
        sources=["linkedin", "remoteok", "remotive", "weworkremotely"],
    ),
    "data entry": CategorySpec(
        search_terms=["data entry", "data entry clerk"],
        filter_keywords=[
            "data entry",
            "data entr",
            "data clerk",
            "data contributor",
            "data processing",
        ],
        sources=["freelancer", "remoteco", "linkedin", "weworkremotely"],
    ),
    "data collection": CategorySpec(
        search_terms=["data collection", "search evaluator", "online data analyst"],
        filter_keywords=[
            "data collection",
            "search evaluator",
            "search evaluation",
            "rater",
            "online data analyst",
            "ai data analyst",
        ],
        sources=[
            "linkedin", "remoteco", "remoteok", "workingnomads", "freelancer",
        ],
    ),
    "usability testing": CategorySpec(
        search_terms=["usability testing", "user testing", "website testing"],
        filter_keywords=[
            "usability",
            "user testing",
            "usertesting",
            "userlytics",
            "website testing",
            "app testing",
        ],
        sources=["linkedin", "remoteok", "remotive", "weworkremotely"],
    ),
    "online research": CategorySpec(
        search_terms=["web research", "online research", "research assistant"],
        filter_keywords=[
            "web research",
            "online research",
            "research assistant",
            "researcher",
        ],
        sources=["freelancer", "linkedin", "remoteok"],
    ),
    "micro task": CategorySpec(
        search_terms=["micro task", "microtasks", "online surveys", "survey"],
        filter_keywords=[
            "micro task",
            "microtasks",
            "mturk",
            "prolific",
            "clickworker",
            "survey",
        ],
        sources=["freelancer", "remoteco", "workingnomads", "linkedin"],
    ),
    "user interviews": CategorySpec(
        search_terms=["user interviews", "research panel", "respondent"],
        filter_keywords=[
            "user interview",
            "respondent",
            "panel",
            "participant",
        ],
        sources=["linkedin", "remoteok", "remoteco"],
    ),
    "translation": CategorySpec(
        search_terms=[
            "amharic translation",
            "amharic english",
            "english amharic translator",
            "amharic to english",
        ],
        filter_keywords=[
            "amharic",
            "translat",
            "translator",
            "english to amharic",
            "amharic to english",
            "interpreter",
            "interpret",
            "አማርኛ",
            "language specialist",
            "linguist",
            "linguistic",
            "ethiopian language",
        ],
        sources=[
            "linkedin", "remoteafrica", "remoteco", "freelancer",
            "remoteok", "workingnomads",
        ],
    ),
}


def categories() -> list[str]:
    return sorted(CATEGORIES)


def category_keywords(category: str) -> list[str]:
    return CATEGORIES.get(category, CategorySpec([], [], [])).filter_keywords


def category_search_terms(category: str) -> list[str]:
    return CATEGORIES.get(category, CategorySpec([], [], [])).search_terms


def category_sources(category: str) -> list[str]:
    return CATEGORIES.get(category, CategorySpec([], [], [])).sources


def all_search_terms() -> list[str]:
    seen: list[str] = []
    for spec in CATEGORIES.values():
        for term in spec.search_terms:
            if term not in seen:
                seen.append(term)
    return seen


def all_filter_keywords() -> list[str]:
    seen: list[str] = []
    for spec in CATEGORIES.values():
        for kw in spec.filter_keywords:
            if kw not in seen:
                seen.append(kw)
    return seen
