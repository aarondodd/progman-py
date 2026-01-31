#
# Build script for Program Manager (Windows)
# Creates a single-file executable using PyInstaller
#

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppName = "progman"
$DistDir = Join-Path $ScriptDir "dist"
$BuildDir = Join-Path $ScriptDir "build"
$VenvDir = Join-Path $ScriptDir ".venv"
$BinDir = Join-Path $env:USERPROFILE "bin"

Write-Host "=== Program Manager Build Script ===" -ForegroundColor Cyan
Write-Host ""

# Check if we're in a virtual environment, if not activate or create one
if (-not $env:VIRTUAL_ENV) {
    if (Test-Path $VenvDir) {
        Write-Host "Activating virtual environment..."
        & "$VenvDir\Scripts\Activate.ps1"
    } else {
        Write-Host "Creating virtual environment..."
        python -m venv $VenvDir
        & "$VenvDir\Scripts\Activate.ps1"
    }
}

# Install dependencies
Write-Host "Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r (Join-Path $ScriptDir "requirements.txt")
pip install --quiet pyinstaller

# Clean previous builds
Write-Host "Cleaning previous builds..."
if (Test-Path $DistDir) { Remove-Item -Recurse -Force $DistDir }
if (Test-Path $BuildDir) { Remove-Item -Recurse -Force $BuildDir }

# Run PyInstaller
Write-Host "Building executable with PyInstaller..."
Set-Location $ScriptDir

pyinstaller `
    --name $AppName `
    --onefile `
    --windowed `
    --noconfirm `
    --clean `
    --hidden-import=PyQt6 `
    --hidden-import=PyQt6.QtCore `
    --hidden-import=PyQt6.QtGui `
    --hidden-import=PyQt6.QtWidgets `
    --collect-all=PyQt6 `
    main.py

# Check if build succeeded
$ExePath = Join-Path $DistDir "$AppName.exe"
if (-not (Test-Path $ExePath)) {
    Write-Host "ERROR: Build failed - executable not found" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Build successful!" -ForegroundColor Green
Write-Host "Executable: $ExePath"

# Create ~/bin if it doesn't exist
if (-not (Test-Path $BinDir)) {
    Write-Host "Creating $BinDir..."
    New-Item -ItemType Directory -Path $BinDir | Out-Null
}

# Copy to ~/bin
# Remove/rename old executable first (allows replacing even if currently running)
$DestPath = Join-Path $BinDir "$AppName.exe"
$OldPath = Join-Path $BinDir "$AppName.exe.old"
Write-Host "Installing to $DestPath..."
# Try to remove .old file, but ignore errors (it may be locked from previous run)
if (Test-Path $OldPath) {
    try { Remove-Item -Force $OldPath -ErrorAction SilentlyContinue } catch { }
}
# Rename current exe to .old (works even if running on Windows)
if (Test-Path $DestPath) {
    try { Rename-Item $DestPath $OldPath -ErrorAction SilentlyContinue } catch { }
}
Copy-Item $ExePath $DestPath -Force

Write-Host ""
Write-Host "=== Installation Complete ===" -ForegroundColor Cyan
Write-Host "Executable installed to: $DestPath"
Write-Host ""
Write-Host "Make sure $BinDir is in your PATH."
Write-Host "You can add it via System Properties > Environment Variables"
Write-Host ""
