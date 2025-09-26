# Error Handling Strategy

### General Approach
- **Error Model:** Structured hierarchy rooted at `FiltraError` with modules raising `InputValidationError`, `PdfExtractionError`, `NERModelError`, `LLMRequestError`, and `ReportGenerationError`.
- **Exception Hierarchy:** Wrap lower-level exceptions at module boundaries; allow system errors (KeyboardInterrupt, MemoryError) to bubble.
- **Error Propagation:** Orchestrator catches domain errors, maps them to user-friendly messages, and sets exit codes while logging context.

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
- **Custom Exceptions:** `InputValidationError`, `RubricConfigError`, `NormalizationConflictError`.
- **User-Facing Errors:** Plain English messages plus hints (e.g., check file path, rerun warm-up).
- **Error Codes:** Exit codes 1 (general), 2 (input), 3 (external service), 4 (configuration).

#### Data Consistency
- **Transaction Strategy:** N/A (no persistent storage).
- **Compensation Logic:** On partial pipeline failure, produce rubric-only report with warning banner when possible.
- **Idempotency:** CLI reruns with identical inputs yield same results; warm-up cache prevents redundant downloads.

