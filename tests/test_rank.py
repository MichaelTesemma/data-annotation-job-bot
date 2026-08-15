import rank


def test_global_toloka_outranks_us_only():
    us_job = rank.score_job({"company": "DataAnnotation.tech", "location": "US only", "remote": True, "description": "US-based role", "pay": ""})
    global_job = rank.score_job({"company": "Toloka", "location": "Worldwide", "remote": True, "description": "Global role open worldwide", "pay": "$15/hr"})
    assert global_job["access_score"] > us_job["access_score"]
    assert global_job["overall_score"] > us_job["overall_score"]


def test_platform_reputation_weights():
    toloka = rank.access_score("Toloka", "Anywhere", True, "global")
    outlier = rank.access_score("Outlier", "Anywhere", True, "global")
    assert toloka > outlier


def test_region_restriction_penalizes():
    base = rank.access_score("Toloka", "Anywhere", True, "global role")
    restricted = rank.access_score("Toloka", "US only", True, "US-based role")
    assert restricted < base


def test_global_keywords_boost():
    low = rank.access_score("Random Co", "", False, "some task")
    boosted = rank.access_score("Random Co", "Worldwide", False, "remote anywhere global")
    assert boosted > low


def test_scores_within_bounds():
    for company in ("Toloka", "Outlier", "Random Co"):
        for location in ("Worldwide", "US only", "EU only", ""):
            job = rank.score_job({"company": company, "location": location, "remote": True, "description": "x" * 300, "pay": "$20/hr"})
            assert 0.0 <= job["access_score"] <= 1.0
            assert 0.0 <= job["overall_score"] <= 1.0


def test_pay_and_description_raise_overall():
    no_pay = rank.overall_score(0.8, True, "", "short")
    with_pay = rank.overall_score(0.8, True, "$20/hr", "short")
    assert with_pay > no_pay


def test_score_job_fills_both_fields():
    job = rank.score_job({"company": "Mercor", "location": "Worldwide", "remote": True, "description": "global"})
    assert "access_score" in job
    assert "overall_score" in job
