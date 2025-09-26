"""Offline diagnostics helpers for the Filtra CLI."""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Tuple

_REQUIREMENTS_FILENAME = "requirements.txt"


@dataclass(frozen=True)
class HealthCheck:
    """Represents the outcome of an individual health validation."""

    name: str
    status: str
    detail: str
    remediation: str | None = None


@dataclass(frozen=True)
class HealthReport:
    """Aggregated health diagnostics for the Filtra CLI."""

    python_version: str
    huggingface_cache: Path
    dependency_pins: Tuple[str, ...]
    checks: Tuple[HealthCheck, ...]

    @property
    def overall_status(self) -> str:
        """Summarise overall readiness based on individual checks."""

        return "PASS" if all(check.status == "PASS" for check in self.checks) else "FAIL"


def collect_health_report(project_root: Path | None = None) -> HealthReport:
    """Gather offline diagnostics without invoking external services."""

    root = project_root or Path.cwd()
    python_check = _check_python_version()
    api_key_check = _check_api_key()
    proxy_check = _check_proxy_configuration()

    cache_path = _resolve_cache_directory()
    cache_check = _check_cache_directory(cache_path)

    pins = tuple(_load_dependency_pins(root / _REQUIREMENTS_FILENAME))
    dependency_check = _check_dependency_pins(pins)

    checks = (python_check, api_key_check, proxy_check, cache_check, dependency_check)

    return HealthReport(
        python_version=_format_python_version(),
        huggingface_cache=cache_path,
        dependency_pins=pins,
        checks=checks,
    )


def _check_python_version() -> HealthCheck:
    version = _format_python_version()
    interpreter_ok = sys.version_info.major == 3 and sys.version_info.minor >= 10

    if interpreter_ok:
        detail = f"Detected Python {version}; compatible with Filtra requirements."
        return HealthCheck(name="Python runtime", status="PASS", detail=detail)

    remediation = "Install Python 3.10.11 and recreate the virtual environment."
    detail = (
        f"Detected Python {version}; Filtra requires 3.10.x for Windows compatibility."
    )
    return HealthCheck(
        name="Python runtime",
        status="FAIL",
        detail=detail,
        remediation=remediation,
    )


def _check_api_key() -> HealthCheck:
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if api_key:
        masked = f"{len(api_key)} characters"
        detail = f"OPENROUTER_API_KEY detected ({masked})."
        return HealthCheck(name="OpenRouter API key", status="PASS", detail=detail)

    remediation = (
        "Set OPENROUTER_API_KEY before running 'filtra run'. PowerShell example: "
        "setx OPENROUTER_API_KEY 'sk-...'."
    )
    return HealthCheck(
        name="OpenRouter API key",
        status="FAIL",
        detail="OPENROUTER_API_KEY is not configured.",
        remediation=remediation,
    )


def _check_proxy_configuration() -> HealthCheck:
    proxy_vars = {
        "HTTPS_PROXY": os.getenv("HTTPS_PROXY"),
        "HTTP_PROXY": os.getenv("HTTP_PROXY"),
        "NO_PROXY": os.getenv("NO_PROXY"),
    }

    configured = any(value for value in proxy_vars.values())
    configured_vars = ", ".join(name for name, value in proxy_vars.items() if value)

    if configured:
        detail = f"Proxy variables detected: {configured_vars}."
        return HealthCheck(name="Proxy configuration", status="PASS", detail=detail)

    remediation = (
        "Set HTTPS_PROXY/HTTP_PROXY or configure NO_PROXY to comply with corporate network "
        "policies before invoking remote APIs."
    )
    detail = "No proxy environment variables detected; direct internet access assumed."
    return HealthCheck(
        name="Proxy configuration",
        status="FAIL",
        detail=detail,
        remediation=remediation,
    )


def _resolve_cache_directory() -> Path:
    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "filtra" / "models"

    transformers_cache = os.getenv("TRANSFORMERS_CACHE")
    if transformers_cache:
        return Path(transformers_cache)

    hf_home = os.getenv("HF_HOME")
    if hf_home:
        return Path(hf_home) / "transformers"

    return Path.home() / ".cache" / "filtra" / "models"


def _check_cache_directory(cache_path: Path) -> HealthCheck:
    if cache_path.exists():
        detail = f"Model cache present at {cache_path}."
        return HealthCheck(name="Model cache", status="PASS", detail=detail)

    remediation = "Run 'filtra warm-up' to download model weights into the cache directory."
    detail = f"No cached models found at {cache_path}."
    return HealthCheck(
        name="Model cache",
        status="FAIL",
        detail=detail,
        remediation=remediation,
    )


def _load_dependency_pins(requirements_path: Path) -> Iterable[str]:
    if not requirements_path.exists():
        return []

    pins: list[str] = []
    for line in requirements_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "==" in stripped:
            pins.append(stripped)
        if len(pins) >= 5:
            break
    return pins


def _check_dependency_pins(pins: Iterable[str]) -> HealthCheck:
    pins_tuple = tuple(pins)
    if pins_tuple:
        detail = "Key dependencies: " + ", ".join(pins_tuple)
        return HealthCheck(name="Dependency pins", status="PASS", detail=detail)

    remediation = "Generate requirements.txt with 'pip-compile' to lock dependencies."
    return HealthCheck(
        name="Dependency pins",
        status="FAIL",
        detail="No dependency pins discovered in requirements.txt.",
        remediation=remediation,
    )


def _format_python_version() -> str:
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


__all__ = ["HealthCheck", "HealthReport", "collect_health_report"]
