# Test Strategy and Standards

### Testing Philosophy
- **Approach:** Test-after with fast feedback; each story delivers unit + targeted integration coverage plus golden sample regression.
- **Coverage Goals:** ≥85% overall statement coverage; 100% on scoring/normalization modules.
- **Test Pyramid:** Unit-heavy, focused integration (PDF parsing, LLM adapter), CLI golden-sample smoke tests.

### Unit Tests
- **Framework:** pytest 8.3.2
- **File Convention:** `tests/<module>/test_*.py`
- **Location:** Mirrors package structure under `tests/`
- **Mocking Library:** pytest-mock (`unittest.mock` wrappers)
- **Coverage Requirement:** ≥85% per module via `coverage run -m pytest`
  **AI Agent Requirements:**
  - Test all public functions/methods
  - Include error-path assertions (invalid CLI args, PDF failure, OpenRouter errors)
  - Follow Arrange/Act/Assert; use structured log assertions
  - Mock external HTTP via httpx.MockTransport or pytest-httpx
  - Validate language detection defaults (es-MX) against English overrides using sample fixtures
  - Assert HTTP client honours proxy environment variables via patched settings

### Integration Tests
- **Scope:** PDF extraction + normalization pipeline; language detection/localization with es-MX default and overrides; scoring orchestrator with real rubric/alias data; CLI run with golden samples (offline mock).
- **Location:** `tests/integration/test_pipeline.py`, `tests/integration/test_cli_run.py`
- **Test Infrastructure:**
  - **OpenRouter:** pytest-httpx mock server for deterministic responses
  - **HuggingFace NER:** Cached model loaded once per session (mark slow; reuse fixture)

### End-to-End Tests
- **Framework:** pytest (subprocess invocation)
- **Scope:** `python -m filtra run ...` against `samples/` inputs, compare JSON snapshot
- **Environment:** GitHub Actions Windows + local machines
- **Test Data:** Golden outputs under `samples/expected/`; regenerate via approved script when specs change

### Test Data Management
- **Strategy:** Version-control anonymized fixtures; avoid storing real PII
- **Fixtures:** `tests/fixtures/` for ES/EN text snippets; `samples/inputs/` for PDFs/JDs demonstrating bilingual scenarios.
- **Factories:** `tests/factories.py` for rubric variants
- **Cleanup:** Use `tmp_path`; integration tests must not mutate global model cache

### Continuous Testing
- **CI Integration:** GitHub Actions workflow runs lint → unit → integration → golden sample compare on Windows & Ubuntu matrices
- **Performance Tests:** Manual observation only; record runtime in warm-up outputs as heuristic
- **Security Tests:** `pip-audit` dependency scan and `gitleaks` for secrets as part of CI

### Risk Review
- Golden sample checks rely on stable mocked LLM output; provide regeneration script + documented workflow.
- Model downloads can flake in CI; prime cache via warm-up and cache artifacts.
- Windows CLI tests require env vars; fixtures must stub `OPENROUTER_API_KEY`.
- Excessive mocking can mask integration gaps; ensure integration suites exercise real pipeline paths.
- No automated perf suite; monitor warm-up runtime logs for regressions.

