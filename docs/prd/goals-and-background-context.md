# Goals and Background Context

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
