param(
    [string]$ExeName = "Tenciometro",
    [string]$PackageName = "tenciometro_build_V0.1",
    [string]$EntryPoint = "main.py"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$workspaceParent = Split-Path -Parent $repoRoot
$buildRoot = Join-Path $workspaceParent "_build"
$distRoot = Join-Path $workspaceParent "_dist"
$workPath = Join-Path $buildRoot $PackageName
$pyInstallerDistRoot = Join-Path $distRoot $PackageName
$pyInstallerDistPath = Join-Path $pyInstallerDistRoot $ExeName
$finalPackagePath = Join-Path $workspaceParent $PackageName
$entryPath = Join-Path $repoRoot $EntryPoint
$iconPath = Join-Path $repoRoot "resources\app_icon.ico"
$stylesheetTemplatePath = Join-Path $repoRoot "consumo_lib\ui\styles.qss.template"
$specPath = Join-Path $repoRoot "$ExeName.spec"

$runtimeDirectories = @(
    "config",
    "assets",
    "resources",
    "data",
    "patterns",
    "recipes",
    "map_programs",
    "tension_routines"
)

if (-not (Test-Path $entryPath)) {
    throw "Entry point not found: $entryPath"
}

New-Item -ItemType Directory -Force -Path $buildRoot | Out-Null
New-Item -ItemType Directory -Force -Path $distRoot | Out-Null

foreach ($path in @($workPath, $pyInstallerDistRoot, $finalPackagePath)) {
    if (Test-Path $path) {
        Remove-Item -Recurse -Force $path
    }
}

$pyInstallerCmd = Get-Command pyinstaller -ErrorAction SilentlyContinue
if (-not $pyInstallerCmd) {
    throw "pyinstaller not found in PATH. Install it before running this script."
}

Push-Location $repoRoot
try {
    $pyInstallerArgs = @(
        "--noconfirm",
        "--clean",
        "--onedir",
        "--name", $ExeName,
        "--workpath", $workPath,
        "--distpath", $pyInstallerDistRoot
    )

    if (Test-Path $iconPath) {
        $pyInstallerArgs += @("--icon", $iconPath)
    }

    if (Test-Path $stylesheetTemplatePath) {
        $pyInstallerArgs += @("--add-data", "${stylesheetTemplatePath};consumo_lib\ui")
    }

    $pyInstallerArgs += $EntryPoint

    & $pyInstallerCmd.Source @pyInstallerArgs
}
finally {
    Pop-Location
}

if (-not (Test-Path $pyInstallerDistPath)) {
    throw "PyInstaller output folder not found: $pyInstallerDistPath"
}

New-Item -ItemType Directory -Force -Path $finalPackagePath | Out-Null

Get-ChildItem -Force $pyInstallerDistPath | ForEach-Object {
    Copy-Item -Recurse -Force $_.FullName -Destination $finalPackagePath
}

foreach ($dir in $runtimeDirectories) {
    $sourceDir = Join-Path $repoRoot $dir
    if (Test-Path $sourceDir) {
        $targetDir = Join-Path $finalPackagePath $dir
        Copy-Item -Recurse -Force $sourceDir -Destination $targetDir
    }
}

if (Test-Path $specPath) {
    Remove-Item -Force $specPath
}

Write-Host "Build generated outside the worktree:"
Write-Host "  build work: $workPath"
Write-Host "  pyinstaller dist: $pyInstallerDistPath"
Write-Host "  final package: $finalPackagePath"
