from __future__ import annotations

import logging
from pathlib import Path

import typer
from rich.logging import RichHandler

from . import FiltraError, __version__
from .errors import InputValidationError
from .exit_codes import ExitCode
from .orchestration import HealthReport, collect_health_report, run_pipeline

APP_NAME = "filtra"
_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

app = typer.Typer(
    name=APP_NAME,
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)


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
        raise InputValidationError(
            message=f"Missing {description} path.",
            remediation=f"Provide a valid {description} file via the CLI options.",
        )
    if not path.exists() or not path.is_file():
        raise InputValidationError(
            message=f"{description.capitalize()} path '{path}' does not exist or is not a file.",
            remediation=f"Verify the {description} path and ensure the file is readable.",
        )
    return path


def _render_health_report(report: HealthReport) -> None:
    """Pretty-print the health diagnostics to the console."""

    typer.echo("Filtra environment diagnostics")
    typer.echo(f"Python runtime     : {report.python_version}")
    typer.echo(f"Model cache folder : {report.huggingface_cache}")

    if report.dependency_pins:
        typer.echo("Pinned dependencies: " + ", ".join(report.dependency_pins))
    else:
        typer.echo("Pinned dependencies: none detected")

    typer.echo("")
    for check in report.checks:
        typer.echo(f"[{check.status}] {check.name} - {check.detail}")
        if check.remediation:
            typer.echo(f"    Remediation: {check.remediation}")

    typer.echo("")
    typer.echo(f"Overall status: {report.overall_status}")


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
    health: bool = typer.Option(
        False,
        "--health",
        help="Run offline diagnostics to verify environment readiness.",
    ),
) -> None:
    """Configure logging and handle global options."""

    configure_logging(quiet=quiet)

    if version:
        typer.echo(__version__)
        raise typer.Exit(code=int(ExitCode.SUCCESS))

    if health:
        report = collect_health_report()
        _render_health_report(report)
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
    except InputValidationError as exc:
        logger.error(str(exc))
        if exc.remediation:
            logger.error("Remediation: %s", exc.remediation)
        raise typer.Exit(code=int(ExitCode.INVALID_INPUT)) from exc
    except FiltraError as exc:  # pragma: no cover - defensive guard
        logger.error(str(exc))
        remediation = getattr(exc, "remediation", None)
        if remediation:
            logger.error("Remediation: %s", remediation)
        raise typer.Exit(code=int(ExitCode.UNEXPECTED_ERROR)) from exc

    outcome = run_pipeline(resume_path=resume_path, jd_path=jd_path)

    raise typer.Exit(code=int(outcome.exit_code))


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

