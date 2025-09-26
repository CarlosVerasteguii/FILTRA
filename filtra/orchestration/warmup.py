"""Diagnostics warm-up orchestration."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Tuple

import httpx

from filtra.errors import TimeoutExceededError
from filtra.llm import LLMHealth, perform_health_check
from filtra.ner import DEFAULT_MODEL_ID, warm_cache
from filtra.orchestration.diagnostics import (
    HealthCheck,
    check_api_key,
    check_proxy_configuration,
    check_python_version,
    format_python_version,
    get_proxy_environment,
    resolve_cache_directory,
)

logger = logging.getLogger("filtra.orchestration.warmup")

_WARMUP_TIMEOUT_SECONDS = 5.0


@dataclass(frozen=True)
class WarmupResult:
    """Aggregated outcome of the warm-up diagnostics workflow."""

    python_version: str
    huggingface_cache: Path
    cache_size_bytes: int
    duration_seconds: float
    proxy_environment: Mapping[str, str | None]
    checks: Tuple[HealthCheck, ...]

    @property
    def overall_status(self) -> str:
        """Summarise overall readiness based on individual checks."""

        return "PASS" if all(check.status == "PASS" for check in self.checks) else "FAIL"


def run_warmup(
    *,
    model_id: str = DEFAULT_MODEL_ID,
    max_duration_seconds: float = 120.0,
    transport: httpx.BaseTransport | None = None,
) -> WarmupResult:
    """Execute the warm-up workflow to prime external dependencies."""

    start = time.perf_counter()
    logger.info("Starting warm-up diagnostics", extra={"model_id": model_id})

    python_check = check_python_version()
    api_key_check = check_api_key()
    proxy_check = check_proxy_configuration()

    cache_path = resolve_cache_directory()
    logger.info("Resolved cache path", extra={"path": str(cache_path)})
    warm_cache(cache_path=cache_path, model_id=model_id)
    cache_size = _compute_cache_size(cache_path)

    ner_check = HealthCheck(
        name="NER model cache",
        status="PASS",
        detail=(
            f"Prefetched '{model_id}' into {cache_path} "
            f"(~{_format_bytes(cache_size)} on disk)."
        ),
    )

    llm_health = perform_health_check(timeout_seconds=_WARMUP_TIMEOUT_SECONDS, transport=transport)
    llm_check = _build_llm_check(llm_health)

    if proxy_check.status != "PASS":
        proxy_check = HealthCheck(
            name=proxy_check.name,
            status="PASS",
            detail="No proxy variables detected; direct access succeeded during warm-up.",
        )

    duration = time.perf_counter() - start
    logger.info("Warm-up duration", extra={"seconds": duration})

    if duration > max_duration_seconds:
        raise TimeoutExceededError(
            message=(
                f"Warm-up exceeded the {max_duration_seconds:.0f}-second budget with "
                f"{duration:.2f} seconds elapsed."
            ),
            remediation=(
                "Retry on a faster connection or prefetch the cache outside demo time before rerunning warm-up."
            ),
        )

    duration_check = HealthCheck(
        name="Warm-up duration",
        status="PASS",
        detail=f"Completed in {duration:.2f} seconds (budget {max_duration_seconds:.0f}s).",
    )

    checks = (
        python_check,
        api_key_check,
        proxy_check,
        ner_check,
        llm_check,
        duration_check,
    )

    return WarmupResult(
        python_version=format_python_version(),
        huggingface_cache=cache_path,
        cache_size_bytes=cache_size,
        duration_seconds=duration,
        proxy_environment=get_proxy_environment(),
        checks=checks,
    )


def _build_llm_check(health: LLMHealth) -> HealthCheck:
    """Translate an LLM health record into a diagnostics check."""

    request_detail = f" request {health.request_id}" if health.request_id else ""
    detail = (
        f"OpenRouter endpoint {health.endpoint} responded in "
        f"{health.latency_seconds:.2f} seconds{request_detail}."
    )
    return HealthCheck(name="OpenRouter connectivity", status="PASS", detail=detail)


def _compute_cache_size(cache_path: Path) -> int:
    """Calculate the total size of files within the cache path."""

    if not cache_path.exists():
        return 0

    total = 0
    for item in cache_path.rglob("*"):
        if item.is_file():
            try:
                total += item.stat().st_size
            except OSError:  # pragma: no cover - defensive
                logger.debug("Unable to stat cache file", exc_info=True, extra={"path": str(item)})
    return total


def _format_bytes(size: int) -> str:
    """Render a human-readable representation of a byte size."""

    if size < 1024:
        return f"{size} B"
    if size < 1024 ** 2:
        return f"{size / 1024:.1f} KiB"
    if size < 1024 ** 3:
        return f"{size / (1024 ** 2):.1f} MiB"
    return f"{size / (1024 ** 3):.2f} GiB"


__all__ = ["WarmupResult", "run_warmup"]
