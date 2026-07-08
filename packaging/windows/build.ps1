<#
.SYNOPSIS
    Produktiver Windows-Build fuer Jarvis: PyInstaller -> Portable ZIP -> Installer.

.DESCRIPTION
    Fuehrt den kompletten Release-Build in einem sauberen venv aus und legt alle
    Artefakte unter dist\release ab. Erfordert Python 3.11+ auf Windows. Inno Setup
    (iscc) ist optional; fehlt es, wird der Installer-Schritt uebersprungen.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File packaging\windows\build.ps1
#>
[CmdletBinding()]
param(
    [switch]$SkipInstaller,
    [switch]$SkipZip
)
$ErrorActionPreference = "Stop"

$Root       = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Spec       = Join-Path $PSScriptRoot "jarvis.spec"
$Iss        = Join-Path $PSScriptRoot "installer.iss"
$DistDir    = Join-Path $Root "dist"
$BuildDir   = Join-Path $Root "build"
$ReleaseDir = Join-Path $DistDir "release"
$AppOut     = Join-Path $DistDir "Jarvis"

Write-Host "== Jarvis Windows build ==" -ForegroundColor Cyan
Set-Location $Root

# Version aus der Single-Source-of-Truth lesen.
$Version = (& python -c "from secondbrain.version import get_version; print(get_version())").Trim()
if (-not $Version) { throw "Version konnte nicht ermittelt werden." }
Write-Host "Version: $Version"

# 1) Sauberes venv + Abhaengigkeiten.
$Venv = Join-Path $BuildDir "buildvenv"
if (Test-Path $Venv) { Remove-Item -Recurse -Force $Venv }
python -m venv $Venv
$Py = Join-Path $Venv "Scripts\python.exe"
& $Py -m pip install --upgrade pip wheel | Out-Null
foreach ($req in @("requirements-runtime.txt","requirements-security.txt","requirements-vision.txt")) {
    $p = Join-Path $Root $req
    if (Test-Path $p) { & $Py -m pip install -r $p }
}
& $Py -m pip install pyinstaller

# 2) Vorherige Outputs entfernen und PyInstaller ausfuehren.
if (Test-Path $AppOut) { Remove-Item -Recurse -Force $AppOut }
New-Item -ItemType Directory -Force -Path $ReleaseDir | Out-Null
& $Py -m PyInstaller --noconfirm --clean --distpath $DistDir --workpath $BuildDir $Spec
if (-not (Test-Path (Join-Path $AppOut "Jarvis.exe"))) { throw "PyInstaller-Output fehlt." }

# 3) Build-Smoke-Test (frozen exe startet und meldet ok).
Write-Host "== Smoke-Test (frozen) ==" -ForegroundColor Cyan
& (Join-Path $AppOut "jarvis-cli.exe") smoke-test
if ($LASTEXITCODE -ne 0) { throw "Smoke-Test fehlgeschlagen (Code $LASTEXITCODE)." }

# 4) Portable ZIP.
if (-not $SkipZip) {
    $Zip = Join-Path $ReleaseDir "Jarvis-$Version-portable-win64.zip"
    if (Test-Path $Zip) { Remove-Item -Force $Zip }
    Compress-Archive -Path (Join-Path $AppOut "*") -DestinationPath $Zip
    Write-Host "Portable ZIP: $Zip" -ForegroundColor Green
}

# 5) Installer (Inno Setup), wenn iscc verfuegbar ist.
if (-not $SkipInstaller) {
    $Iscc = (Get-Command iscc.exe -ErrorAction SilentlyContinue)
    if ($null -eq $Iscc) {
        $Iscc = @("${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe","$env:ProgramFiles\Inno Setup 6\ISCC.exe") |
                 Where-Object { Test-Path $_ } | Select-Object -First 1
    } else { $Iscc = $Iscc.Source }
    if ($Iscc) {
        & $Iscc "/DAppVersion=$Version" $Iss
        Write-Host "Installer: $ReleaseDir\Jarvis-Setup-$Version.exe" -ForegroundColor Green
    } else {
        Write-Warning "Inno Setup (iscc) nicht gefunden - Installer uebersprungen. Portable ZIP steht bereit."
    }
}

# 6) Checksums fuer alle Release-Artefakte.
Get-ChildItem $ReleaseDir -File | ForEach-Object {
    $hash = (Get-FileHash $_.FullName -Algorithm SHA256).Hash
    "$hash  $($_.Name)" | Out-File -Append -Encoding ascii (Join-Path $ReleaseDir "SHA256SUMS.txt")
}
Write-Host "== Build fertig. Artefakte in $ReleaseDir ==" -ForegroundColor Cyan
