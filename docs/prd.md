# FILTRA Product Requirements Document (PRD)

## Goals and Background Context

### Goals
- Build a functional Python prototype that screens resumes against a job description using AI.
- Demonstrate integration with an OpenRouter-hosted LLM for qualitative scoring and analysis.
- Use a local HuggingFace NER model to extract structured entities (e.g., skills, companies) from resumes.
- Generate a concise, recruiter-friendly report combining LLM insights and extracted entities.
- Enable single-run CLI usage: PDF in, JD text in, formatted output in terminal.
- Showcase capabilities relevant to RRHH Ingenia interview requirements within 24 hours.

### Background Context
Recruitment teams invest significant time manually screening resumes, a process that is slow, error-prone, and susceptible to bias, delaying identification of top candidates. FILTRA addresses this by providing a Python command-line tool that integrates two AI modalities: a Large Language Model (via OpenRouter) for qualitative analysis and compatibility scoring, and a locally run HuggingFace NER model for structured entity extraction. The outcome is a practical prototype designed to support the RRHH Ingenia interview by demonstrating AI API integration, local model usage, and clear, useful reports for faster, data-driven decisions.

### Change Log
| Date       | Version | Description                                                           | Author     |
|------------|---------|------------------------------------------------------------------------|------------|
| 2025-09-26 | 0.1     | Initial PRD draft: Goals, Background, and Change Log seeded from Brief | John (PM)  |
| 2025-09-26 | 0.2     | Risk-driven updates: FR13 clarified; FR16 added; NFR3 strengthened; NFR12–NFR17 added; Windows 11 specifics | John (PM)  |
| 2025-09-26 | 0.3     | Critique pass: refined NFR2/3; added FR17–FR18; added NFR18–NFR20; rubric path noted | John (PM)  |
| 2025-09-26 | 0.4     | Sequencing audit: added independence ACs to Epics 2–4 to avoid forward deps | John (PM)  |

## Requirements

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

## User Interface Design Goals (CLI UX)

### Overall UX Vision
- Prioritize a clear, readable terminal report suitable for copy/paste into notes.
- Favor deterministic, repeatable output ordering and labeling to ease comparison.
- Keep cognitive load low: minimal flags by default, sensible defaults, examples in `--help`.

### Key Interaction Paradigms
- Single-run, linear workflow: parse → NER → LLM → render.
- Explicit progress messages at INFO level; `--quiet` suppresses non-errors.
- Errors are actionable and mapped to explicit exit codes.

### Core Screens and Views (Terminal Sections)
- Header (run metadata: timestamp, models used)
- Inputs summary (paths, sizes)
- Entities (normalized list: skills, companies)
- Compatibility (score + weighted sub-scores)
- Strengths and Gaps (bulleted)
- Next Steps (brief, optional)

### Accessibility
- Use high-contrast ASCII formatting only; avoid color reliance.
- Respect terminal width; wrap lines to ~100 chars for readability.

### Branding
- Keep neutral CLI tone; include project name “FILTRA” in header.

### Target Device and Platforms
- Web Responsive: N/A (CLI-first)
- Platforms: Windows 11 terminal (PowerShell). macOS/Linux may work but are out of MVP scope.

### Windows 11 Considerations
- File paths and encodings must handle Windows paths and UTF-8 content reliably.
- Provide PowerShell-friendly examples in `--help`.
- Dependencies should install via `pip` on Windows 11 without native build toolchains (prefer prebuilt wheels).

## Technical Assumptions

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

## Epic List

- Epic 1: Foundation & Warm-up — Set up CLI project, dependency pins, Windows 11 support, warm-up command, and basic health checks.
- Epic 2: Core Extraction — Implement PDF text extraction, multilingual NER with normalization/dedup, and entity reporting.
- Epic 3: LLM Scoring — Integrate OpenRouter, implement deterministic scoring rubric with sub-scores, and compose terminal report.
- Epic 4: Reliability & UX — Add retries/timeouts, explicit exit codes, ASCII width-aware rendering, proxy support, and quiet mode.
- Epic 5: Validation & Samples — Add golden samples, unit/integration tests, and documentation for Windows 11 usage.

## Epic 1: Foundation & Warm-up

Goal: Establish a Windows 11–ready CLI foundation with pinned dependencies, deterministic defaults, health checks, and a warm-up command for first-run reliability.

### Story 1.1 CLI Project Scaffold
As a developer,
I want a pinned, Windows 11–friendly CLI scaffold,
so that I can run and iterate reliably without native build tools.

#### Acceptance Criteria
1: A `requirements.txt` with pinned versions exists; `python -m venv .venv && pip install -r requirements.txt` succeeds on Windows 11 without native compilers.
2: A CLI entry point `filtra.py` (or package `filtra/__main__.py`) accepts `--resume` and `--jd` and prints usage with `-h/--help`.
3: Logging set to INFO by default, `--quiet` reduces to WARN+; no secrets printed.
4: README includes PowerShell-friendly examples with quoted paths.
5: Document initial repository bootstrap instructions (git init, first commit, README scaffolding) so newcomers can reproduce setup.

