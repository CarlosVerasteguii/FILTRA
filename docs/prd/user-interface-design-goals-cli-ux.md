# User Interface Design Goals (CLI UX)

### Overall UX Vision
- Prioritize a clear, readable terminal report suitable for copy/paste into notes.
- Favor deterministic, repeatable output ordering and labeling to ease comparison.
- Keep cognitive load low: minimal flags by default, sensible defaults, examples in `--help`.

### Key Interaction Paradigms
- Single-run, linear workflow: parse → NER → LLM → render.
- Explicit progress messages at INFO level; `--quiet` suppresses non-errors.
- Errors are actionable and mapped to explicit exit codes.

### Core Screens and Views (Terminal Sections)
- Header (run metadata: timestamp, models used)
- Inputs summary (paths, sizes)
- Entities (normalized list: skills, companies)
- Compatibility (score + weighted sub-scores)
- Strengths and Gaps (bulleted)
- Next Steps (brief, optional)

### Accessibility
- Use high-contrast ASCII formatting only; avoid color reliance.
- Respect terminal width; wrap lines to ~100 chars for readability.

### Branding
- Keep neutral CLI tone; include project name “FILTRA” in header.

### Target Device and Platforms
- Web Responsive: N/A (CLI-first)
- Platforms: Windows 11 terminal (PowerShell). macOS/Linux may work but are out of MVP scope.

### Windows 11 Considerations
- File paths and encodings must handle Windows paths and UTF-8 content reliably.
- Provide PowerShell-friendly examples in `--help`.
- Dependencies should install via `pip` on Windows 11 without native build toolchains (prefer prebuilt wheels).
