# Infrastructure and Deployment

### Infrastructure as Code
- **Tool:** Not required (local CLI execution)
- **Location:** N/A
- **Approach:** Distribute as Python project; optional scripts automate `pip-tools` compilation and model warm-up caching.

### Deployment Strategy
- **Strategy:** Local installation via `pip install -r requirements.txt` then `python -m filtra`. Optional packaging (pipx/PyInstaller) if requested later.
- **CI/CD Platform:** GitHub Actions (Windows + Linux matrix).
- **Pipeline Configuration:** `.github/workflows/ci.yml` running lint, unit/integration tests, golden sample diff.

### Environments
- **Development:** Engineer laptops (Windows 11 target, macOS/Linux secondary) running CLI with environment variable secrets.
- **Demo:** Same setup executed by recruiters after warm-up.

### Environment Promotion Flow
```
Git commit → GitHub Actions CI → Tag release → Share installer/instructions for demo use.
```

### Rollback Strategy
- **Primary Method:** Revert to prior git tag & requirements lock, reinstall dependencies, rerun warm-up.
- **Trigger Conditions:** Golden sample regression, CI failure, or OpenRouter incompatibility.
- **Recovery Time Objective:** <15 minutes.

