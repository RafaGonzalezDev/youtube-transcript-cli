from __future__ import annotations

import logging

from views.gui_view import run_gui


def configure_logging() -> None:
    """
    Configures basic logging for the desktop application.

    This function sets up a logging configuration with a specific format and level,
    ensuring consistent logging throughout the application.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> None:
    """
    The main entry point for the desktop application.

    This function initializes the logging configuration and launches the graphical
    user interface (GUI).
    """
    configure_logging()
    run_gui()


if __name__ == "__main__":
    # Ensures that the main function is called only when the script is executed directly.
    main()
