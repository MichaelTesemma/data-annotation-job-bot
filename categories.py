"""Keyword-based job categories for dashboard filtering."""

# Keys are category names shown in the dashboard filter.
# Values are substrings matched (case-insensitively) against
# title, company, location, and description.
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "data annotation": [
        "annotat",
        "label",
        "ai training",
        "ai tutor",
        "rlhf",
        "training data",
        "model training",
        "prompt",
    ],
    "translation": [
        "amharic",
        "translat",
        "translator",
        "english to amharic",
        "amharic to english",
        "interpreter",
        "አማርኛ",
        "language specialist",
    ],
}


def categories() -> list[str]:
    return sorted(CATEGORY_KEYWORDS)


def category_keywords(category: str) -> list[str]:
    return CATEGORY_KEYWORDS.get(category, [])
