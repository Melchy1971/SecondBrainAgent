<# Standalone target harness: requires only PowerShell and signed installers. #>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$CurrentSetup,
    [Parameter(Mandatory)][string]$PreviousSetup,
    [Parameter(Mandatory)][string]$EvidencePath,
    [switch]$PurgeUserData
)
$ErrorActionPreference = "Stop"
$Workspace = Join-Path ([IO.Path]::GetTempPath()) ("Jarvis Gate " + [guid]::NewGuid())
$InstallDir = Join-Path $Workspace "Program Files With Spaces\Jarvis"
$UserData = Join-Path $Workspace "User Data With Spaces"
$Desktop = [Environment]::GetFolderPath("Desktop")
$Startup = [Environment]::GetFolderPath("Startup")
$Phases = [Collections.Generic.List[object]]::new()

function Add-Phase([string]$Name, [bool]$Ok, [string]$Detail) {
    $Phases.Add([ordered]@{ name=$Name; status=$(if ($Ok) {"PASS"} else {"BLOCKED"}); detail=$Detail })
    if (-not $Ok) { throw "phase_failed:$Name" }
}
function Invoke-Checked([string]$File, [string[]]$Arguments) {
    $p = Start-Process -FilePath $File -ArgumentList $Arguments -Wait -PassThru -WindowStyle Hidden
    if ($p.ExitCode -ne 0) { throw "process_failed" }
}
function Install-Jarvis([string]$Setup) {
    Invoke-Checked $Setup @("/VERYSILENT","/SUPPRESSMSGBOXES","/NORESTART","/CURRENTUSER",
        "/TASKS=desktopicon","/DIR=$InstallDir")
}
function Uninstall-Jarvis {
    $uninstaller = Join-Path $InstallDir "unins000.exe"
    Invoke-Checked $uninstaller @("/VERYSILENT","/SUPPRESSMSGBOXES","/NORESTART")
}

try {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "standard_user_required"
    }
    New-Item -ItemType Directory -Force -Path $Workspace,$UserData | Out-Null
    $env:JARVIS_HOME = $UserData
    Install-Jarvis $PreviousSetup
    Add-Phase "silent_install" (Test-Path (Join-Path $InstallDir "Jarvis.exe")) "per-user silent install"
    $shortcut = Join-Path $Desktop "Jarvis.lnk"
    Add-Phase "desktop_shortcut" (Test-Path $shortcut) "desktop shortcut created"
    Invoke-Checked (Join-Path $InstallDir "jarvis-cli.exe") @("smoke-test")
    Add-Phase "application_start" $true "frozen application started"
    Invoke-Checked (Join-Path $InstallDir "jarvis-cli.exe") @("config-doctor")
    Add-Phase "health_check" $true "frozen health check passed"
    $sentinel = Join-Path $UserData "vault\preserve.sentinel"
    New-Item -ItemType Directory -Force -Path (Split-Path $sentinel) | Out-Null
    Set-Content -LiteralPath $sentinel -Value "preserve" -NoNewline
    Install-Jarvis $CurrentSetup
    Add-Phase "upgrade" ((Test-Path $sentinel) -and (Test-Path (Join-Path $InstallDir "Jarvis.exe"))) "upgrade preserved user data"
    Uninstall-Jarvis
    Install-Jarvis $PreviousSetup
    Add-Phase "rollback" ((Test-Path $sentinel) -and (Test-Path (Join-Path $InstallDir "Jarvis.exe"))) "previous signed version restored"
    Uninstall-Jarvis
    Add-Phase "uninstall" (-not (Test-Path (Join-Path $InstallDir "Jarvis.exe"))) "uninstall completed"
    if ($PurgeUserData -and (Test-Path $UserData)) {
        Remove-Item -LiteralPath $UserData -Recurse -Force
    }
    $executables = @(Get-ChildItem -LiteralPath $InstallDir -Recurse -Filter *.exe -ErrorAction SilentlyContinue)
    $startupLinks = @(Get-ChildItem -LiteralPath $Startup -Filter "Jarvis*.lnk" -ErrorAction SilentlyContinue)
    $runEntry = Get-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -ErrorAction SilentlyContinue
    $hasRunEntry = $null -ne $runEntry -and $null -ne $runEntry.Jarvis
    $credentialText = (& cmdkey.exe /list 2>$null) -join "`n"
    $credentialsRemain = $credentialText -match "(?i)Jarvis|SecondBrain"
    $dataPolicyOk = if ($PurgeUserData) { -not (Test-Path $UserData) } else { Test-Path $sentinel }
    Add-Phase "residue_check" (
        $executables.Count -eq 0 -and $startupLinks.Count -eq 0 -and
        -not $hasRunEntry -and -not $credentialsRemain -and $dataPolicyOk
    ) "no executable, autostart or credential residue; user-data policy honored"
}
catch {
    $known = @($Phases | ForEach-Object { $_.name })
    foreach ($name in @("silent_install","desktop_shortcut","application_start","health_check",
            "upgrade","rollback","uninstall","residue_check")) {
        if ($known -notcontains $name) {
            $Phases.Add([ordered]@{ name=$name; status="BLOCKED"; detail="controlled target failure" })
            break
        }
    }
}
finally {
    Remove-Item Env:JARVIS_HOME -ErrorAction SilentlyContinue
    $payload = [ordered]@{ schema="secondbrain.windows-installer-target.v1"; phases=$Phases }
    $json = $payload | ConvertTo-Json -Depth 5
    $parent = Split-Path -Parent $EvidencePath
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    $temporary = Join-Path $parent ("." + [IO.Path]::GetFileName($EvidencePath) + "." + [guid]::NewGuid() + ".tmp")
    [IO.File]::WriteAllText($temporary, $json, [Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $temporary -Destination $EvidencePath -Force
    if (Test-Path $Workspace) { Remove-Item -LiteralPath $Workspace -Recurse -Force }
}
if (@($Phases | Where-Object { $_.status -ne "PASS" }).Count -gt 0) { exit 2 }
