# Database Schema

FILTRA operates entirely in-memory; no persistent database is required. Runtime artifacts (EvaluationRun, RubricScorecard, ExtractedEntityCollection) only persist in optional golden sample files. Configuration assets such as `config/rubric.yaml` and alias maps are version-controlled and validated via Pydantic models to maintain determinism.

