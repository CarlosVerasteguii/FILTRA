from __future__ import annotations

import logging
from enum import IntEnum
from pathlib import Path

import typer
from rich.logging import RichHandler

from . import FiltraError, __version__

APP_NAME = "filtra"
_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

app = typer.Typer(
    name=APP_NAME,
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)


class ExitCode(IntEnum):
    """Supported CLI exit codes."""

    SUCCESS = 0
    GENERAL_FAILURE = 1
    INPUT_ERROR = 2
    EXTERNAL_FAILURE = 3
    CONFIGURATION_FAILURE = 4


def configure_logging(*, quiet: bool = False) -> None:
    """Initialise application-wide logging."""

    level = logging.WARNING if quiet else logging.INFO
    root = logging.getLogger()

    if getattr(configure_logging, "_configured", False):
        root.setLevel(level)
        for handler in root.handlers:
            handler.setLevel(level)
        configure_logging._level = level
        return

    handler = RichHandler(
        rich_tracebacks=True,
        show_path=False,
        markup=False,
    )
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))

    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    configure_logging._configured = True
    configure_logging._level = level


def _validate_file(path: Path, description: str) -> Path:
    """Ensure the provided file path exists and is readable."""

    if not path:
        raise FiltraError(f"Missing {description} path.")
    if not path.exists() or not path.is_file():
        raise FiltraError(f"{description.capitalize()} path '{path}' does not exist or is not a file.")
    return path


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    quiet: bool = typer.Option(
        False,
        "--quiet",
        help="Reduce log output to warnings and errors.",
    ),
    version: bool = typer.Option(
        False,
        "--version",
        help="Show the Filtra version and exit.",
    ),
) -> None:
    """Configure logging and handle global options."""

    configure_logging(quiet=quiet)

    if version:
        typer.echo(__version__)
        raise typer.Exit(code=int(ExitCode.SUCCESS))

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit(code=int(ExitCode.SUCCESS))


@app.command("run")
def run(
    resume: Path = typer.Option(
        ...,
        "--resume",
        "-r",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to the resume file (PDF or text).",
    ),
    jd: Path = typer.Option(
        ...,
        "--jd",
        "-j",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to the job description file.",
    ),
) -> None:
    """Execute the resume vs job description evaluation pipeline."""

    logger = logging.getLogger("filtra.cli")

    try:
        resume_path = _validate_file(resume, "resume")
        jd_path = _validate_file(jd, "job description")
    except FiltraError as exc:  # pragma: no cover - defensive guard
        logger.error(str(exc))
        raise typer.Exit(code=int(ExitCode.INPUT_ERROR)) from exc

    logger.info("Starting evaluation run", extra={"resume": resume_path.name, "jd": jd_path.name})
    logger.info("Pipeline execution is not yet implemented in this scaffold.")

    raise typer.Exit(code=int(ExitCode.SUCCESS))


@app.command("warm-up")
def warm_up() -> None:
    """Placeholder warm-up routine for model caching and diagnostics."""

    logger = logging.getLogger("filtra.cli")
    logger.info("Warm-up diagnostics are not yet implemented in this scaffold.")
    raise typer.Exit(code=int(ExitCode.SUCCESS))


def entrypoint() -> None:
    """Execute the Typer application."""

    app()


__all__ = ["app", "entrypoint", "configure_logging", "ExitCode"]