### Story 1.2 Health Checks and Exit Codes
As a user,
I want clear health checks and exit codes,
so that failures are actionable during demos.

#### Acceptance Criteria
1: Implement explicit exit codes (0 success, 2 invalid input, 3 parse error, 4 NER error, 5 LLM error, 6 timeout) wired through main.
2: Add a `--health` flag that validates Python version, env var presence, and prints model/API readiness summary without network calls.
3: Errors include remediation text (e.g., missing `OPENROUTER_API_KEY`).

### Story 1.3 Warm-up Command
As a user,
I want a warm-up command,
so that first demo run does not incur downloads or cold failures.

#### Acceptance Criteria
1: `filtra warm-up` pre-downloads the selected NER model to cache and verifies OpenRouter connectivity with a lightweight request.
2: Prints cache location and approximate on-disk size; respects proxy env vars.
3: Completes under 120 seconds on typical connection or exits with clear guidance.

### Story 1.4 Windows 11 Readiness
As a user on Windows 11,
I want encoding and path handling to just work,
so that inputs render correctly and examples run as-is.

#### Acceptance Criteria
1: File I/O uses utf-8-sig first, cp1252 fallback; normalized newlines in output.
2: All README examples quote paths; CLI correctly handles spaces in file paths.
3: Installation and run steps verified on Windows 11 PowerShell.

## Epic 2: Core Extraction

Goal: Implement robust PDF text extraction and multilingual NER with normalization/dedup to produce high-quality, structured entities for later scoring.

### Story 2.1 PDF Text Extraction
As a developer,
I want reliable PDF-to-text extraction,
so that resumes produce clean text for NER and LLM.

#### Acceptance Criteria
1: Implement PDF parsing with detection of non-text/encrypted PDFs; on detection, fail fast with actionable error (OCR out-of-scope per NFR12).
2: Normalize whitespace and newlines; ensure utf-8 output (utf-8-sig read, cp1252 fallback per NFR15).
3: Unit tests cover typical text PDFs and non-text PDFs; exit code 3 on parse errors.

### Story 2.2 Multilingual NER (CPU-only)
As a developer,
I want a CPU-only multilingual NER pipeline,
so that Spanish/English resumes are supported on Windows 11.

#### Acceptance Criteria
1: Default model supports ES/EN (e.g., `Davlan/bert-base-multilingual-cased-ner-hrl`); swappable via `--ner-model`.
2: First run downloads to cache (<~200MB total); cache path printed; respects proxy env vars.
3: Integration test confirms entities extracted from a sample Spanish and English resume.

### Story 2.3 Entity Normalization & Dedup
As a user,
I want clean, normalized entities,
so that the report avoids duplicates and alias noise.

#### Acceptance Criteria
1: Apply casefolding, trimming, and alias map; language-agnostic normalization; output sorted lists.
2: Unit tests for alias normalization (e.g., "PyTorch" == "pytorch").
3: CLI flag or config to extend alias map without code changes.

### Story 2.4 Entities Report Section
As a user,
I want a clear entities section in the terminal output,
so that I can quickly scan skills and companies.

#### Acceptance Criteria
1: ASCII-only, width-aware rendering (~100 cols) with `--wide` override.
2: Sections: Skills, Companies (others optional); empty states handled gracefully.
3: Works with `--quiet` (only final section prints unless error).
4: Independent of scoring; runs without any LLM configuration or outputs from Epic 3.

## Epic 3: LLM Scoring

Goal: Integrate OpenRouter LLM, implement deterministic rubric-based scoring with sub-scores, and compose the terminal report sections.

### Story 3.1 OpenRouter Integration
As a developer,
I want a robust OpenRouter client with timeouts and retries,
so that scoring requests are reliable and safe to demo.

#### Acceptance Criteria
1: Client uses 15s per-call timeout and one retry with jittered backoff; rate-limit errors produce friendly wait guidance.
2: Model selection via `--llm-model`; unknown model errors include remediation text.
3: Unit tests mock HTTP and verify timeout/exit code 5 behavior.
4: Independent of prompt builder (Story 3.3); tests use a stub prompt string to exercise the client.

### Story 3.2 Scoring Rubric with Sub-scores
As a user,
I want a clear 0–100 score with weighted sub-scores,
so that candidate comparison is transparent.

#### Acceptance Criteria
1: Rubric weights are versioned in repo; default temperature=0 for determinism.
2: Sub-scores (e.g., skills match, experience relevance) + overall score computed and included in output.
3: Unit tests cover rubric math and determinism settings.
4: Independent of OpenRouter integration (Story 3.1); scoring functions operate on local inputs without network calls.

