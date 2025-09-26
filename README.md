# Filtra CLI Scaffold

Filtra is a Windows-first Typer CLI that compares a resume against a job description and produces rich terminal reports. This repository snapshot provides the baseline scaffold, logging policy, and dependency lock that future stories build on.

## Getting Started on Windows 11
1. Ensure [Python 3.10.11](https://www.python.org/downloads/release/python-31011/) is installed and available as `python` in PowerShell.
2. Clone or unzip the repository, then open Windows PowerShell in the project root.
3. Create and activate a virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
4. Upgrade pip (helps with transformer wheel downloads on Windows):
   ```powershell
   python -m pip install --upgrade pip
   ```
5. Install the pinned dependencies (no C/C++ build tools required):
   ```powershell
   pip install -r requirements.txt
   ```
6. (Optional) Install pip-tools if you need to regenerate the lockfile later:
   ```powershell
   python -m pip install pip-tools==7.4.1
   ```

> Note: If script execution is blocked, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` before activating the virtual environment.

## CLI Usage Examples
All commands are tested from PowerShell with quoted paths to survive spaces and localized directories.

```powershell
# Show global help and commands
python -m filtra --help

# Run offline environment diagnostics
python -m filtra --health

# Display help for the run command and its parameters
python -m filtra run --help

# Execute a comparison run
python -m filtra run --resume "./samples/inputs/resume_sample.pdf" --jd "./samples/inputs/jd_sample.txt"

# Run quietly, emitting only warnings and errors
python -m filtra --quiet run --resume "./samples/inputs/resume_sample.pdf" --jd "./samples/inputs/jd_sample.txt"

# Prime model cache and verify OpenRouter connectivity
python -m filtra warm-up
```

`--quiet` drops the global logging threshold to WARN while keeping structured Rich logging handlers. The scaffold logs placeholder information without leaking resume or JD contents.

### Health Diagnostics
Use `python -m filtra --health` before demos to confirm the runtime, secrets, proxy variables, and Hugging Face cache are in good shape. The command never performs network calls; it only inspects local configuration and prints PASS/FAIL rows with remediation guidance for anything missing.

### Warm-up Diagnostics
`python -m filtra warm-up` now performs the full diagnostics workflow:

- Pre-downloads the multilingual NER model into the Hugging Face cache.
- Issues a lightweight OpenRouter request (5s timeout, retry once) to confirm the API key, proxy settings, and network access are valid.
- Summarises proxy variables, cache location, cache size, and execution time while respecting `--quiet` and without exposing secrets.

Example output:

````powershell
python -m filtra warm-up
Filtra warm-up diagnostics
Python runtime     : 3.10.11
Model cache folder : C:\Users\carlo\AppData\Local\filtra\models
Cache on disk      : 112.4 MiB
Duration           : 18.4s

Proxy environment:
  HTTPS_PROXY : set (value hidden)
  HTTP_PROXY  : (not set)
  NO_PROXY    : set (value hidden)

[PASS] Python runtime - Detected Python 3.10.11.
[PASS] OpenRouter API key - OPENROUTER_API_KEY detected (48 characters).
[PASS] Proxy configuration - Proxy variables detected: HTTPS_PROXY, NO_PROXY.
[PASS] NER model cache - Prefetched 'Davlan/bert-base-multilingual-cased-ner-hrl' into C:\Users\carlo\AppData\Local\filtra\models (~112.4 MiB on disk).
[PASS] OpenRouter connectivity - OpenRouter endpoint https://openrouter.ai/api/v1/chat/completions responded in 0.78 seconds (request req-xyz123).
[PASS] Warm-up duration - Completed in 18.40 seconds (budget 120s).

Overall status: PASS
````

Use `scripts\warmup_demo.ps1` as a convenience wrapper before customer demos; it checks prerequisites, reports proxy status without revealing values, and forwards all arguments to `python -m filtra warm-up`.

### Exit Codes & Remediation
| Code | Scenario                                   | Remediation Hint |
| ---- | ------------------------------------------ | ---------------- |
| 0    | Successful run                             | No action required. |
| 2    | Invalid or missing CLI input               | Verify resume/JD file paths and rerun the command. |
| 3    | Document parsing failed                    | Check file readability; convert PDFs to text if necessary. |
| 4    | NER model could not be initialised         | Clear the Hugging Face cache and run `filtra warm-up` to repopulate weights. |
| 5    | LLM gateway error or missing API key       | Set `OPENROUTER_API_KEY` and confirm proxy settings before retrying. |
| 6    | Pipeline exceeded the configured timeout   | Retry on a stable network or increase the timeout once configuration is exposed. |

## Windows 11 Verification Checklist
The following checklist confirms Filtra runs end-to-end on a clean Windows 11 PowerShell session. Quote every path to survive directories with spaces.

1. Activate the project virtual environment and install dependencies as described above.
2. Run `python -m filtra --health` to confirm prerequisites resolve without network calls.
3. Execute `scripts\warmup_demo.ps1` (optionally pass `-WarmupArgs @('--quiet')`) and confirm the Hugging Face cache lives under `$env:LOCALAPPDATA\filtra\models`.
4. Copy the provided samples into a folder with spaces, then run the CLI against those paths:
   ```powershell
   $target = Join-Path $env:USERPROFILE 'Documents\Filtra Samples'
   New-Item -ItemType Directory -Path $target -Force | Out-Null
   Copy-Item .\samples\inputs\resume_sample.pdf "$target\resume sample.pdf"
   Copy-Item .\samples\inputs\jd_sample.txt "$target\jd sample.txt"
   python -m filtra run --resume "$target\resume sample.pdf" --jd "$target\jd sample.txt"
   ```
   The output should report each file name in quotes, list the detected encodings, and only use `
` newlines.
5. Open the copied job description in Notepad, save it with **ANSI** encoding, and rerun the command to confirm Windows-1252 fallback still succeeds.
6. Record the run results, durations, and any deviations in `docs/qa/windows-11-runbook.md` for traceability.

## Repository Bootstrap Checklist
Use this flow when rehydrating the scaffold in a new folder:

1. Initialise the repository:
   ```powershell
   git init
   git branch -m main
   git add .
   git commit -m "chore: bootstrap filtra cli"
   ```
2. Create the virtual environment and install dependencies as shown above.
3. Run `python -m filtra --help` to verify the CLI loads.
4. Execute the unit tests:
   ```powershell
   pytest
   ```
5. Run `python -m filtra warm-up` (or `scripts\warmup_demo.ps1`) once to prime the model cache and validate OpenRouter connectivity ahead of the first demo.

## Scaffold Overview & Future Workflow Fit
- `filtra/cli.py` hosts the Typer application with `run` and `warm-up` commands, structured exit codes, and Rich logging that respects `--quiet`.
- `filtra/__main__.py` enables `python -m filtra`, matching the architecture source tree contract.
- `tests/test_cli.py` exercises help text, argument validation, warm-up output, and quiet logging semantics following the unit test standards.
- `requirements.in` tracks top-level dependencies from the architecture tech stack. `requirements.txt` pins those versions for deterministic installs on Windows 11.
- Tooling configs (`pyproject.toml`, `ruff.toml`) align with the coding standards (Black line length 100, Ruff linting/import sorting, pytest defaults).

This layout mirrors the monolithic workflow described in the architecture: the CLI command layer now hands off to the diagnostics service to prepare transformers models and verify OpenRouter, while future stories will wire the remaining orchestration pipeline.

## Updating Dependencies Safely
When you need to refresh versions, run the following from an activated virtual environment after editing `requirements.in`:

```powershell
python -m piptools compile requirements.in
pip install -r requirements.txt
```

Document any installation hiccups (especially transformer wheel downloads) in `docs/infrastructure-and-deployment.md` so future contributors stay unblocked.

## Troubleshooting
- **SSL or proxy issues**: ensure `HTTPS_PROXY`/`HTTP_PROXY` are set before invoking `pip install` or the CLI. The application honours these variables through `httpx`.
- **Large dependency downloads**: Transformers wheels can be sizeable; rerun `pip install` with `--no-cache-dir` if OneDrive quotas cause issues.
- **Virtual environment path issues**: If the activation script is blocked, confirm the execution policy note above and re-run `.\.venv\Scripts\Activate.ps1` from the project root.
- **Unclear failures**: Run `python -m filtra warm-up` to populate caches and surface remediation hints for API or proxy configuration, or `python -m filtra --health` for offline diagnostics.

