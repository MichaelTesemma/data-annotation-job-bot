from categories import (
    all_filter_keywords,
    all_search_terms,
    categories,
    category_keywords,
    category_search_terms,
    category_sources,
)


def test_ten_categories():
    assert categories() == [
        "ai training",
        "content moderation",
        "data annotation",
        "data collection",
        "data entry",
        "micro task",
        "online research",
        "translation",
        "usability testing",
        "user interviews",
    ]


def test_every_category_has_terms_keywords_sources():
    for name in categories():
        assert category_search_terms(name), name
        assert category_keywords(name), name
        assert category_sources(name), name


def test_all_search_terms_union():
    terms = all_search_terms()
    assert "data annotation" in terms
    assert "amharic translation" in terms
    assert "usability testing" in terms
    assert "survey" in terms
    assert len(terms) == len(set(terms))


def test_all_filter_keywords_union_covers_categories():
    keywords = all_filter_keywords()
    for name in categories():
        for kw in category_keywords(name):
            assert kw in keywords


def test_translation_category_kept():
    assert "translation" in categories()
    assert "amharic" in category_keywords("translation")
    assert "amharic translation" in category_search_terms("translation")
    assert "linkedin" in category_sources("translation")
