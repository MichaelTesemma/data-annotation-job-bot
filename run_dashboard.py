import argparse
import logging
import sys
from pathlib import Path

import uvicorn

from config import PROJECT_ROOT


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Start the local job dashboard.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    uvicorn.run("dashboard.main:app", host=args.host, port=args.port, reload=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
