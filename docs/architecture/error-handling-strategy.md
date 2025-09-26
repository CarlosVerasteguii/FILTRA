# Error Handling Strategy

### General Approach
- **Error Model:** Structured hierarchy rooted at `FiltraError` with modules raising `InputValidationError`, `PdfExtractionError`, `NERModelError`, `LLMRequestError`, and `TimeoutExceededError`. Each exception carries optional remediation text for the CLI to surface.
- **Exception Hierarchy:** Wrap lower-level exceptions at module boundaries; allow system errors (KeyboardInterrupt, MemoryError) to bubble.
- **Error Propagation:** The orchestration runner translates domain errors into deterministic exit codes, emits remediation logging, and keeps secrets out of log output.

### Logging Standards
- **Library:** stdlib `logging` with `rich.logging.RichHandler`.
- **Format:** `%(asctime)s | %(levelname)s | %(name)s | %(message)s` (Rich formatted).
- **Levels:** DEBUG (opt-in), INFO (default progress), WARNING (recoverable), ERROR (terminal).
- **Required Context:** Correlation `run_id` per EvaluationRun; logger names reflect module; never log resume/JD content, only sanitized metadata.

### Error Handling Patterns

#### External API Errors
- **Retry Policy:** `tenacity` exponential backoff (base 1s, max 3 attempts) for timeouts/5xx.
- **Circuit Breaker:** Not needed for single-run CLI; rely on bounded retries + exit messaging.
- **Timeout Configuration:** `httpx` total timeout 20s (connect/read split); warm-up uses 5s limit.
- **Error Translation:** Map to `LLMRequestError` with status code and offline guidance.

#### Business Logic Errors
- **Custom Exceptions:** `InputValidationError`, `PdfExtractionError`, `NERModelError`, `LLMRequestError`, `TimeoutExceededError`.
- **User-Facing Errors:** Plain English messages plus hints (e.g., check file path, rerun warm-up).
- **Exit Code Map:**
  - `0` Success
  - `2` Invalid input (missing files or CLI arguments)
  - `3` Parse error (resume/JD unreadable)
  - `4` NER failure (model load/execution)
  - `5` LLM gateway failure (API key/proxy)
  - `6` Timeout (orchestration exceeded allowed window)

#### Data Consistency
- **Transaction Strategy:** N/A (no persistent storage).
- **Compensation Logic:** On partial pipeline failure, produce rubric-only report with warning banner when possible.
- **Idempotency:** CLI reruns with identical inputs yield same results; warm-up cache prevents redundant downloads.


