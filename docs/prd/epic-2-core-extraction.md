# Epic 2: Core Extraction

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

### Story 2.4a Canonical Entity Data Model
As a developer,
I want the extraction pipeline to emit canonical entities with document context,
so that reporting and downstream analysis can reuse counts, sources, and snippets without re-reading source files.

#### Acceptance Criteria
1: Introduce `EntityOccurrence` and `CanonicalEntity` dataclasses and evolve `ExtractedEntityCollection` to expose occurrence lists, canonical aggregates, and a backwards-compatible `entities` alias.
2: filtra/ner/pipeline.py populates each occurrence with span, document role/display, raw text, placeholder canonical text, confidence, context snippet, and language before normalization.
3: filtra/ner/normalization.py groups occurrences deterministically (category + folded canonical text), updates canonical labels, computes ordered contexts/sources, and records collection-level totals in the normalization log.
4: filtra/orchestration/runner.py merges per-document occurrences, preserves ingestion order, and invokes normalization once to produce the enriched collection.
5: Tests cover context snippet helpers, alias compatibility via the `entities` alias, document ordering, and multi-document aggregation edge cases.

### Story 2.4b CLI Reporting Modes
As a CLI user,
I want quiet and wide modes that align with the reporting specification,
so that I can control verbosity and layout without losing the final entities summary.

#### Acceptance Criteria
1: Add a `--wide` flag surfaced in CLI help and warm-up output that toggles additional columns in the report renderer.
2: Quiet mode suppresses progress logs but still prints the final entities section unless an error occurs.
3: CLI help and documentation describe quiet and wide behavior with PowerShell-friendly examples.
4: Automated tests validate quiet output, wide column rendering, and help text updates.

### Story 2.4 Entities Report Section
As a user,
I want a clear entities section in the terminal output,
so that I can quickly scan skills and companies.

#### Acceptance Criteria
1: Render Skills and Companies tables using canonical entity aggregates, with default layout remaining ASCII-only and ~100 columns wide.
2: When the CLI is invoked with `--wide`, include the sources column and adjust wrapping to fit the expanded table; empty states display graceful placeholders.
3: Quiet mode prints only the final entities section and essential status lines while suppressing intermediate progress logs.
4: Reporting functions without scoring or LLM output and reuses evaluation labels/localization.
