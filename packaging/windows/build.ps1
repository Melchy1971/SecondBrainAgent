<# Reproducible Jarvis Windows release: frozen app, portable ZIP, EXE, MSI, SBOM and manifest. #>
[CmdletBinding()]
param(
    [switch]$SkipInstaller,
    [switch]$SkipMsi,
    [switch]$SkipInstallerSmoke,
    [string]$Python = "python",
    [string]$SourceDateEpoch = "1767225600"
)
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$DistDir = Join-Path $Root "dist"
$BuildDir = Join-Path $Root "build\windows-release"
$ReleaseDir = Join-Path $DistDir "release"
$AppOut = Join-Path $DistDir "Jarvis"
$Venv = Join-Path $BuildDir "venv"
$Constraints = Join-Path $PSScriptRoot "constraints.txt"
$env:SOURCE_DATE_EPOCH = $SourceDateEpoch
$env:PYTHONHASHSEED = "0"
Set-Location $Root

$Version = (& $Python -c "from secondbrain.version import get_version; print(get_version())").Trim()
if (-not $Version) { throw "Version konnte nicht ermittelt werden." }

if (Test-Path $BuildDir) { Remove-Item -Recurse -Force $BuildDir }
if (Test-Path $AppOut) { Remove-Item -Recurse -Force $AppOut }
if (Test-Path $ReleaseDir) { Remove-Item -Recurse -Force $ReleaseDir }
New-Item -ItemType Directory -Force -Path $BuildDir, $ReleaseDir | Out-Null

& $Python -m venv $Venv
$Py = Join-Path $Venv "Scripts\python.exe"
& $Py -m pip install --disable-pip-version-check -c $Constraints -r requirements-runtime.txt -r requirements-security.txt -r requirements-vision.txt
& $Py -m pip install --disable-pip-version-check -c $Constraints pyinstaller
& $Py -m pip check

& $Py -m PyInstaller --noconfirm --clean --distpath $DistDir --workpath $BuildDir (Join-Path $PSScriptRoot "jarvis.spec")
if (-not (Test-Path (Join-Path $AppOut "Jarvis.exe"))) { throw "Jarvis.exe fehlt." }
if (-not (Test-Path (Join-Path $AppOut "jarvis-cli.exe"))) { throw "jarvis-cli.exe fehlt." }

# Payload gate blocks tests, state, credentials, private keys and developer paths.
& $Py -m secondbrain.install.release_pipeline scan $AppOut
& (Join-Path $AppOut "jarvis-cli.exe") smoke-test
if ($LASTEXITCODE -ne 0) { throw "Frozen smoke test fehlgeschlagen: $LASTEXITCODE" }

$Portable = Join-Path $ReleaseDir "Jarvis-$Version-portable-win64.zip"
& $Py -m secondbrain.install.release_pipeline zip $AppOut $Portable

if (-not $SkipInstaller) {
    $Iscc = Get-Command iscc.exe -ErrorAction SilentlyContinue
    if ($null -eq $Iscc) {
        $IsccPath = @("${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe", "$env:ProgramFiles\Inno Setup 6\ISCC.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
    } else { $IsccPath = $Iscc.Source }
    if (-not $IsccPath) { throw "Inno Setup 6 fehlt. Nur mit -SkipInstaller bewusst auslassen." }
    & $IsccPath "/DAppVersion=$Version" (Join-Path $PSScriptRoot "installer.iss")
}

if (-not $SkipMsi) {
    $Wix = Get-Command wix.exe -ErrorAction SilentlyContinue
    $Heat = Get-Command heat.exe -ErrorAction SilentlyContinue
    if ($null -eq $Wix -or $null -eq $Heat) { throw "WiX v4 mit heat fehlt. Nur mit -SkipMsi bewusst auslassen." }
    $Harvest = Join-Path $BuildDir "harvest.wxs"
    & $Heat.Source dir $AppOut -cg JarvisFiles -dr INSTALLFOLDER -srd -sreg -gg -var var.SourceDir -out $Harvest
    & $Wix.Source build (Join-Path $PSScriptRoot "jarvis.wxs") $Harvest -d "SourceDir=$AppOut" -d "AppVersion=$Version" -o (Join-Path $ReleaseDir "Jarvis-$Version.msi")
}

if (-not $SkipInstaller -and -not $SkipInstallerSmoke) {
    & (Join-Path $PSScriptRoot "installer_smoke.ps1") `
        -SetupPath (Join-Path $ReleaseDir "Jarvis-Setup-$Version.exe") `
        -PortableZip $Portable
}

& $Py -m secondbrain.install.release_pipeline sbom (Join-Path $ReleaseDir "Jarvis-$Version-sbom.cdx.json")
& $Py -m secondbrain.install.release_pipeline metadata $ReleaseDir --version $Version --notes-file (Join-Path $Root "RELEASE_NOTES.md")
& $Py -c "from secondbrain.install.release_pipeline import verify_checksums; import sys; sys.exit(0 if verify_checksums(r'$ReleaseDir') else 1)"
if ($LASTEXITCODE -ne 0) { throw "Checksum-Pruefung fehlgeschlagen." }

Write-Host "Jarvis $Version: reproduzierbare Release-Artefakte in $ReleaseDir" -ForegroundColor Green
