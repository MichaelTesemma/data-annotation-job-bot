import db

PLATFORMS = [
    {"name": "DataAnnotation.tech", "url": "https://www.dataannotation.tech/", "ethiopia_accessible": False},
    {"name": "Outlier", "url": "https://outlier.ai/", "ethiopia_accessible": False},
    {"name": "Scale AI", "url": "https://scale.com/", "ethiopia_accessible": False},
    {"name": "Remotasks", "url": "https://www.remotasks.com/", "ethiopia_accessible": True},
    {"name": "Appen", "url": "https://appen.com/", "ethiopia_accessible": True},
    {"name": "Clickworker", "url": "https://www.clickworker.com/", "ethiopia_accessible": True},
    {"name": "Toloka", "url": "https://toloka.ai/", "ethiopia_accessible": True},
    {"name": "Mercor", "url": "https://mercor.com/", "ethiopia_accessible": True},
    {"name": "Invisible", "url": "https://www.invisible.co/", "ethiopia_accessible": False},
    {"name": "Alignerr", "url": "https://www.alignerr.com/", "ethiopia_accessible": False},
    {"name": "Prolific", "url": "https://www.prolific.com/", "ethiopia_accessible": False},
]


def seed_platforms() -> int:
    seeded = 0
    for platform in PLATFORMS:
        with db.get_conn() as conn:
            existing = conn.execute(
                "SELECT id FROM platforms WHERE name = ?", (platform["name"],)
            ).fetchone()
            if existing:
                continue
            conn.execute(
                """
                INSERT INTO platforms (name, url, ethiopia_accessible, status, notes)
                VALUES (:name, :url, :ethiopia_accessible, :status, :notes)
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
