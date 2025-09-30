# Tech Stack

### Cloud Infrastructure
- **Provider:** Local execution (developer machine) plus OpenRouter API
- **Key Services:** Local filesystem, HuggingFace cache directory, OpenRouter HTTPS endpoint
- **Deployment Regions:** N/A (client-side tool)

### Technology Stack Table
| Category                | Technology                               | Version   | Purpose                                        | Rationale                                                                 |
|-------------------------|-------------------------------------------|-----------|------------------------------------------------|---------------------------------------------------------------------------|
| Language                | Python                                    | 3.10.11   | Primary runtime                                | Matches PRD Windows requirement; default locale tuned for Spanish users  |
| Package Management      | pip-tools + venv                          | 7.4.1     | Pin dependencies / generate requirements files | Automates lock files while honouring requirements.txt mandate            |
| CLI Framework           | typer                                     | 0.12.3    | Build commands, subcommands, PowerShell help   | Modern API, auto completion, clean help output                           |
| Argument Parsing        | typer/click (transitive)                  | 8.1.7     | Underlying CLI parsing                         | Provided via typer dependency                                            |
| PDF Extraction          | pypdf                                     | 5.1.0     | Parse resume PDFs                              | Pure Python, Windows-friendly                                            |
| Language Detection      | langdetect                                | 1.0.9     | Auto-detect resume/JD language                 | Lightweight, works offline; bias configurable to prefer Spanish          |
| NER Pipeline            | transformers + Davlan/bert-base-multilingual-cased-ner-hrl | 4.44.0 | Multilingual entity extraction                 | CPU-only support, covers ES/EN per PRD                                   |
| Alt NER (EN fallback)   | transformers + dslim/bert-base-NER        | 4.44.0    | EN-only fallback                               | Lightweight alternative if multilingual weights unavailable              |
| Tokenizer Backend       | tokenizers                                | 0.19.1    | Support HF pipelines                           | Required for transformers pipelines                                      |
| HTTP Client             | httpx                                     | 0.27.0    | OpenRouter communication                       | Built-in retries/timeouts; respects proxy env vars                       |
| Proxy Configuration     | Built-in environment variables            | n/a       | Honour HTTPS_PROXY/HTTP_PROXY/NO_PROXY         | Satisfies NFR17 corporate network constraints                            |
| Retries/Backoff         | tenacity                                  | 9.0.0     | Resilient API calls                            | Simplifies retry policies demanded by reliability epic                   |
| Config Management       | PyYAML                                    | 6.0.1     | Load rubric/config files                       | Simple YAML parsing                                                      |
| Config Validation       | pydantic                                  | 2.8.2     | Validate rubric & CLI config                   | Strict types, good error messages                                        |
| Report Rendering        | rich                                      | 13.7.1    | Terminal-friendly report, width handling       | Handles `--wide`, tables, quiet toggles                                  |
| Logging                 | logging + rich.logging                    | builtin   | Structured logs respecting `--quiet`           | Meets PRD logging requirement                                            |
| Testing Framework       | pytest                                    | 8.3.2     | Unit & integration tests                       | Widely used, plugin ecosystem                                            |
| Test Utilities          | pytest-mock                               | 3.14.0    | Mocking external services                      | Streamlines adapter tests                                                |
| Coverage                | coverage                                  | 7.5.4     | Coverage reporting                             | Ensures quality metrics                                                  |
| Linting                 | ruff                                      | 0.6.5     | Lint + import sorting                          | Fast, single tool for lint + style                                       |
| Formatting              | black                                     | 24.8.0    | Code formatting                                | Widely adopted, deterministic output                                    |
| Type Checking           | mypy                                      | 1.10.0    | Static type analysis                           | Improves reliability of adapters                                         |
| Packaging Script        | python -m piptools compile                | n/a       | Generate pinned requirements                   | Documented for Windows compatibility                                     |
| Golden Sample Storage   | samples/ directory                        | n/a       | Store FR12 sample inputs                       | Simplifies test fixtures                                                 |
| Model Cache Location    | %LOCALAPPDATA%/filtra/models              | n/a       | Persist HF weights between runs                | Windows-appropriate default                                              |\n## Data Models

#### ResumeDocument
**Purpose:** Represents the candidate resume input, capturing both the original PDF metadata and the extracted plain text used downstream.

**Key Attributes:**
- source_path: Path - Absolute/relative filesystem path to the PDF provided via `--resume`.
- extracted_text: str - Normalized plain-text body produced by the PDF parser, ready for NER and scoring.

**Relationships:**
- Supplies text to ExtractedEntityCollection for multilingual NER processing.
- Linked to EvaluationRun as the primary user-provided artifact.
#### JobDescription
**Purpose:** Stores the target role description text and metadata that guide compatibility scoring and prompt construction.

**Key Attributes:**
- source_path: Path - Filesystem location of the text file provided via `--jd`.
- normalized_text: str - Cleaned job description content used for NER comparison and LLM prompting.

**Relationships:**
- Coupled with EvaluationRun to provide context for scoring and reporting.
- Cross-referenced by RubricConfig to weight criteria based on job expectations.
#### LanguageProfile
**Purpose:** Captures detected and user-specified language preferences to drive prompt localization and reporting outputs.

**Key Attributes:**
- default_locale: str - Project default (`es-MX`) applied when no overrides are provided.
- resume_locale: Optional[str] - Auto-detected language code from resume content.
- jd_locale: Optional[str] - Auto-detected language code from job description text.
- effective_locale: str - Final locale used for prompts and rendered report sections.

