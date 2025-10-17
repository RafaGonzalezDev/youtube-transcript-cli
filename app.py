from __future__ import annotations

import logging
import sys

from views.cli_view import run_cli


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> int:
    configure_logging()
    return run_cli()


if __name__ == "__main__":
    sys.exit(main())
