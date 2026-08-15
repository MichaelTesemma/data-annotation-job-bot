import argparse
import logging
import sys

import db
from scrapers import aggregators, jobboards  # noqa: F401  (registers sources)
from scrapers.registry import run_all, SOURCE_REGISTRY
from data.seed_platforms import seed_platforms


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(level=level, format="%(levelname)s %(name)s: %(message)s")


def _print_summary(results: list[dict]) -> None:
    width = max(len(r["source"]) for r in results) if results else 8
    print(f"\n{'source'.ljust(width)}  {'status'.ljust(8)}  count")
    print("-" * (width + 20))
    for r in results:
        print(f"{r['source'].ljust(width)}  {r['status'].ljust(8)}  {r.get('count_found', 0)}")
    failures = [r for r in results if r["status"] == "error"]
    if failures:
        print("\nFailures:")
        for r in failures:
            print(f"  {r['source']}: {r.get('error', 'unknown error')[:120]}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Crawl data annotation job sources into the local database.")
    parser.add_argument("--source", nargs="*", help="Only run the given source(s).")
    parser.add_argument("--seed-platforms", action="store_true", help="Seed the dedicated-platforms table.")
    parser.add_argument("--no-verify", action="store_true", help="Skip robots.txt verification for this run.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging.")
    args = parser.parse_args(argv)

    _setup_logging(args.verbose)
    db.init_db()

    if args.seed_platforms:
        added = seed_platforms()
        print(f"Seeded {added} new platform(s).")
        return 0

    sources = args.source or None
    if sources:
        unknown = [s for s in sources if s not in SOURCE_REGISTRY]
        if unknown:
            print(f"Unknown source(s): {', '.join(unknown)}", file=sys.stderr)
            print(f"Available: {', '.join(sorted(SOURCE_REGISTRY))}", file=sys.stderr)
            return 2

    results = run_all(sources)
    _print_summary(results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
