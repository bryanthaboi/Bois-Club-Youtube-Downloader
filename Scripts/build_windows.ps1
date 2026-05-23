# Build Bois Club YouTube Downloader as a Windows .exe.
# Bundles ffmpeg.exe so users don't need to install it.
#
# Usage:
#   pwsh ./Scripts/build_windows.ps1

$ErrorActionPreference = 'Stop'

$Root    = (Resolve-Path "$PSScriptRoot/..").Path
$AppName = 'Bois Club YouTube Downloader'
$Venv    = Join-Path $Root '.venv-build'
$Dist    = Join-Path $Root 'dist'
$Build   = Join-Path $Root 'build'
$FfDir   = Join-Path $Root '.ffmpeg'
$FfExe   = Join-Path $FfDir 'ffmpeg.exe'

Set-Location $Root

Write-Host "==> python venv ($Venv)"
python -m venv $Venv
& "$Venv/Scripts/python.exe" -m pip install --upgrade pip wheel | Out-Null
& "$Venv/Scripts/pip.exe" install -r requirements.txt pyinstaller | Out-Null

if (-not (Test-Path $FfExe)) {
    Write-Host "==> fetching ffmpeg (gyan.dev essentials build)"
    New-Item -ItemType Directory -Force -Path $FfDir | Out-Null
    $zip = Join-Path $FfDir 'ffmpeg.zip'
    Invoke-WebRequest -Uri 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -OutFile $zip
    Expand-Archive -Path $zip -DestinationPath $FfDir -Force
    $extracted = Get-ChildItem $FfDir -Directory | Where-Object { $_.Name -like 'ffmpeg-*' } | Select-Object -First 1
    Copy-Item (Join-Path $extracted.FullName 'bin/ffmpeg.exe') $FfExe -Force
    Remove-Item $zip
}

Write-Host "==> pyinstaller"
if (Test-Path $Dist)  { Remove-Item -Recurse -Force $Dist }
if (Test-Path $Build) { Remove-Item -Recurse -Force $Build }

& "$Venv/Scripts/pyinstaller.exe" `
    --noconfirm `
    --windowed `
    --onedir `
    --name "$AppName" `
    --add-binary "$FfExe;." `
    ytmp3.py

Write-Host ""
Write-Host "Built: $Dist/$AppName/"
