# Technical Assumptions

### Repository Structure
- Monorepo (single Python project) for MVP simplicity.

### Service Architecture
- Monolith CLI application (no services); local NER inference + remote LLM API.

### Testing Requirements
- Unit + light integration tests (PDF extraction, entity normalization, prompt construction, CLI arg parsing).

### Additional Technical Assumptions and Requests
- Python 3.10+ on Windows 11; use `venv` + `requirements.txt` with pinned versions.
- Prefer pure-Python or wheel-available deps (Windows-friendly). Avoid requiring Visual C++ build tools.
- OpenRouter key via `OPENROUTER_API_KEY`; no secrets in code.
- Deterministic defaults: temperature=0; model settable via `--llm-model`.
- Logging via standard library `logging`; `--quiet` toggles level.
 - Default NER model should support ES/EN (e.g., `Davlan/bert-base-multilingual-cased-ner-hrl`); for EN-only environments, `dslim/bert-base-NER` is acceptable. CPU-only execution.
 - Provide a `warm-up` CLI that pre-downloads the NER model and tests OpenRouter connectivity.
 - Rubric weights are stored in `config/rubric.yaml` and versioned; defaults loaded at runtime with override capability.

### Third-Party Services (OpenRouter)
- Create an OpenRouter account at https://openrouter.ai/signup and verify the email address to enable API access.
- Generate an API key from https://openrouter.ai/keys, ensuring the required HTTP headers (HTTP-Referer, X-Title) noted in the architecture are configured when integrating.
- Store the key in the environment variable `OPENROUTER_API_KEY` (`$env:OPENROUTER_API_KEY` in PowerShell) and manage shared usage via GitHub Actions secrets or Windows Credential Manager.
