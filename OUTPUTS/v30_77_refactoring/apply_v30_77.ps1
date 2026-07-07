<#  apply_v30_77.ps1 — reversible Quarantäne + self-gating Abnahme (Windows)
    Ausführen:  powershell -ExecutionPolicy Bypass -File apply_v30_77.ps1
    Verhalten:  verschiebt die in DELTA_MANIFEST_v30_77.json gelisteten Module nach
                archive/v30_77_quarantine/, führt compileall + pytest + *_smoke.ps1 + launcher --help aus.
                Bei irgendeinem roten Schritt: automatischer, vollständiger Rollback. Nichts bleibt.
#>
$ErrorActionPreference = "Stop"
$here   = Split-Path -Parent $MyInvocation.MyCommand.Path      # ...\OUTPUTS\v30_77_refactoring
$top    = Resolve-Path (Join-Path $here "..\..")               # H:\SecondBrainAgent
$code   = Join-Path $top "SecondBrain-Agent"
$man    = Join-Path $here "DELTA_MANIFEST_v30_77.json"
$qrel   = "archive/v30_77_quarantine"
$qdir   = Join-Path $code $qrel

if (!(Test-Path $man)) { Write-Error "Manifest fehlt: $man"; exit 2 }
$data   = Get-Content $man -Raw | ConvertFrom-Json
$files  = $data.files_quarantined | ForEach-Object { $_ -replace '^SecondBrain-Agent/','' }

Write-Host "== v30.77 Quarantäne: $($files.Count) Module ==" -ForegroundColor Cyan
Push-Location $code
$usesGit = (Test-Path (Join-Path $code ".git"))
New-Item -ItemType Directory -Force -Path $qdir | Out-Null
$moved = @()
try {
  foreach ($f in $files) {
    $src = Join-Path $code $f
    if (!(Test-Path $src)) { Write-Warning "fehlt, übersprungen: $f"; continue }
    $flat = ($f -replace '[\\/]','.')
    $dst  = Join-Path $qdir $flat
    if ($usesGit) { git mv -f -- "$f" "$qrel/$flat" 2>$null; if ($LASTEXITCODE -ne 0) { Move-Item -Force $src $dst } }
    else { Move-Item -Force $src $dst }
    $moved += ,@($src,$dst,$f,$flat)
  }

  $fail = $false
  Write-Host "-- compileall --" -ForegroundColor Yellow
  python -m compileall -q secondbrain; if ($LASTEXITCODE -ne 0) { $fail = $true }

  if (-not $fail) {
    Write-Host "-- pytest -q --" -ForegroundColor Yellow
    python -m pytest -q; if ($LASTEXITCODE -ne 0) { $fail = $true }
  }
  if (-not $fail) {
    Write-Host "-- GUI/agent smoke tests --" -ForegroundColor Yellow
    Get-ChildItem "scripts\*_smoke.ps1" | ForEach-Object {
      powershell -ExecutionPolicy Bypass -File $_.FullName
      if ($LASTEXITCODE -ne 0) { Write-Warning "smoke rot: $($_.Name)"; $fail = $true }
    }
  }
  if (-not $fail) {
    Write-Host "-- launcher smoke --" -ForegroundColor Yellow
    python launcher.py --help | Out-Null; if ($LASTEXITCODE -ne 0) { $fail = $true }
  }

  if ($fail) { throw "Validierung ROT — Rollback." }
  Write-Host "== GRÜN. Quarantäne abgenommen. $($moved.Count) Module in $qrel ==" -ForegroundColor Green
  Write-Host "Commit-Vorschlag: git add -A && git commit -m 'v30.77 quarantine (green run)'"
}
catch {
  Write-Host "!! $($_.Exception.Message) Rollback läuft..." -ForegroundColor Red
  foreach ($m in $moved) {
    $src=$m[0]; $dst=$m[1]
    New-Item -ItemType Directory -Force -Path (Split-Path $src) | Out-Null
    if (Test-Path $dst) { Move-Item -Force $dst $src }
  }
  if ($usesGit) { git restore --staged --worktree . 2>$null }
  if (Test-Path $qdir) { Remove-Item -Recurse -Force $qdir -ErrorAction SilentlyContinue }
  Write-Host "== Rollback fertig. Repo unverändert. ==" -ForegroundColor Green
  Pop-Location; exit 1
}
Pop-Location