**Relationships:**
- Managed within EvaluationRun; referenced by PromptTemplateAssembler and ReportRenderer.
- Ingests signals from Language Detection & Localization component and exposes them to downstream modules.
### Canonical Entity Data Model
#### EntityOccurrence
**Purpose:** Represents a single detected entity span before and after normalization, preserving document context for reporting and audit trails.

**Key Attributes:**
- raw_text / canonical_text: Original span text and the resolved canonical form.
- category: EntityCategory enumeration (skills, companies, etc.).
- confidence: Float score from the NER pipeline.
- span: Tuple[int, int] indicating character offsets within the source document.
- document_role / document_display: Logical role (resume, job_description) and user-facing label.
- context_snippet: Optional excerpt surrounding the occurrence for report snippets.
- source_language: Language code inferred for the occurrence.

**Relationships:**
- Produced by filtra/ner/pipeline.py with document metadata supplied by the orchestrator.
- Grouped into CanonicalEntity aggregates during normalization.
#### CanonicalEntity
**Purpose:** Captures the canonical representation of related occurrences along with ordered contexts and document sources.

**Key Attributes:**
- text: Final canonical label after normalization and alias resolution.
- category: EntityCategory shared by grouped occurrences.
- top_confidence: Highest confidence value among occurrences.
- occurrence_count: Total occurrences grouped under this canonical entry.
- occurrences: Tuple[EntityOccurrence, ...] preserving ingestion order.
- contexts / sources: Tuples mirroring occurrences for snippet display and source labeling.

**Relationships:**
- Built inside filtra/ner/normalization.py; consumed by reporting and scoring layers.
- Serialized within ExtractedEntityCollection for downstream consumers.
#### ExtractedEntityCollection
**Purpose:** Aggregates canonical entities and their occurrences into a single structure returned by the NER pipeline after normalization.

**Key Attributes:**
- occurrences: Tuple[EntityOccurrence, ...] concatenated across processed documents.
- canonical_entities: Tuple[CanonicalEntity, ...] used by reporting and scoring modules.
- entities: Legacy alias (Tuple[CanonicalEntity, ...]) maintained temporarily for backward compatibility.
- language_profile: Optional LanguageProfile snapshot carried through the pipeline.
- normalization_log: Tuple[str, ...] summarizing normalization, alias application, and document totals for FR13 auditability.

**Relationships:**
- Returned by filtra/ner/pipeline.py and enriched by filtra/orchestration/runner.py when merging per-document results.
- Feeds RubricScorecard, ReportEnvelope, and any analytics that rely on canonical entities.
#### AliasMap
**Purpose:** Maintains curated alias mappings and language-agnostic normalization rules applied to extracted entities.

**Key Attributes:**
- alias_rules: Dict[str, List[str]] - Canonical term to alias list mapping, versioned for audit.
- locale_overrides: Dict[str, Dict[str, str]] - Optional per-language overrides when ES/EN nuances differ.

**Relationships:**
- Referenced by ExtractedEntityCollection during normalization workflows.
- Loaded from configuration files managed by RubricConfig to ensure reproducible scoring.
#### RubricConfig
**Purpose:** Encapsulates the compatibility scoring rubric, weighting criteria and threshold rules used to compute deterministic sub-scores.

**Key Attributes:**
- weights: Dict[str, float] - Weight assignments per scoring dimension (skills match, experience, language fit, etc.).
- thresholds: Dict[str, Any] - Cutoff values or normalization parameters (e.g., minimum skill overlap percentages).

**Relationships:**
- Loaded from `config/rubric.yaml` and versioned for FR11/FR12 traceability.
- Consumed by RubricScorecard during score computation; referenced by PromptTemplateAssembler to align LLM prompts with rubric focus.
#### RubricScorecard
**Purpose:** Stores computed rubric sub-scores, intermediate metrics, and final compatibility score before report rendering.

**Key Attributes:**
- sub_scores: Dict[str, float] - Weighted results per criterion (e.g., skills_match, experience_alignment).
- overall_score: float - Aggregated 0-100 score respecting weight totals.

**Relationships:**
- Receives weights/thresholds from RubricConfig and normalized entities from ExtractedEntityCollection.
- Supplies deterministic metrics to ReportEnvelope and to the LLM prompt for context.
#### EvaluationRun
**Purpose:** Represents a single CLI execution, bundling inputs, configuration choices, processing metadata, and outputs for auditing and golden sample comparisons.

**Key Attributes:**
- run_id: str - UUID or timestamp-based identifier for traceability.
- cli_options: Dict[str, Any] - Flags provided (models, quiet, lang, seed) captured for reproducibility.

**Relationships:**
- Aggregates ResumeDocument, JobDescription, and LanguageProfile artifacts and references the RubricConfig snapshot.
- Produces RubricScorecard and ReportEnvelope; linked to WarmupResult when preflight checks precede execution and exposes effective locale to downstream renderers.
#### ReportEnvelope
**Purpose:** Encapsulates the structured report presented to the recruiter, merging deterministic rubric scores and LLM narrative output.

**Key Attributes:**
- summary_sections: List[ReportSection] - Ordered blocks (overview, strengths, gaps, entity highlights) ready for terminal rendering.
- render_options: Dict[str, Any] - Flags influencing layout (`wide` adds sources/extra width, `quiet` suppresses progress while retaining the final entities section, plus localization).

**Relationships:**
- Receives RubricScorecard data, LLMAnalysis artifacts, and the effective locale from LanguageProfile; passed to ReportRenderer for CLI display.
- Stored alongside EvaluationRun for FR12 golden sample comparisons.
