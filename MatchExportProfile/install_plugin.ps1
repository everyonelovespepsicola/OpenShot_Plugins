# Install Script for OpenShot MatchExportProfile Plugin

$PluginName = "MatchExportProfile"
$SourceDir = $PSScriptRoot

# 1. Target User Plugins Folder
$UserOpenShotDir = Join-Path $env:USERPROFILE ".openshot_qt"
$UserPluginsDir = Join-Path $UserOpenShotDir "plugins"

Write-Host "Installing OpenShot Plugin: $PluginName..." -ForegroundColor Cyan

if (-not (Test-Path $UserPluginsDir)) {
    New-Item -ItemType Directory -Force -Path $UserPluginsDir | Out-Null
    Write-Host "Created plugins directory at $UserPluginsDir" -ForegroundColor Green
}

# Target directory inside user plugins
$TargetDir = Join-Path $UserPluginsDir $PluginName
if (-not (Test-Path $TargetDir)) {
    New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
}

# Copy python files
Copy-Item -Path (Join-Path $SourceDir "*.py") -Destination $TargetDir -Force
Write-Host "Copied plugin files to: $TargetDir" -ForegroundColor Green

# 2. Check system installation path for convenience
$ProgramFilesDir = "C:\Program Files\OpenShot Video Editor\classes"
if (Test-Path $ProgramFilesDir) {
    try {
        Copy-Item -Path (Join-Path $SourceDir "match_export_profile.py") -Destination $ProgramFilesDir -Force -ErrorAction SilentlyContinue
        Write-Host "Also registered with OpenShot system classes at: $ProgramFilesDir" -ForegroundColor Green
    } catch {
        # Ignore if permissions restricted
    }
}

Write-Host "Installation complete! Restart OpenShot Video Editor to enable the plugin." -ForegroundColor Yellow
