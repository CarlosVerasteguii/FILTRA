"""Module entrypoint for `python -m filtra`."""
from __future__ import annotations

from .cli import entrypoint


def main() -> None:
    """Invoke the CLI entrypoint."""

    entrypoint()


if __name__ == "__main__":
    main()

