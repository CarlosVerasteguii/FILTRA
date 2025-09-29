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
     Copy-Item .\samples\inputs\resume_windows_sample.txt "$target\resume sample.txt"
     Copy-Item .\samples\inputs\jd_windows_sample.txt "$target\jd sample.txt"
     ```
   - Run `python -m filtra run --resume "$target\resume sample.txt" --jd "$target\jd sample.txt"`.
   - Verify the CLI output quotes each filename, reports `UTF-8 (with BOM)` for the resume sample and `Windows-1252` for the job description, and uses only `\n` newlines.
5. **Windows-1252 fallback**
   - The job description sample already ships as Windows-1252. Open `jd sample.txt` in Notepad, make a minor edit, and re-save with **ANSI** to confirm the fallback persists after manual changes.
   - Rerun the CLI command and confirm the output reports `Windows-1252` for the job description while succeeding.
6. **Result capture**
   - Record timestamps, observed outputs, and any deviations or remediation steps applied.
   - If issues arise, file them with logs and attach this runbook as supporting evidence.

## Execution Log
| Date       | Operator | Outcome | Notes                                                                                                                                                                                                                              |
| ---------- | -------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2025-09-27 | carlosh  | FAIL    | Health diagnosis failed (OpenRouter API Key and Proxy not configured). Warm-up script failed (--quiet not recognized, API Key missing). Sample files (samples/inputs) not found. Command `filtra run` failed due to missing files. |
| 2025-09-28 | carlosh  | PASS    | ✅ ENCODING: UTF-8-sig (resume) and Windows-1252 (JD) detected correctly. ✅ PATHS: Correct handling of paths with spaces. ✅ NEWLINES: Normalized output. ❌ API Key missing (does not block encoding/paths functionality).           |
