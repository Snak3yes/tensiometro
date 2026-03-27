param(
    [string]$Name = "Tenciometro",
    [string]$EntryPoint = "main.py"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$workspaceParent = Split-Path -Parent $repoRoot
$buildRoot = Join-Path $workspaceParent "_build"
$distRoot = Join-Path $workspaceParent "_dist"
$workPath = Join-Path $buildRoot $Name
$distPath = Join-Path $distRoot $Name
$entryPath = Join-Path $repoRoot $EntryPoint

if (-not (Test-Path $entryPath)) {
    throw "Entry point not found: $entryPath"
}

New-Item -ItemType Directory -Force -Path $buildRoot | Out-Null
New-Item -ItemType Directory -Force -Path $distRoot | Out-Null

if (Test-Path $workPath) {
    Remove-Item -Recurse -Force $workPath
}

if (Test-Path $distPath) {
    Remove-Item -Recurse -Force $distPath
}

$pyInstallerCmd = Get-Command pyinstaller -ErrorAction SilentlyContinue
if (-not $pyInstallerCmd) {
    throw "pyinstaller not found in PATH. Install it before running this script."
}

Push-Location $repoRoot
try {
    & $pyInstallerCmd.Source `
        --noconfirm `
        --clean `
        --onedir `
        --name $Name `
        --workpath $workPath `
        --distpath $distRoot `
        $EntryPoint
}
finally {
    Pop-Location
}

Write-Host "Build generated outside the worktree:"
Write-Host "  work: $workPath"
Write-Host "  dist: $distPath"
