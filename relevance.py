"""Central relevance gate: keep only annotation/translation/data jobs.

Applied in BaseScraper.run() so every source is filtered uniformly. A job
must match at least one include keyword (annotation / translation / data
work), and its title must not match a clearly-unrelated profession.
"""

# Substrings (case-insensitive) that mark a job as relevant.
INCLUDE_KEYWORDS = [
    # annotation / AI training
    "annotat",
    "data label",
    "labeling",
    "labeler",
    "tagger",
    "tagging",
    "rlhf",
    "ai training",
    "ai trainer",
    "ai tutor",
    "ai teacher",
    "ai coach",
    "model training",
    "model evaluation",
    "model validation",
    "evaluator",
    "prompt",
    "training data",
    "training dataset",
    "ai content",
    "content reviewer",
    "content review",
    "content moderation",
    "ai/ml",
    "ai ml",
    "ml data",
    "ai data",
    # translation
    "translat",
    "translator",
    "interpret",
    "interpreter",
    "amharic",
    "አማርኛ",
    "ethiopian language",
    "language specialist",
    "linguist",
    "linguistic",
    # data work (Ethiopia-relevant remote gigs)
    "data entry",
    "data entr",
    "data collection",
    "data contributor",
    "data processing",
    "data clerk",
    "online data analyst",
    "ai content analyst",
    "ai data analyst",
]

# Title-only substrings that mark a job as irrelevant even if it matches
# an include keyword (e.g. "Sales Data Analyst").
EXCLUDE_KEYWORDS = [
    "sales",
    "marketing",
    "nurse",
    "nursing",
    "physician",
    "doctor",
    "therapist",
    "psychologist",
    "psychiatrist",
    "dietitian",
    "nutrition",
    "lawyer",
    "attorney",
    "paralegal",
    "accountant",
    "bookkeeper",
    "driver",
    "delivery",
    "machinist",
    "electrician",
    "plumber",
    "welder",
    "carpenter",
    "construction",
    "mechanic",
    "receptionist",
    "barista",
    "waiter",
    "waitress",
    "janitor",
    "photographer",
    "videographer",
    "graphic designer",
    "realtor",
    "pharmacist",
    "optometrist",
    "dentist",
    "veterinarian",
    "chef",
    "cook",
    "kitchen",
    # on-site / local-language interpreting and teaching roles that leak
    # in through the "interpreter"/"bilingual" keywords are not relevant
    "police",
    "officer",
    "teaching",
    "teacher",
    "school",
    "professor",
    "lecturer",
    "customer service",
    "customer support",
    "healthcare",
    "recruiter",
    "employment specialist",
    "mentor",
    "counselor",
    "care representative",
    "care specialist",
    "office assistant",
    # virtual-assistant / admin gigs (leak via description keywords)
    "virtual assistant",
    "micro task",
    "administrative assistant",
    "admin assistant",
    "executive assistant",
    "back office",
    "bookkeep",
    "hr coordinator",
    "office manager",
    # software / app / on-site dev gigs that leak via description keywords
    "mobile app",
    "ios app",
    "android app",
    "android",
    "ios",
    "iot",
    "embedded",
    "social media",
    "engagement drive",
    "retail management",
    "dating app",
    "on-site",
    "on site",
    "fullstack",
    "software engineer",
    "openwakeword",
]


def is_relevant(title: str, description: str) -> bool:
    title_l = (title or "").lower()
    desc_l = (description or "").lower()

    if not title_l and not desc_l:
        return False

    if any(kw in title_l for kw in EXCLUDE_KEYWORDS):
        return False

    haystack = f"{title_l} {desc_l}"
    return any(kw in haystack for kw in INCLUDE_KEYWORDS)
