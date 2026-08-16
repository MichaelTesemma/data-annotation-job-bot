from relevance import is_relevant


def test_annotation_jobs_kept():
    assert is_relevant("Data Annotator", "label training data for ML models")
    assert is_relevant("AI Tutor - Igbo", "tutor and grade AI responses")
    assert is_relevant("Prompt Engineer", "write and evaluate prompts for LLM training")
    assert is_relevant("RLHF Data Contributor", "rank model outputs")
    assert is_relevant("Online Data Analyst", "help train search relevance")


def test_new_categories_kept():
    assert is_relevant("Website Tester", "test website usability and report bugs")
    assert is_relevant("UserTesting Panelist", "complete usability sessions")
    assert is_relevant("MTurk Worker", "complete micro tasks on Amazon MTurk")
    assert is_relevant("Clickworker Survey Taker", "take online surveys for pay")
    assert is_relevant("Research Respondent", "join research panel and share feedback")
    assert is_relevant("Content Moderator", "review flagged user content")
    assert is_relevant("Web Research Assistant", "compile online research into spreadsheets")
    assert is_relevant("Search Evaluator", "rate search results for relevance")
    assert is_relevant("Micro task specialist", "complete small micro tasks")


def test_translation_jobs_kept():
    assert is_relevant("Amharic English Translator", "translate documents to and from Amharic")
    assert is_relevant("Twi English Interpreter", "interpret calls between Twi and English")
    assert is_relevant("Language Specialist", "bilingual review of translated content")
    assert is_relevant("አማርኛ ተርጓሚ", "amharic translation work")


def test_off_topic_jobs_dropped():
    assert not is_relevant("Optometrist", "provide eye exams")
    assert not is_relevant("Kitchen Porter", "assist kitchen staff")
    assert not is_relevant("1st Class Machinist", "operate lathes")
    assert not is_relevant("Electrician ETO", "maintain ship electrical systems")
    assert not is_relevant("Licensed Therapist", "provide counseling")
    assert not is_relevant("Registered Dietitian", "nutrition counseling")
    assert not is_relevant("Sales Manager", "grow revenue")
    assert not is_relevant("Senior Ruby on Rails Developer", "build web apps")
    assert not is_relevant("Graphic Designer", "create brand assets")
    assert not is_relevant("Executive Assistant", "manage executive calendar")


def test_exclude_beats_include():
    assert not is_relevant("Sales Data Analyst", "analyze data and close deals")


def test_empty_text_dropped():
    assert not is_relevant("", "")
    assert not is_relevant("", "no useful info here")
