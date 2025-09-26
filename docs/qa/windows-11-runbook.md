# Windows 11 Verification Runbook

This runbook captures the manual validation required to prove Filtra operates smoothly on Windows 11 PowerShell sessions, including encoding fallbacks and path handling.

## Preconditions
- Windows 11 Pro build 22631 or newer.
- PowerShell (pwsh.exe) with `ExecutionPolicy` permitting script execution for the current process.
- Python 3.10.11 available as `python` on `PATH`.
- Local clone of the Filtra repository.

## Verification Steps
1. **Environment bootstrap**
   - `python -m venv .venv`
   - `.\.venv\Scripts\Activate.ps1`
   - `pip install -r requirements.txt`
2. **Offline diagnostics** — run `python -m filtra --health` and record PASS/FAIL rows and any remediation guidance.
3. **Warm-up cache** — execute `scripts\warmup_demo.ps1 -WarmupArgs @('--quiet')`.
   - Confirm the script reports the Hugging Face cache under `$env:LOCALAPPDATA\filtra\models`.
   - Capture total duration and exit code.
4. **Sample path with spaces**
   - Copy sample files into a directory containing spaces:
     ```powershell
     $target = Join-Path $env:USERPROFILE 'Documents\Filtra Samples'
     New-Item -ItemType Directory -Path $target -Force | Out-Null
     Copy-Item .\samples\inputs\resume_sample.pdf "$target\resume sample.pdf"
     Copy-Item .\samples\inputs\jd_sample.txt "$target\jd sample.txt"
     ```
   - Run `python -m filtra run --resume "$target\resume sample.pdf" --jd "$target\jd sample.txt"`.
   - Verify the CLI output quotes each filename, reports the detected encodings, and uses only `\n` newlines.
5. **Windows-1252 fallback**
   - Edit the copied job description in Notepad and save it using **ANSI** encoding.
   - Rerun the CLI command and confirm the output now reports `Windows-1252` for the job description while succeeding.
6. **Result capture**
   - Record timestamps, observed outputs, and any deviations or remediation steps applied.
   - If issues arise, file them with logs and attach this runbook as supporting evidence.

## Execution Log
| Date | Operator | Outcome | Notes |
| ---- | -------- | ------- | ----- |
| YYYY-MM-DD | name | PASS/FAIL | e.g., cache size, timings, remediation applied |
