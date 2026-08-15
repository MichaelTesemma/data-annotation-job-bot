import argparse
import logging
import sys
import time

import schedule

from config import SETTINGS
from scrapers import aggregators, jobboards  # noqa: F401  (registers sources)
from scrapers.registry import run_all


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(message)s")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the job scraper on a schedule.")
    parser.add_argument("--interval", type=int, default=SETTINGS.scheduler_interval_hours,
                        help="Hours between runs (default: %(default)s).")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    _setup_logging(args.verbose)

    def job() -> None:
        logging.info("Scheduled run starting")
        results = run_all()
        ok = sum(1 for r in results if r["status"] == "success")
        logging.info("Scheduled run finished: %d/%d sources succeeded", ok, len(results))

    schedule.every(args.interval).hours.do(job)
    logging.info("Scheduler running every %d hour(s). Ctrl+C to stop.", args.interval)

    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        logging.info("Stopped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
