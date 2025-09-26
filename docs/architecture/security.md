# Security

### Input Validation
- **Validation Library:** Typer parameter definitions plus Pydantic models (`EvaluationRunOptions`, `RubricConfig`).
- **Validation Location:** `filtra/cli.py` for CLI args; `filtra/utils/config_loader.py` for YAML configs.
- **Required Rules:** Validate all CLI inputs before orchestration; reject unreadable files; Pydantic enforces rubric/alias schema; normalize and sanitize user-provided paths.

### Authentication & Authorization
- **Auth Method:** Bearer token via `OPENROUTER_API_KEY` environment variable.
- **Session Management:** Stateless CLI; key loaded per invocation.
- **Required Patterns:** Fail fast when key missing/empty; never log or echo secrets.

### Secrets Management
- **Development:** Document variables in `.env.example`; optional `python-dotenv` for local runs (excluded from prod).
- **Production/Demo:** Inject via environment/secret manager (GitHub Actions secrets, Windows Credential Manager).
- **Code Requirements:** No hardcoded secrets; access via environment only; redact sensitive data from logs and reports.

### API Security
- **Rate Limiting:** `tenacity` exponential backoff (max 3 retries) to respect OpenRouter quotas.
- **CORS Policy:** Not applicable (CLI client) but never expose API key in generated artifacts.
- **Security Headers:** Always send `Authorization`, `HTTP-Referer`, `X-Title`; omit unnecessary headers.
- **Proxy Support:** Automatically respects HTTPS_PROXY/HTTP_PROXY/NO_PROXY environment variables; document required outbound endpoints.
- **HTTPS Enforcement:** Force `https://openrouter.ai/api/v1`; reject non-HTTPS endpoints.

### Data Protection
- **Encryption at Rest:** None required; no persistent storage of resume/JD content. Avoid temporary files or delete immediately if created.
- **Encryption in Transit:** HTTPS/TLS 1.2+ for all remote calls (OpenRouter, HuggingFace downloads).
- **PII Handling:** Treat resumes/JDs as sensitive; operate in-memory; scrub PII from logs and deterministic outputs.
- **Logging Restrictions:** Only log filenames, status codes, metrics; never raw text or LLM responses containing candidate data.

### Dependency Security
- **Scanning Tool:** `pip-audit` in CI; optional `bandit` security linting.
- **Update Policy:** Review pinned versions monthly or upon advisories; regenerate `requirements.txt` with `pip-compile`.
- **Approval Process:** New deps require architecture review; confirm Windows wheels/compatibility before adoption.

### Security Testing
- **SAST Tool:** `ruff` security rules plus `bandit` focused on normalization and HTTP client modules.
- **DAST Tool:** Not applicable (no hosted surface); rely on integration tests with mocked endpoints.
- **Penetration Testing:** Manual review before demos; verify warm-up logs redact sensitive values and fallback behavior remains safe.
