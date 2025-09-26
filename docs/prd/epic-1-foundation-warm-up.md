# Epic 1: Foundation & Warm-up

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
