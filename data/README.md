# Local data directory

This directory holds local, gitignored state:

- `jobs.db` — the SQLite database produced and read by the job bot.

It is safe to delete `jobs.db` (or the whole directory) to reset; everything is
recreated on the next run. Source code in this package (`seed_platforms.py`) is
tracked in git.
