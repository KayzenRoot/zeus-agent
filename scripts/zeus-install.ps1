# Zeus-owned local installer (issue #5, flow B).
# Installs from this verified checkout into an isolated root; never runs an
# upstream installer. Full contract: scripts/zeus_install_local.py --help.
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Error 'python 3 is required to run the Zeus local installer'
    exit 1
}
& $python.Source (Join-Path $repo 'scripts/zeus_install_local.py') @args
exit $LASTEXITCODE