### Story 3.3 Prompt Construction and Safety
As a developer,
I want a safe, consistent prompt builder,
so that inputs are structured and privacy rules are respected.

#### Acceptance Criteria
1: Prompt builder assembles inputs (resume text, entities, JD) with redaction policy (no secrets).
2: Supports multilingual contexts; test with Spanish/English samples.
3: Unit test verifies prompt shape and redaction behavior.
4: No network calls; builder is purely local and independent of the OpenRouter client (Story 3.1).

### Story 3.4 Report Composition
As a user,
I want a complete terminal report section for scoring,
so that I can quickly understand strengths and gaps.

#### Acceptance Criteria
1: Output includes: Score (0–100) + sub-scores, Strengths (bulleted), Gaps (bulleted).
2: ASCII-only, width-aware rendering; integrates with entities section from Epic 2.
3: Works with `--quiet` (prints final report only) and `--wide` (disables wrapping).
4: Operates with stubbed LLM output when needed; does not require retry/timeout features from Epic 4.

## Epic 4: Reliability & UX

Goal: Improve resilience (timeouts, retries, proxies), terminal UX (width-aware, quiet mode), and privacy logging to meet NFR2–NFR17.

### Story 4.1 Timeouts, Retries, and Exit Codes Hardening
As a developer,
I want hardened error handling and exit codes,
so that failures are predictable and user-guided.

#### Acceptance Criteria
1: Centralized HTTP/timeouts config (15s per call, single retry with jitter); parse timeout 20s; total budget 120s enforced.
2: Exit codes audited end-to-end; integration tests validate each code path.
3: Rate-limit responses emit friendly guidance (retry-after) without stack traces.

### Story 4.2 Proxy Support
As an enterprise user,
I want proxy environment variables to be honored,
so that the tool works behind corporate networks.

#### Acceptance Criteria
1: HTTPS_PROXY/HTTP_PROXY/NO_PROXY are honored for both model downloads and OpenRouter.
2: Documentation lists required egress endpoints; warm-up prints which proxy vars are in effect.
3: Integration test sets fake proxy env and verifies requests route accordingly (mocked).

### Story 4.3 Terminal UX: Width & Quiet Mode
As a user,
I want readable output in my terminal,
so that reports are easy to consume and compare.

#### Acceptance Criteria
1: Width-aware wrapping at ~100 cols; `--wide` disables wrapping.
2: `--quiet` prints only the final report or errors; INFO progress hidden.
3: Snapshot tests verify wrapped vs wide output with entities + scoring.
4: Formatting-only changes; does not alter data from earlier epics (entities/scoring).

### Story 4.4 Privacy Logging & Redaction
As a security-conscious user,
I want privacy-preserving logs,
so that sensitive content never leaks.

#### Acceptance Criteria
1: No logging of resume or JD content; redact potential PII in error contexts.
2: API keys never printed; errors redact key substrings; warning if key missing.
3: Unit tests confirm redaction and absence of sensitive data in logs.

## Epic 5: Validation & Samples

Goal: Provide golden samples, tests, and documentation to validate behavior, enable quick demos, and ensure reproducibility on Windows 11.

### Story 5.1 Golden Samples
As a developer,
I want curated golden samples (resumes + JD),
so that I can validate output shape and demo quickly.

#### Acceptance Criteria
1: Include 2–3 sample resumes (EN + ES) and one JD; ensure license-safe synthetic data.
2: Provide expected report schema and example outputs; diff script compares shape (not exact text).
3: Document how to run samples in README with PowerShell examples.

### Story 5.2 Unit & Integration Tests
As a developer,
I want unit and light integration tests,
so that core logic is verified and regressions are caught.

#### Acceptance Criteria
1: Unit tests for PDF parse, alias normalization, prompt construction, rubric math, and log redaction.
2: Integration test runs end-to-end with mocked LLM, real NER; validates entities and report sections.
3: Tests runnable on Windows 11 without extra toolchains; provide `pytest` config.

### Story 5.3 Reproducibility & Tooling
As a user,
I want reproducible runs,
so that results are consistent across machines.

#### Acceptance Criteria
1: Document deterministic defaults (temperature=0, fixed weights); provide a `--seed` option if applicable.
2: Add `requirements.txt` pins and optional `requirements-lock.txt` with resolved hashes if feasible.
3: Add a script or Make-like PowerShell tasks (`scripts\run.ps1`) for common commands (warm-up, run sample, tests).

### Story 5.4 Documentation & Quickstart
As a user on Windows 11,
I want a Quickstart guide,
so that I can set up and run a demo in minutes.

#### Acceptance Criteria
1: README Quickstart: create venv, install, set OPENROUTER_API_KEY, warm-up, run on sample.
2: Troubleshooting section for proxies, timeouts, and model downloads; list egress endpoints.
3: Clear statement of out-of-scope (OCR) and limitations; link to PRD sections.




