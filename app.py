from __future__ import annotations

import logging
import sys

from views.cli_view import run_cli


def configure_logging() -> None:
    """
    Configures the basic logging for the application.

    This function sets up a logging configuration with a specific format and level,
    allowing for consistent logging throughout the application.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> int:
    """
    The main entry point of the application.

    This function initializes the logging configuration and runs the command-line
    interface, returning its exit code.

    Returns:
        int: The exit code of the CLI application.
    """
    configure_logging()
    return run_cli()


if __name__ == "__main__":
    # Ensures that the main function is called only when the script is executed directly.
    sys.exit(main())
