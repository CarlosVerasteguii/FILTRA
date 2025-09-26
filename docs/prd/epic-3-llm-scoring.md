# Epic 3: LLM Scoring

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
