<#
.SYNOPSIS
    Convenience wrapper to prime Filtra dependencies via the warm-up command.
.DESCRIPTION
    Ensures the required environment variables are present, shows the cache target,
    then executes `python -m filtra warm-up` with any additional arguments you supply.
    Use this script before live demos to pre-download Hugging Face weights and
    verify OpenRouter connectivity without waiting during the main run.
#>
[CmdletBinding()]
param(
    [string[]]
    $WarmupArgs = @()
)

Write-Host "=== Filtra Warm-up Demo ===" -ForegroundColor Cyan

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCommand) {
    throw "Python executable not found on PATH. Install Python 3.10.11 before running warm-up."
}

if (-not $env:OPENROUTER_API_KEY) {
    Write-Warning "OPENROUTER_API_KEY is not set. Warm-up will exit with remediation guidance."
    Write-Host "Use: `setx OPENROUTER_API_KEY 'sk-...'` and open a new PowerShell session." -ForegroundColor Yellow
}

$cacheRoot = if ($env:LOCALAPPDATA) {
    Join-Path $env:LOCALAPPDATA 'filtra\models'
} else {
    Join-Path (Join-Path $env:USERPROFILE '.cache') 'filtra\models'
}

function Get-ProxyStatus {
    param(
        [string]$Value
    )

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return '(not set)'
    }

    return 'set (value hidden)'
}

$proxyStatuses = [ordered]@{
    'HTTPS_PROXY' = Get-ProxyStatus $env:HTTPS_PROXY
    'HTTP_PROXY'  = Get-ProxyStatus $env:HTTP_PROXY
    'NO_PROXY'    = Get-ProxyStatus $env:NO_PROXY
}

Write-Host "Model cache target : $cacheRoot" -ForegroundColor Gray
Write-Host "Proxy environment  :" -ForegroundColor Gray
foreach ($name in $proxyStatuses.Keys) {
    $status = $proxyStatuses[$name]
    Write-Host ("  {0,-11}: {1}" -f $name, $status) -ForegroundColor Gray
}

if (-not ($env:HTTPS_PROXY -or $env:HTTP_PROXY -or $env:NO_PROXY)) {
    Write-Host "  (none configured; direct internet access assumed)" -ForegroundColor Gray
}
Write-Host "Launching warm-up..." -ForegroundColor Yellow

$pythonArgs = @('-m', 'filtra', 'warm-up') + $WarmupArgs
& $pythonCommand.Path @pythonArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host "Warm-up completed successfully. Subsequent runs will skip cold downloads." -ForegroundColor Green
} else {
    Write-Warning "Warm-up exited with code $LASTEXITCODE. Review the remediation hints above."
}
