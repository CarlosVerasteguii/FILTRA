# Epic 5: Validation & Samples

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




