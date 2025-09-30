from __future__ import annotations

import logging
from pathlib import Path

import pytest
from typer.testing import CliRunner

from filtra.configuration import AliasMapDetails
from filtra.cli import ExitCode, app, configure_logging
from filtra.errors import (
    InputValidationError,
    LLMRequestError,
    NERModelError,
    PdfExtractionError,
    TimeoutExceededError,
)
from filtra.ner import ExtractedEntity, ExtractedEntityCollection
from filtra.orchestration import ExecutionOutcome, HealthCheck, WarmupResult
from filtra.utils import LoadedDocument

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


@pytest.fixture(autouse=True)
def stub_ner_pipeline(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoid real model downloads during CLI tests by stubbing the extractor."""

    def _fake_extract_entities(**kwargs: object) -> ExtractedEntityCollection:
        language = (kwargs.get("language_hint") or "und").lower()
        return ExtractedEntityCollection(
            entities=(
                ExtractedEntity(
                    text="Filtra Technologies",
                    category="company",
                    confidence=0.99,
                    span=(0, 19),
                    source_language=language,
                ),
                ExtractedEntity(
                    text="Python",
                    category="skill",
                    confidence=0.95,
                    span=(20, 26),
                    source_language=language,
                ),
            ),
            language_profile=language,
        )

    monkeypatch.setattr("filtra.orchestration.runner.extract_entities", _fake_extract_entities)


@pytest.fixture
def windows_samples(tmp_path: Path) -> tuple[Path, Path]:
    """Copy the bundled Windows samples into a temporary path with spaces."""

    project_root = Path(__file__).resolve().parents[1]
    samples_dir = project_root / "samples" / "inputs"
    resume_src = samples_dir / "resume_windows_sample.txt"
    jd_src = samples_dir / "jd_windows_sample.txt"
    assert resume_src.exists(), "resume_windows_sample.txt missing from repository"
    assert jd_src.exists(), "jd_windows_sample.txt missing from repository"

    target_dir = tmp_path / "Windows Samples"
    target_dir.mkdir(parents=True, exist_ok=True)

    resume_dst = target_dir / resume_src.name
    jd_dst = target_dir / jd_src.name
    resume_dst.write_bytes(resume_src.read_bytes())
    jd_dst.write_bytes(jd_src.read_bytes())
    return resume_dst, jd_dst


def _normalize(output: str) -> str:
    """Collapse whitespace to simplify assertions across Rich formatting."""

    return " ".join(output.split())


def _warmup_result() -> WarmupResult:
    cache_path = Path("C:/cache/filtra/models")
    alias_details = AliasMapDetails(
        sources=(Path("config/alias_map.yaml"),),
        canonical_count=3,
        alias_count=6,
        locale_codes=("es",),
    )
    checks = (
        HealthCheck(name="Python runtime", status="PASS", detail="Detected Python 3.10.11."),
        HealthCheck(
            name="Alias map configuration",
            status="PASS",
            detail="3 groups, 6 aliases (locales: es; sources: config/alias_map.yaml).",
        ),
        HealthCheck(
            name="OpenRouter connectivity",
            status="PASS",
            detail="Endpoint responded in 0.20 seconds.",
        ),
    )
    return WarmupResult(
        python_version="3.10.11",
        huggingface_cache=cache_path,
        cache_size_bytes=2048,
        duration_seconds=2.3,
        proxy_environment={
            "HTTPS_PROXY": "http://proxy.local:8080",
            "HTTP_PROXY": None,
            "NO_PROXY": "localhost",
        },
        alias_map_details=alias_details,
        checks=checks,
    )


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
    resume = tmp_path / "resume.txt"
    resume.write_text("resume")
    jd = tmp_path / "job.txt"
    jd.write_text("jd")

    result = runner.invoke(app, ["run", "--resume", str(resume), "--jd", str(jd)])

    assert result.exit_code == int(ExitCode.SUCCESS)
    output = result.stdout
    assert "Resume resume.txt decoded as UTF-8 (with BOM)" in output
    assert "Job description job.txt decoded as UTF-8 (with BOM)" in output
    assert "Pipeline execution is not yet implemented in this scaffold." in output


def test_run_accepts_pdf_resume(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    resume = tmp_path / "resume.pdf"
    resume.write_bytes(b"%PDF")
    jd = tmp_path / "job.txt"
    jd.write_text("jd")

    loaded = LoadedDocument(path=resume, text="Resumen normalizado", encoding="utf-8")

    def _load_pdf(path: Path, *, description: str) -> LoadedDocument:
        assert description == "resume"
        assert path == resume
        return loaded

    monkeypatch.setattr("filtra.orchestration.runner.extract_pdf_text", _load_pdf)

    result = runner.invoke(app, ["run", "--resume", str(resume), "--jd", str(jd)])

    assert result.exit_code == int(ExitCode.SUCCESS)
    output = result.stdout
    combined = _normalize(output)
    assert "Resume resume.pdf decoded as" in combined
    assert "UTF-8" in combined
    assert "Pipeline execution is not yet implemented in this scaffold." in output


def test_run_reports_pdf_parse_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    resume = tmp_path / "resume.pdf"
    resume.write_bytes(b"%PDF")
    jd = tmp_path / "job.txt"
    jd.write_text("jd")

    def _raise(path: Path, *, description: str) -> LoadedDocument:
        raise PdfExtractionError("Encrypted PDF detected", remediation="Export an unprotected PDF")

    monkeypatch.setattr("filtra.orchestration.runner.extract_pdf_text", _raise)

    result = runner.invoke(
        app,
        ["run", "--resume", str(resume), "--jd", str(jd)],
        catch_exceptions=False,
    )

    assert result.exit_code == int(ExitCode.PARSE_ERROR)
    combined = _normalize(result.stdout + result.stderr)
    assert "Encrypted PDF detected" in combined
    assert "Remediation" in combined

def test_run_reports_windows_sample_encodings(windows_samples: tuple[Path, Path]) -> None:
    resume, jd = windows_samples

    result = runner.invoke(app, ["run", "--resume", str(resume), "--jd", str(jd)])

    assert result.exit_code == int(ExitCode.SUCCESS)
    output = result.stdout
    assert "Resume resume_windows_sample.txt decoded as UTF-8 (with BOM)" in output
    assert "Job description jd_windows_sample.txt decoded as Windows-1252" in output

def test_quiet_flag_suppresses_info_logs(tmp_path: Path) -> None:
    resume = tmp_path / "resume.txt"
    resume.write_text("resume")
    jd = tmp_path / "job.txt"
    jd.write_text("jd")

    result = runner.invoke(app, ["--quiet", "run", "--resume", str(resume), "--jd", str(jd)])

    assert result.exit_code == int(ExitCode.SUCCESS)
    assert "Pipeline execution is not yet implemented in this scaffold." not in _normalize(
        result.stdout
    )
    assert getattr(configure_logging, "_level", logging.INFO) == logging.WARNING


def test_run_handles_input_validation_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    resume = tmp_path / "resume.txt"
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


def test_run_accepts_custom_ner_model(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    resume = tmp_path / "resume.txt"
    resume.write_text("resume")
    jd = tmp_path / "job.txt"
    jd.write_text("jd")

    recorded: dict[str, object] = {}

    def _fake_run_pipeline(**kwargs: object) -> ExecutionOutcome:
        recorded["resume"] = kwargs.get("resume_path")
        recorded["jd"] = kwargs.get("jd_path")
        recorded["ner_model"] = kwargs.get("ner_model")
        recorded["alias_map_paths"] = kwargs.get("alias_map_paths")
        return ExecutionOutcome(exit_code=ExitCode.SUCCESS, status="success", message="ok")

    monkeypatch.setattr("filtra.cli.run_pipeline", _fake_run_pipeline)

    result = runner.invoke(
        app,
        [
            "run",
            "--resume",
            str(resume),
            "--jd",
            str(jd),
            "--ner-model",
            "custom/company-ner",
        ],
    )

    assert result.exit_code == int(ExitCode.SUCCESS)
    assert recorded["ner_model"] == "custom/company-ner"
    assert recorded["resume"] == resume.resolve()
    assert recorded["jd"] == jd.resolve()


def test_run_rejects_empty_ner_model(tmp_path: Path) -> None:
    resume = tmp_path / "resume.txt"
    resume.write_text("resume")
    jd = tmp_path / "job.txt"
    jd.write_text("jd")

    result = runner.invoke(
        app,
        [
            "run",
            "--resume",
            str(resume),
            "--jd",
            str(jd),
            "--ner-model",
            "",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == int(ExitCode.INVALID_INPUT)
    combined = _normalize(result.stdout + result.stderr)
    assert "NER model identifier cannot be empty." in combined


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
    resume = tmp_path / "resume.txt"
    resume.write_text("resume")
    jd = tmp_path / "jd.txt"
    jd.write_text("jd")

    def _raise_error(**kwargs: object) -> None:
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


def test_warmup_command_renders_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("filtra.cli.run_warmup", lambda *_, **__: _warmup_result())

    result = runner.invoke(app, ["warm-up"], catch_exceptions=False)

    assert result.exit_code == int(ExitCode.SUCCESS)
    combined = _normalize(result.stdout)
    assert "Filtra warm-up diagnostics" in combined
    assert "Cache on disk" in combined
    assert "Alias map sources" in combined
    assert "Alias map coverage" in combined
    assert "2.0 KiB" in combined
    assert "[PASS] Alias map configuration" in combined
    assert "[PASS] OpenRouter connectivity" in combined


def test_warmup_command_respects_quiet(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("filtra.cli.run_warmup", lambda *_, **__: _warmup_result())

    result = runner.invoke(app, ["--quiet", "warm-up"], catch_exceptions=False)

    assert result.exit_code == int(ExitCode.SUCCESS)
    combined = _normalize(result.stdout)
    assert "Proxy environment" not in combined
    assert "Warm-up PASS" in combined
    assert "alias map" in combined.lower()
    assert "[PASS] Alias map configuration" in combined
    assert "[PASS] OpenRouter connectivity" in combined


def test_warmup_command_maps_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise() -> None:
        raise LLMRequestError("Gateway unavailable", remediation="Set OPENROUTER_API_KEY")

    monkeypatch.setattr("filtra.cli.run_warmup", lambda *_, **__: _raise())

    result = runner.invoke(app, ["warm-up"], catch_exceptions=False)

    assert result.exit_code == int(ExitCode.LLM_ERROR)
    combined = _normalize(result.stdout + result.stderr)
    assert "Gateway unavailable" in combined
    assert "Remediation" in combined


def test_run_accepts_windows_1252_job_description(tmp_path: Path) -> None:
    resume = tmp_path / "resume.txt"
    resume.write_text("perfil", encoding="utf-8")
    jd = tmp_path / "job-desc.txt"
    jd.write_bytes("requisición".encode("cp1252"))

    result = runner.invoke(app, ["run", "--resume", str(resume), "--jd", str(jd)])

    assert result.exit_code == int(ExitCode.SUCCESS)
    assert "Windows-1252" in result.stdout


def test_run_reports_encoding_failure(tmp_path: Path) -> None:
    resume = tmp_path / "resume.txt"
    resume.write_text("perfil", encoding="utf-8")
    jd = tmp_path / "job-desc.txt"
    jd.write_bytes(bytes([0x81, 0x82, 0x83]))

    result = runner.invoke(
        app,
        ["run", "--resume", str(resume), "--jd", str(jd)],
        catch_exceptions=False,
    )

    assert result.exit_code == int(ExitCode.INVALID_INPUT)
    combined = _normalize(result.stdout + result.stderr)
    assert "not encoded" in combined
    assert "Windows-1252" in combined


def test_run_handles_paths_with_spaces_and_normalizes_newlines(tmp_path: Path) -> None:
    resume = tmp_path / "resume spaced.txt"
    resume.write_text("línea uno\r\nlínea dos", encoding="utf-8")
    jd = tmp_path / "job desc.txt"
    jd.write_text("descriptor\r\n", encoding="utf-8")

    result = runner.invoke(app, ["run", "--resume", str(resume), "--jd", str(jd)])

    assert result.exit_code == int(ExitCode.SUCCESS)
    output = result.stdout
    assert '"resume spaced.txt"' in output
    assert '"job desc.txt"' in output
    assert "\r" not in output


def test_run_accepts_alias_map_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    resume = tmp_path / "resume.txt"
    resume.write_text("perfil", encoding="utf-8")
    jd = tmp_path / "job.txt"
    jd.write_text("rol", encoding="utf-8")
    alias_file = tmp_path / "alias-map.yaml"
    alias_file.write_text("aliases: {}\n", encoding="utf-8")

    captured: dict[str, object] = {}

    def _run_pipeline(**kwargs: object) -> ExecutionOutcome:
        captured["alias_map_paths"] = kwargs.get("alias_map_paths")
        return ExecutionOutcome(exit_code=ExitCode.SUCCESS, status="success", message=None)

    monkeypatch.setattr("filtra.cli.run_pipeline", _run_pipeline)

    result = runner.invoke(
        app,
        [
            "run",
            "--resume",
            str(resume),
            "--jd",
            str(jd),
            "--alias-map",
            str(alias_file),
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == int(ExitCode.SUCCESS)
    resolved_paths = captured.get("alias_map_paths")
    assert isinstance(resolved_paths, list)
    assert alias_file.resolve() in resolved_paths
