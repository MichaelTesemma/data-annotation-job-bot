import db

PLATFORMS = [
    # data annotation / labeling
    {"name": "DataAnnotation.tech", "url": "https://www.dataannotation.tech/", "ethiopia_accessible": False, "category": "data annotation"},
    {"name": "Scale AI", "url": "https://scale.com/", "ethiopia_accessible": False, "category": "data annotation"},
    {"name": "Remotasks", "url": "https://www.remotasks.com/", "ethiopia_accessible": True, "category": "data annotation"},
    {"name": "Mercor", "url": "https://mercor.com/", "ethiopia_accessible": True, "category": "data annotation"},
    {"name": "Invisible", "url": "https://www.invisible.co/", "ethiopia_accessible": False, "category": "data annotation"},
    {"name": "Alignerr", "url": "https://www.alignerr.com/", "ethiopia_accessible": False, "category": "data annotation"},
    {"name": "TELUS International AI", "url": "https://www.telusinternational.ai/", "ethiopia_accessible": False, "category": "data annotation"},
    {"name": "Appen", "url": "https://appen.com/", "ethiopia_accessible": True, "category": "data annotation"},
    {"name": "LXT", "url": "https://lxt.ai/", "ethiopia_accessible": False, "category": "data annotation"},
    {"name": "SuperAnnotate", "url": "https://www.superannotate.com/", "ethiopia_accessible": False, "category": "data annotation"},
    # ai training / tutor / prompt evaluation
    {"name": "Outlier", "url": "https://outlier.ai/", "ethiopia_accessible": False, "category": "ai training"},
    {"name": "Turing", "url": "https://www.turing.com/", "ethiopia_accessible": False, "category": "ai training"},
    {"name": "Mindrift", "url": "https://mindrift.ai/", "ethiopia_accessible": False, "category": "ai training"},
    {"name": "DataAnnotation.tech", "url": "https://www.dataannotation.tech/", "ethiopia_accessible": False, "category": "ai training"},
    # content moderation & review
    {"name": "Telus Digital", "url": "https://www.telusdigital.com/", "ethiopia_accessible": False, "category": "content moderation"},
    {"name": "ModSquad", "url": "https://modsquad.com/", "ethiopia_accessible": False, "category": "content moderation"},
    # data entry
    {"name": "Fiverr", "url": "https://www.fiverr.com/", "ethiopia_accessible": True, "category": "data entry"},
    {"name": "Upwork", "url": "https://www.upwork.com/", "ethiopia_accessible": True, "category": "data entry"},
    {"name": "Freelancer", "url": "https://www.freelancer.com/", "ethiopia_accessible": True, "category": "data entry"},
    # online data collection / search evaluation
    {"name": "Appen", "url": "https://appen.com/", "ethiopia_accessible": True, "category": "data collection"},
    {"name": "Welocalize", "url": "https://www.welocalize.com/", "ethiopia_accessible": False, "category": "data collection"},
    {"name": "TELUS International AI", "url": "https://www.telusinternational.ai/", "ethiopia_accessible": False, "category": "data collection"},
    {"name": "OneForma", "url": "https://www.oneforma.com/", "ethiopia_accessible": False, "category": "data collection"},
    {"name": "Raterlabs", "url": "https://www.raterlabs.com/", "ethiopia_accessible": False, "category": "data collection"},
    # usability testing
    {"name": "UserTesting", "url": "https://www.usertesting.com/", "ethiopia_accessible": True, "category": "usability testing"},
    {"name": "Userlytics", "url": "https://www.userlytics.com/", "ethiopia_accessible": False, "category": "usability testing"},
    {"name": "TryMyUI", "url": "https://www.trymyui.com/", "ethiopia_accessible": True, "category": "usability testing"},
    {"name": "UsabilityHub", "url": "https://usabilityhub.com/", "ethiopia_accessible": True, "category": "usability testing"},
    {"name": "TestingTime", "url": "https://www.testingtime.com/", "ethiopia_accessible": False, "category": "usability testing"},
    # online research / web research
    {"name": "Upwork", "url": "https://www.upwork.com/", "ethiopia_accessible": True, "category": "online research"},
    {"name": "Fiverr", "url": "https://www.fiverr.com/", "ethiopia_accessible": True, "category": "online research"},
    {"name": "JustAnswer", "url": "https://www.justanswer.com/", "ethiopia_accessible": False, "category": "online research"},
    # micro-task / survey platforms
    {"name": "Amazon Mechanical Turk", "url": "https://www.mturk.com/", "ethiopia_accessible": True, "category": "micro task"},
    {"name": "Prolific", "url": "https://www.prolific.com/", "ethiopia_accessible": False, "category": "micro task"},
    {"name": "Clickworker", "url": "https://www.clickworker.com/", "ethiopia_accessible": True, "category": "micro task"},
    {"name": "Toloka", "url": "https://toloka.ai/", "ethiopia_accessible": True, "category": "micro task"},
    {"name": "Microworkers", "url": "https://www.microworkers.com/", "ethiopia_accessible": True, "category": "micro task"},
    {"name": "Swagbucks", "url": "https://www.swagbucks.com/", "ethiopia_accessible": False, "category": "micro task"},
    {"name": "Timebucks", "url": "https://www.timebucks.com/", "ethiopia_accessible": True, "category": "micro task"},
    # user interviews / respondent panels
    {"name": "User Interviews", "url": "https://www.userinterviews.com/", "ethiopia_accessible": False, "category": "user interviews"},
    {"name": "Respondent.io", "url": "https://www.respondent.io/", "ethiopia_accessible": False, "category": "user interviews"},
    {"name": "dscout", "url": "https://dscout.com/", "ethiopia_accessible": False, "category": "user interviews"},
    {"name": "UserTesting", "url": "https://www.usertesting.com/", "ethiopia_accessible": True, "category": "user interviews"},
    # translation
    {"name": "Gengo", "url": "https://gengo.com/", "ethiopia_accessible": False, "category": "translation"},
    {"name": "ProZ", "url": "https://www.proz.com/", "ethiopia_accessible": True, "category": "translation"},
    {"name": "TransPerfect", "url": "https://www.transperfect.com/", "ethiopia_accessible": False, "category": "translation"},
    {"name": "Welocalize", "url": "https://www.welocalize.com/", "ethiopia_accessible": False, "category": "translation"},
]


def seed_platforms() -> int:
    seeded = 0
    for platform in PLATFORMS:
        with db.get_conn() as conn:
            existing = conn.execute(
                "SELECT id FROM platforms WHERE name = ? AND category = ?",
                (platform["name"], platform["category"]),
            ).fetchone()
            if existing:
                continue
            conn.execute(
                """
                INSERT INTO platforms (name, url, ethiopia_accessible, status, notes, category)
                VALUES (:name, :url, :ethiopia_accessible, :status, :notes, :category)
                """,
                {**platform, "status": "not_applied", "notes": ""},
            )
            seeded += 1
    return seeded


def main() -> None:
    db.init_db()
    count = seed_platforms()
    print(f"Seeded {count} new platform(s).")


if __name__ == "__main__":
    main()