from __future__ import annotations

import logging
from pathlib import Path

import typer
from rich.logging import RichHandler

from . import FiltraError, __version__
from .errors import InputValidationError
from .exit_codes import ExitCode
from .ner import DEFAULT_MODEL_ID
from .orchestration import (
    HealthReport,
    WarmupResult,
    collect_health_report,
    handle_domain_error,
    run_pipeline,
    run_warmup,
)
from .reporting import render_entities_report

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

    candidate = path.expanduser()
    try:
        resolved = candidate.resolve()
    except OSError:
        resolved = candidate

    display = _quote_path(resolved)
    if not resolved.exists() or not resolved.is_file():
        raise InputValidationError(
            message=f"{description.capitalize()} path {display} does not exist or is not a file.",
            remediation=f"Verify the {description} path and ensure the file is readable.",
        )
    return resolved


def _validate_model_id(model_id: str) -> str:
    """Ensure the provided NER model identifier is non-empty."""

    value = (model_id or "").strip()
    if not value:
        raise InputValidationError(
            message="NER model identifier cannot be empty.",
            remediation="Pass a valid Hugging Face repo using --ner-model.",
        )
    return value


def _is_quiet_mode() -> bool:
    """Determine if the CLI is currently running in quiet mode."""

    return getattr(configure_logging, "_level", logging.INFO) == logging.WARNING


def _quote_path(path: Path) -> str:
    """Return a quoted string representation when spaces are present."""

    value = str(path)
    if " " in value:
        return f'"{value}"'
    return value


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


def _render_warmup_result(result: WarmupResult, *, quiet: bool) -> None:
    """Present warm-up diagnostics while respecting quiet mode expectations."""

    cache_summary = _format_bytes(result.cache_size_bytes)
    alias_details = result.alias_map_details
    alias_summary = f"alias map {alias_details.canonical_count} groups"

    if quiet:
        typer.echo(
            f"Warm-up {result.overall_status} in {result.duration_seconds:.2f}s; "
            f"cache {cache_summary}; {alias_summary}; use --wide for source columns"
        )
        for check in result.checks:
            typer.echo(f"[{check.status}] {check.name}")
        return

    typer.echo("Filtra warm-up diagnostics")
    typer.echo(f"Python runtime     : {result.python_version}")
    typer.echo(f"Model cache folder : {result.huggingface_cache}")
    typer.echo(f"Cache on disk      : {cache_summary}")
    typer.echo(f"Duration           : {result.duration_seconds:.2f}s")
    typer.echo(
        f"Alias map sources  : {', '.join(str(path) for path in alias_details.sources)}"
    )
    typer.echo(
        "Alias map coverage : "
        f"{alias_details.canonical_count} groups / {alias_details.alias_count} aliases "
        f"(locales: {', '.join(alias_details.locale_codes or ('none',))})"
    )
    typer.echo("Report modifiers    : --quiet suppresses logs; --wide adds source columns")

    typer.echo("")
    typer.echo("Proxy environment:")
    for name, value in result.proxy_environment.items():
        status = "set (value hidden)" if value else "(not set)"
        typer.echo(f"  {name:<11}: {status}")
    if not any(result.proxy_environment.values()):
        typer.echo("  (none configured; direct internet access assumed)")

    typer.echo("")
    for check in result.checks:
        typer.echo(f"[{check.status}] {check.name} - {check.detail}")
        if check.remediation:
            typer.echo(f"    Remediation: {check.remediation}")

    typer.echo("")
    typer.echo(f"Overall status: {result.overall_status}")


def _format_bytes(size: int) -> str:
    """Format a byte count into a human-readable string."""

    if size < 1024:
        return f"{size} B"
    if size < 1024**2:
        return f"{size / 1024:.1f} KiB"
    if size < 1024**3:
        return f"{size / (1024 ** 2):.1f} MiB"
    return f"{size / (1024 ** 3):.2f} GiB"


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
    ner_model: str = typer.Option(
        DEFAULT_MODEL_ID,
        "--ner-model",
        help="Hugging Face model identifier for entity extraction.",
        show_default=True,
    ),
    alias_map: list[Path] = typer.Option(
        [],
        "--alias-map",
        "-a",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Additional alias map YAML files to merge (pass multiple times).",
    ),
    wide: bool = typer.Option(
        False,
        "--wide",
        help="Render the entities report with extended source columns.",
    ),
) -> None:
    """Execute the resume vs job description evaluation pipeline."""

    logger = logging.getLogger("filtra.cli")
    quiet_mode = _is_quiet_mode()

    try:
        resume_path = _validate_file(resume, "resume")
        jd_path = _validate_file(jd, "job description")
        resolved_model = _validate_model_id(ner_model)
        alias_paths = [_validate_file(path, "alias map") for path in alias_map]
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

    outcome = run_pipeline(
        resume_path=resume_path,
        jd_path=jd_path,
        ner_model=resolved_model,
        alias_map_paths=alias_paths,
        quiet=quiet_mode,
        wide=wide,
    )

    printed_message = False
    if outcome.message and not quiet_mode:
        typer.echo(outcome.message)
        printed_message = True

    if outcome.report is not None:
        if printed_message:
            typer.echo("")
        typer.echo(render_entities_report(outcome.report))

    raise typer.Exit(code=int(outcome.exit_code))


@app.command("warm-up")
def warm_up(
    alias_map: list[Path] = typer.Option(
        [],
        "--alias-map",
        "-a",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Additional alias map YAML files to validate during warm-up (pass multiple times).",
    ),
) -> None:
    """Prime model caches and verify external service connectivity."""

    logger = logging.getLogger("filtra.cli")

    try:
        alias_paths = [_validate_file(path, "alias map") for path in alias_map]
        result = run_warmup(alias_map_paths=alias_paths)
    except FiltraError as exc:
        outcome = handle_domain_error(exc)
        raise typer.Exit(code=int(outcome.exit_code)) from exc
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Unexpected error during warm-up diagnostics.")
        raise typer.Exit(code=int(ExitCode.UNEXPECTED_ERROR)) from exc

    _render_warmup_result(result, quiet=_is_quiet_mode())
    raise typer.Exit(code=int(ExitCode.SUCCESS))


def entrypoint() -> None:
    """Execute the Typer application."""

    app()


__all__ = ["app", "entrypoint", "configure_logging", "ExitCode"]
