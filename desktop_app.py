from __future__ import annotations

import logging

from views.gui_view import run_gui


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> None:
    configure_logging()
    run_gui()


if __name__ == "__main__":
    main()
