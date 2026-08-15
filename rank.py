PLATFORM_ACCESS = {
    "remotasks": 0.95,
    "toloka": 0.9,
    "mercor": 0.9,
    "clickworker": 0.9,
    "appen": 0.85,
    "scale ai": 0.5,
    "outlier": 0.4,
    "dataannotation.tech": 0.3,
    "dataannotation": 0.3,
    "alignerr": 0.3,
    "invisible": 0.3,
    "prolific": 0.3,
}

GLOBAL_KEYWORDS = ["global", "worldwide", "remote anywhere", "anywhere", "open to all", "international"]

RESTRICTION_KEYWORDS = [
    "us only",
    "united states only",
    "uk only",
    "eu only",
    "europe only",
    "canada only",
    "australia only",
    "us-based",
    "uk-based",
    "must be located in the united states",
    "u.s. only",
    "us residents",
    "eu residents",
    "requires us citizenship",
]


def access_score(platform: str, location: str, remote: bool, description: str) -> float:
    score = 0.4
    haystack = f"{location} {description}".lower()

    platform_key = platform.strip().lower()
    for key, weight in PLATFORM_ACCESS.items():
        if key in platform_key:
            score = weight
            break

    if any(kw in haystack for kw in RESTRICTION_KEYWORDS):
        score *= 0.25

    if any(kw in haystack for kw in GLOBAL_KEYWORDS):
        score = max(score, 0.75)

    if remote:
        score = max(score, min(score + 0.1, 0.95))

    return max(0.0, min(round(score, 2), 1.0))


def overall_score(access: float, remote: bool, pay_text: str, description: str) -> float:
    access_component = access * 0.5
    desirability = 0.3

    if remote:
        desirability += 0.15

    if pay_text.strip():
        desirability += 0.15

    description_length = len(description.strip())
    if description_length > 200:
        desirability += 0.1
    elif description_length > 50:
        desirability += 0.05

    return max(0.0, min(round(access_component + desirability, 2), 1.0))


def score_job(job: dict) -> dict:
    access = access_score(
        job.get("company", ""),
        job.get("location", ""),
        bool(job.get("remote")),
        job.get("description", ""),
    )
    job["access_score"] = access
    job["overall_score"] = overall_score(
        access,
        bool(job.get("remote")),
        job.get("pay", ""),
        job.get("description", ""),
    )
    return job
