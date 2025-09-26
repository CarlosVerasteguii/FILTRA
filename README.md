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

# Display help for the run command and its parameters
python -m filtra run --help

# Execute a comparison run
python -m filtra run --resume "./samples/inputs/resume_sample.pdf" --jd "./samples/inputs/jd_sample.txt"

# Run quietly, emitting only warnings and errors
python -m filtra --quiet run --resume "./samples/inputs/resume_sample.pdf" --jd "./samples/inputs/jd_sample.txt"

# Invoke warm-up diagnostics placeholder (future stories will wire real checks)
python -m filtra warm-up
```

`--quiet` drops the global logging threshold to WARN while keeping structured Rich logging handlers. The scaffold logs placeholder information without leaking resume or JD contents.

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
5. Optionally pre-download large model weights once virtualenv is ready (future warm-up command will automate this).

## Scaffold Overview & Future Workflow Fit
- `filtra/cli.py` hosts the Typer application with `run` and `warm-up` commands, structured exit codes, and Rich logging that respects `--quiet`.
- `filtra/__main__.py` enables `python -m filtra`, matching the architecture source tree contract.
- `tests/test_cli.py` exercises help text, argument validation, and quiet logging semantics following the unit test standards.
- `requirements.in` tracks top-level dependencies from the architecture tech stack. `requirements.txt` pins those versions for deterministic installs on Windows 11.
- Tooling configs (`pyproject.toml`, `ruff.toml`) align with the coding standards (Black line length 100, Ruff linting/import sorting, pytest defaults).

This layout mirrors the monolithic workflow described in the architecture: the CLI command layer hands off to an execution orchestrator (to be implemented in later stories), while the warm-up command will connect to diagnostics that prime transformers models and OpenRouter connectivity.

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

