# ZEUS-001: deterministic, local-only import of ORIGINAL Hermes Git history.
# Execute in PowerShell 7 with Git on a clean Zeus clone.
param([string]$Branch = "work/ZEUS-001-import-brand")
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Pinned = "53df274b08f2bbbe82bb67bb50c7571952e95809"
$UpstreamUrl = "https://github.com/NousResearch/hermes-agent.git"

function Git {
    & git @args
    if ($LASTEXITCODE -ne 0) {
        throw "Git failed (exit $LASTEXITCODE): $($args -join ' ')"
    }
}

Set-Location (Resolve-Path (Join-Path $PSScriptRoot "../.."))
Git rev-parse --is-inside-work-tree
$origin = (& git remote get-url origin).Trim()
if ($LASTEXITCODE -ne 0 -or $origin -notmatch '(?i)KayzenRoot/zeus-agent(\.git)?$') {
    throw "Unexpected origin: $origin. Clone the existing KayzenRoot/zeus-agent repository."
}
if (@(& git status --porcelain).Where({ $_ -ne "" }).Count -gt 0) {
    throw "The working tree is dirty. Save existing work before importing."
}
Git fetch origin
Git switch $Branch
$remotes = @(& git remote)
if ($remotes -notcontains "upstream") {
    Git remote add upstream $UpstreamUrl
} else {
    $url = (& git remote get-url upstream).Trim()
    if ($url -ne $UpstreamUrl) {
        throw "Existing upstream remote has a different URL: $url"
    }
}
Git fetch upstream main
Git cat-file -e ($Pinned + "^{commit}")
& git merge-base --is-ancestor $Pinned upstream/main
if ($LASTEXITCODE -ne 0) { throw "Pinned revision no longer belongs to upstream/main." }
$licenseText = & git show ($Pinned + ":LICENSE")
if ($LASTEXITCODE -ne 0 -or ($licenseText -join [Environment]::NewLine) -notmatch "Nous Research") {
    throw "Original MIT license not found. Import aborted."
}
# Preserve original upstream commit ancestry, not a downloaded ZIP snapshot.
Git merge --allow-unrelated-histories --no-ff --no-edit $Pinned

$python = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } elseif (Get-Command py -ErrorAction SilentlyContinue) { "py" } else { throw "Python 3 missing" }
& $python .zeus/tools/rebrand.py --apply
if ($LASTEXITCODE -ne 0) { throw "Rebrand failed; inspect local changes." }
& $python -m unittest discover -s .zeus/tests -p "test_*.py"
if ($LASTEXITCODE -ne 0) { throw "Brand tests failed; do not push." }
Git diff --check
Write-Host "Upstream Git history now merged locally; first-pass brand assets updated."
Write-Host "Before pushing: run npm web/desktop checks and inspect visual UI + authentication."
Write-Host "Inspect git diff and staged paths. Commit, push this same branch, and update ZEUS-001 PR after evidence."
Write-Host "No VPS, force push, auto-publish, or automatic merge attempted."
