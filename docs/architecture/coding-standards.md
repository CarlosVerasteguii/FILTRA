# Coding Standards

### Core Standards
- **Languages & Runtimes:** Python 3.10.11 only; ensure Typer CLI remains PowerShell-friendly.
- **Style & Linting:** Format with `black` (line length 100) and lint with `ruff` including import sorting.
- **Test Organization:** Mirror package structure under `tests/` using `test_*.py`; keep golden sample assertions in `tests/golden/`.

### Critical Rules
- **CLI Output Discipline:** Only reporting layer writes to stdout/stderr; other modules must return data or raise `FiltraError` derivatives.
- **External Calls Isolation:** All HTTP/OpenRouter interactions go through `filtra.llm.client`; no ad-hoc requests elsewhere.
- **Entity Normalization:** Every NER result must pass through AliasMap normalization before scoring or reporting.

### Risk Review
- Windows behaviour can drift if devs rely on macOS/Linux; CI must run on Windows runners.
- Black/Ruff compliance needs automation (pre-commit or CI) to avoid style drift.
- Debugging prints are disallowed; provide `--debug` flag to elevate logging instead.
- FR13 hinges on normalization; cover multilingual edge cases in tests to prevent shortcuts.

