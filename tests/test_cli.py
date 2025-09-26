from __future__ import annotations

import logging
from pathlib import Path

import pytest
from typer.testing import CliRunner

from filtra.cli import ExitCode, app, configure_logging

runner = CliRunner(mix_stderr=False)


@pytest.fixture(autouse=True)
def reset_logging_state() -> None:
    """Ensure each test runs with a clean logging configuration."""

    configure_logging._configured = False  # type: ignore[attr-defined]
    configure_logging._level = logging.INFO  # type: ignore[attr-defined]
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.NOTSET)
    yield
    root.handlers.clear()
    root.setLevel(logging.NOTSET)
    configure_logging._configured = False  # type: ignore[attr-defined]
    configure_logging._level = logging.INFO  # type: ignore[attr-defined]


def _normalize(output: str) -> str:
    """Collapse whitespace to simplify assertions across Rich formatting."""

    return " ".join(output.split())


def test_root_help_lists_commands() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == int(ExitCode.SUCCESS)
    normalized = _normalize(result.stdout)
    assert "run" in normalized
    assert "warm-up" in normalized
    assert "--quiet" in normalized


def test_run_requires_required_options() -> None:
    result = runner.invoke(app, ["run"])

    assert result.exit_code == int(ExitCode.INPUT_ERROR)
    assert "Missing option" in result.stderr or "Usage" in result.stderr


def test_run_executes_with_valid_files(tmp_path: Path) -> None:
    resume = tmp_path / "resume.pdf"
    resume.write_text("resume")
    jd = tmp_path / "job.txt"
    jd.write_text("jd")

    result = runner.invoke(app, ["run", "--resume", str(resume), "--jd", str(jd)])

    assert result.exit_code == int(ExitCode.SUCCESS)
    assert "Pipeline execution is not yet implemented in this scaffold." in _normalize(result.stdout)


def test_quiet_flag_suppresses_info_logs(tmp_path: Path) -> None:
    resume = tmp_path / "resume.pdf"
    resume.write_text("resume")
    jd = tmp_path / "job.txt"
    jd.write_text("jd")

    result = runner.invoke(app, ["--quiet", "run", "--resume", str(resume), "--jd", str(jd)])

    assert result.exit_code == int(ExitCode.SUCCESS)
    assert "Pipeline execution is not yet implemented in this scaffold." not in _normalize(result.stdout)
    assert getattr(configure_logging, "_level", logging.INFO) == logging.WARNING

