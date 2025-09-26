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

### Story 2.4 Entities Report Section
As a user,
I want a clear entities section in the terminal output,
so that I can quickly scan skills and companies.

#### Acceptance Criteria
1: ASCII-only, width-aware rendering (~100 cols) with `--wide` override.
2: Sections: Skills, Companies (others optional); empty states handled gracefully.
3: Works with `--quiet` (only final section prints unless error).
4: Independent of scoring; runs without any LLM configuration or outputs from Epic 3.
