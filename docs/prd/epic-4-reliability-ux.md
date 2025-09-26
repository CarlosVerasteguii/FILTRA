# Epic 4: Reliability & UX

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
