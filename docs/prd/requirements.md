# Requirements

### Functional (FR)
1. FR1: The tool shall accept a single resume in PDF format and a job description in plain text file via CLI arguments.
2. FR2: The tool shall extract readable plain text from the provided PDF resume.
3. FR3: The tool shall run a local HuggingFace NER pipeline to extract structured entities (e.g., skills, companies) from the resume text.
4. FR4: The tool shall send the resume text, extracted entities, and job description to an LLM via OpenRouter to obtain a compatibility score and qualitative analysis.
5. FR5: The LLM output shall include: (a) an overall compatibility score (0–100), (b) a concise justification, (c) top strengths, and (d) key gaps relative to the job description.
6. FR6: The tool shall render a terminal-friendly report that combines LLM insights with the NER entities in a clear, readable format.
7. FR7: The CLI shall provide usage/help flags and accept at minimum: --resume <pdf_path>, --jd <txt_path>; optional flags may include model/config options.
8. FR8: The tool shall read the OpenRouter API key from an environment variable and must not require hardcoding secrets.
9. FR9: The tool shall handle common errors (missing files, PDF parsing failures, API timeouts/errors, model load errors) and exit with a non-zero code on failure.
10. FR10: The tool shall print minimal progress and error messages suitable for a single-run CLI workflow.
11. FR11: The tool shall compute a 0–100 compatibility score using a defined rubric with weighted criteria (e.g., skills match, experience relevance); sub-scores shall be included in the report.
12. FR12: The repository shall include 2–3 golden sample inputs (resume + JD) and an expected report schema to validate output shape.
13. FR13: The tool shall normalize and de-duplicate extracted entities before rendering the report, including casefolding, trimming, and application of an alias map; normalization should be language-agnostic (ES/EN).
14. FR14: The CLI shall support `--llm-model`, `--ner-model`, and prompt parameter flags (e.g., temperature, max tokens) with validation and sane defaults.
15. FR15: The tool shall detect unavailable dependencies (e.g., offline OpenRouter or missing NER weights) and degrade gracefully with a clear notice (e.g., skip NER or substitute a mock LLM response).
16. FR16: Provide an optional warm-up command to prefetch models and verify connectivity (OpenRouter, model cache) before first demo run.
17. FR17: Auto-detect input language (resume/JD) and set prompt language accordingly; allow override via `--lang`.
18. FR18: Implement and document flags `--quiet`, `--wide`, `--seed`, and subcommand `warm-up`; ensure they appear in `--help` with PowerShell examples.

### Non-Functional (NFR)
1. NFR1 (Privacy & Security): Do not store resume or job description content beyond immediate processing; do not log sensitive text; API keys must be provided via environment variables only.
2. NFR2 (Performance): Warm run target under 60–120 seconds on a typical laptop; first run after warm-up also within this budget. Per-call timeouts: OpenRouter 15s; PDF parse 20s; total budget 120s.
3. NFR3 (Reliability): Apply one retry with jittered backoff; handle API rate-limit responses with friendly guidance; use explicit exit codes (0 success, 2 invalid input, 3 parse error, 4 NER error, 5 LLM error, 6 timeout). README includes a table mapping exit codes → likely causes → remediation steps.
4. NFR4 (Usability): Provide clear CLI help (-h/--help) with examples and descriptive error messages to guide users.
5. NFR5 (Portability): The solution should run on a standard Python environment without GPU requirements; avoid platform-specific code paths. Primary target: Windows 11 (PowerShell) with Python 3.10+.
6. NFR6 (Maintainability): Structure code into small, testable functions with docstrings; pin dependencies and provide a requirements.txt for reproducibility.
7. NFR7 (Testability): Include basic unit tests for PDF text extraction and prompt construction; design components so external services can be mocked.
8. NFR8 (Observability): Provide INFO-level logs for key stages (parse, NER, LLM call, report generation) with a quiet mode to suppress non-errors.
9. NFR9 (Determinism for Demo): Fix temperature/seed where applicable and pin model versions; defaults are deterministic and overridable via CLI flags.
10. NFR10 (Privacy Logging): Redact PII from logs; support a strict "quiet" mode that logs only progress ticks and summarized errors—never full text content.
11. NFR11 (Graceful Degradation): When a dependency is unavailable, degrade with explicit messaging and continue when safe; otherwise fail fast with a clear remediation hint.
12. NFR12 (PDF Text Detection): Detect non-text or encrypted PDFs and provide an actionable error; OCR is out of MVP scope.
13. NFR13 (Dependencies & Cache Budget): Use CPU-only models and prebuilt wheels; first-run download + cache budget under ~200MB; document approximate sizes and cache location.
14. NFR14 (No Native Build Steps): Installation must not require native build toolchains on Windows; if install fails, provide a mock NER fallback or fail fast with remediation steps.
15. NFR15 (Windows Quoting/Encoding): Enforce Windows-friendly quoting in examples; open files with utf-8-sig first then cp1252 fallback; normalize newlines for terminal display.
16. NFR16 (Terminal Rendering): ASCII-only output; width-aware wrapping at ~100 columns; provide `--wide` flag to disable wrapping.
17. NFR17 (Proxy Support): Honor HTTPS_PROXY/HTTP_PROXY/NO_PROXY; document required egress endpoints for model/API access.
18. NFR18 (Test Coverage): Maintain ≥70% line coverage overall and ≥80% in core modules (parse, NER, scoring) measured by the test suite.
19. NFR19 (Data Handling): Process resume/JD content in memory only; do not write inputs or derived text to disk; only model cache is persisted.
20. NFR20 (Egress Documentation): README must document OpenRouter base URL and model CDN endpoints used; warm-up prints which endpoints were contacted.
