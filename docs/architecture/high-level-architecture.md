# High Level Architecture

### Technical Summary
FILTRA is a single-process Python CLI monolith that orchestrates PDF parsing, entity extraction, rubric-driven scoring, and OpenRouter LLM analysis within one codebase. A command dispatcher coordinates flows between modules handling resume ingestion, multilingual NER via HuggingFace pipelines, rubric-weighted scoring, and report rendering. The CLI persists no user data, instead streaming artifacts through in-memory structures and one-off temp storage that is cleared after execution. External dependencies are limited to OpenRouter’s HTTP API, local HuggingFace model weights, and optional warming routines. This layout satisfies PRD goals of a quickly demoable Windows-friendly tool that showcases both local NER and remote LLM integration. The experience defaults to Spanish ( `es-MX`) responses for Mexican recruiters while preserving English support through detection and overrides. 

### High Level Overview
- **Architecture style:** Monolithic CLI with modular subsystems for parsing, extraction, scoring, reporting, augmented by optional warm-up subcommand.
- **Repository structure:** Monorepo (single Python project) aligned with PRD mandate for MVP simplicity.
- **Service architecture:** Self-contained CLI executable; externalized capabilities limited to OpenRouter API calls and local HF pipeline invocations without microservices.
- **Primary flow:** User invokes CLI (--resume PDF + --jd text) → input validator normalizes CLI arguments and resolves locale preferences (default s-MX, override via --lang, or automatic detection from resume/JD) → resume text is extracted and preprocessed → language profiler finalizes prompt/report locale → NER module loads multilingual model, extracts entities, runs normalization/dedup → scoring orchestrator loads rubric YAML, merges NER findings and JD to assemble LLM prompt and compute rubric-driven sub-scores → OpenRouter client calls configured model → response synthesizer merges deterministic rubric results with LLM insights → report renderer prints terminal-friendly summary respecting --quiet, --wide, and localization options → process exits with status per success/failure.
- **Key decisions:** Keep everything in-process to minimize Windows packaging overhead; prefer synchronous API calls with timeouts and retries per reliability epic; rely on configuration files (`config/rubric.yaml`, CLI flags) for deterministic scoring; isolate external interactions behind adapters so offline mocks satisfy FR15.

### High Level Project Diagram
```mermaid
graph TD
    User[Recruiter CLI Invocation] -->|CLI args| CLIEntry[CLI Entry & Arg Parser]
    CLIEntry --> Warmup{Subcommand?}
    Warmup -->|Prefetch| ModelCache[HF Model Cache]
    Warmup -->|Ping| OpenRouterAPI
    CLIEntry -->|Main run| Orchestrator
    Orchestrator -->|Extract text| PDFParser[PDF Text Extractor]
    Orchestrator -->|Entities| NERPipeline[HuggingFace NER Pipeline]
    Orchestrator -->|Rubric load| RubricLoader[Rubric Config (YAML)]
    Orchestrator -->|Prompt+score| LLMClient[OpenRouter LLM API]
    LLMClient --> OpenRouterAPI[(OpenRouter)]
    NERPipeline --> ModelCache
    Orchestrator -->|Normalize & merge| ScoreEngine[Scoring & Normalization]
    ScoreEngine --> ReportBuilder[Report Composer]
    ReportBuilder --> CLIOutput[Terminal Renderer]
    CLIOutput --> User
```

### Architectural and Design Patterns
- **Layered Modular Monolith:** CLI entrypoint dispatches to domain-focused modules (ingestion, extraction, scoring, reporting) while sharing a common configuration core. _Rationale:_ Keeps implementation simple for MVP, supports Windows distribution, and avoids premature service boundaries while still promoting testable separations.
- **Adapter/Gateway Pattern for External Services:** OpenRouter interactions and NER model loading are wrapped in dedicated clients exposing interface contracts. _Rationale:_ Enables FR15 graceful degradation (mock responses, offline fallbacks) and simplifies dependency injection for unit tests.
- **Pipes & Filters Processing Pipeline:** Resume data flows through a deterministic pipeline (parse → extract → normalize → score → render) where each stage outputs enriched artifacts to the next. _Rationale:_ Aligns with FR13 normalization requirements, facilitates insertion of retries/metrics, and supports optional warm-up and quiet modes without entangling core logic.
- **Configuration-Driven Strategy Pattern:** Scoring behavior and prompt variants are selected via CLI flags/config files, allowing replacement of NER models or LLM prompts without code changes. _Rationale:_ Satisfies FR14/FR18 customization flags and supports experimentation under tight timelines.