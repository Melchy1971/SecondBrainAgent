<# Automated install/update/repair/uninstall/portable smoke test. #>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$SetupPath,
    [Parameter(Mandatory)][string]$PortableZip
)
$ErrorActionPreference = "Stop"
$Sandbox = Join-Path ([IO.Path]::GetTempPath()) ("jarvis-installer-smoke-" + [guid]::NewGuid())
$InstallDir = Join-Path $Sandbox "program"
$UserData = Join-Path $Sandbox "userdata"
$PortableDir = Join-Path $Sandbox "portable"

function Invoke-Checked([string]$File, [string[]]$Arguments) {
    $process = Start-Process -FilePath $File -ArgumentList $Arguments -Wait -PassThru -WindowStyle Hidden
    if ($process.ExitCode -ne 0) { throw "$File failed with exit code $($process.ExitCode)" }
}

try {
    New-Item -ItemType Directory -Force -Path $Sandbox, $UserData | Out-Null
    $env:JARVIS_HOME = $UserData
    $installArgs = @("/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/CURRENTUSER", "/DIR=$InstallDir")

    # Fresh install and first-start/config/GUI-HUD diagnostics.
    Invoke-Checked $SetupPath $installArgs
    $Cli = Join-Path $InstallDir "jarvis-cli.exe"
    Invoke-Checked $Cli @("smoke-test")
    Invoke-Checked $Cli @("config-doctor")
    Invoke-Checked $Cli @("gui-doctor")
    $sentinel = Join-Path $UserData "data\installer-smoke.keep"
    New-Item -ItemType Directory -Force -Path (Split-Path $sentinel) | Out-Null
    Set-Content -Path $sentinel -Value "preserve" -NoNewline

    # A second and third run exercise update detection and repair/idempotency.
    Invoke-Checked $SetupPath $installArgs
    Invoke-Checked $SetupPath $installArgs
    if ((Get-Content -Raw $sentinel) -ne "preserve") { throw "Update/repair overwrote user data." }

    # Default uninstall must preserve data.
    Invoke-Checked (Join-Path $InstallDir "unins000.exe") @("/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART")
    if (-not (Test-Path $sentinel)) { throw "Default uninstall removed user data." }

    # Portable startup uses its own JarvisData directory.
    Expand-Archive -Path $PortableZip -DestinationPath $PortableDir
    Remove-Item Env:JARVIS_HOME -ErrorAction SilentlyContinue
    Invoke-Checked (Join-Path $PortableDir "jarvis-cli.exe") @("smoke-test")
    if (-not (Test-Path (Join-Path $PortableDir "JarvisData"))) { throw "Portable data directory missing." }
}
finally {
    Remove-Item Env:JARVIS_HOME -ErrorAction SilentlyContinue
    if (Test-Path $Sandbox) { Remove-Item -Recurse -Force $Sandbox }
}
