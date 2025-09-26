from __future__ import annotations

import logging
from pathlib import Path

import pytest
from typer.testing import CliRunner

from filtra.cli import ExitCode, app, configure_logging
from filtra.errors import (
    InputValidationError,
    LLMRequestError,
    NERModelError,
    PdfExtractionError,
    TimeoutExceededError,
)

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

    assert result.exit_code == int(ExitCode.INVALID_INPUT)
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


def test_run_handles_input_validation_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    resume = tmp_path / "resume.pdf"
    resume.write_text("resume")
    jd = tmp_path / "jd.txt"
    jd.write_text("jd")

    def _raise_validation(path: Path, description: str) -> Path:
        raise InputValidationError("Invalid input", remediation="Provide correct files")

    monkeypatch.setattr("filtra.cli._validate_file", _raise_validation)

    result = runner.invoke(
        app,
        ["run", "--resume", str(resume), "--jd", str(jd)],
        catch_exceptions=False,
    )

    assert result.exit_code == int(ExitCode.INVALID_INPUT)
    combined = _normalize(result.stdout + result.stderr)
    assert "Invalid input" in combined
    assert "Provide correct files" in combined


@pytest.mark.parametrize(
    ("error_factory", "expected_code", "expected_message"),
    [
        (
            lambda: PdfExtractionError("Unable to parse file", remediation="Verify PDF integrity"),
            ExitCode.PARSE_ERROR,
            "Unable to parse file",
        ),
        (
            lambda: NERModelError("NER weights missing", remediation="Run filtra warm-up"),
            ExitCode.NER_ERROR,
            "NER weights missing",
        ),
        (
            lambda: LLMRequestError("Gateway unavailable", remediation="Set OPENROUTER_API_KEY"),
            ExitCode.LLM_ERROR,
            "Gateway unavailable",
        ),
        (
            lambda: TimeoutExceededError("Processing timed out", remediation="Retry later"),
            ExitCode.TIMEOUT,
            "Processing timed out",
        ),
    ],
)
def test_run_maps_domain_errors(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    error_factory,
    expected_code: ExitCode,
    expected_message: str,
) -> None:
    resume = tmp_path / "resume.pdf"
    resume.write_text("resume")
    jd = tmp_path / "jd.txt"
    jd.write_text("jd")

    def _raise_error(*, resume_path: Path, jd_path: Path) -> None:
        raise error_factory()

    monkeypatch.setattr("filtra.orchestration.runner._perform_run", _raise_error)

    result = runner.invoke(
        app,
        ["run", "--resume", str(resume), "--jd", str(jd)],
        catch_exceptions=False,
    )

    assert result.exit_code == int(expected_code)
    combined = _normalize(result.stdout + result.stderr)
    assert expected_message in combined
    assert "Remediation" in combined


def test_health_flag_reports_pass(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(project_root)

    cache_dir = tmp_path / "filtra" / "models"
    cache_dir.mkdir(parents=True)

    env = {
        "OPENROUTER_API_KEY": "token-value",
        "HTTPS_PROXY": "http://proxy.local:8080",
        "LOCALAPPDATA": str(tmp_path),
    }

    result = runner.invoke(app, ["--health"], env=env, catch_exceptions=False)

    assert result.exit_code == int(ExitCode.SUCCESS)
    combined = _normalize(result.stdout)
    assert "Filtra environment diagnostics" in combined
    assert "[PASS] OpenRouter API key" in combined
    assert "[PASS] Proxy configuration" in combined
    assert "Overall status: PASS" in combined


def test_health_flag_reports_failures(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(project_root)

    env = {
        "LOCALAPPDATA": str(tmp_path),
    }

    result = runner.invoke(app, ["--health"], env=env, catch_exceptions=False)

    assert result.exit_code == int(ExitCode.SUCCESS)
    combined = _normalize(result.stdout)
    assert "[FAIL] OpenRouter API key" in combined
    assert "Remediation" in combined
    assert "Overall status: FAIL" in combined

