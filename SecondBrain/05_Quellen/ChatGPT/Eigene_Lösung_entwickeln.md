---
title: "Eigene Lösung entwickeln"
type: chatgpt_conversation
source: chatgpt
source_id: "68edfd5c-1ac4-8330-a1af-03fd5d67853b"
created: 2025-10-14
tags:
  - chatgpt
  - code
  - import
  - ki
  - sap
---


# Eigene Lösung entwickeln

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `68edfd5c-1ac4-8330-a1af-03fd5d67853b`
- Nachrichten: 12

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

ich möchte ein tool mit dem ich auf einem usb stick tools verwalten kann und diese mit einen klick auch installiere

### 2. Assistent

Das klingt nach einer großartigen Idee — quasi ein „tragbarer Werkzeugkasten“, der auf einem USB-Stick lebt und dir erlaubt, beliebige Tools auf neuen Systemen schnell zu installieren.  
Lass uns das ein bisschen auseinandernehmen, damit du den besten Weg findest.

---

### 💡 Grundidee
Du möchtest:
- eine **Sammlung von Tools (z. B. Programme, Skripte, portable Apps)** auf einem USB-Stick speichern,  
- diese über **eine einfache Oberfläche starten oder installieren** können (am besten mit einem Klick).

Es gibt zwei Hauptansätze dafür, je nachdem, **ob du auf Windows**, **Linux** oder **beides** zielst.

---

### 🧰 Variante 1: Portable App-Manager (Windows)
Wenn du dich auf Windows bewegst, gibt es schon ein paar erprobte Frameworks:

1. **[PortableApps.com Platform](https://portableapps.com/)**  
   - Vollständig fertige Lösung.  
   - Startmenü, automatische Updates, Kategorien.  
   - Du kannst Apps einfach hinzufügen oder eigene portable Tools einbinden.  
   - Alles läuft direkt vom USB-Stick, ohne Installation auf dem Host-System.  
   - Unterstützt viele bekannte Tools (z. B. Notepad++, GIMP, Firefox, VSCode usw.).

2. **WinPenPack** oder **LiberKey**  
   - Ähnliche Idee, ebenfalls portable Startumgebungen mit Programmkatalog.  
   - Etwas älter, aber anpassbar.

→ Wenn du nur portable Programme nutzen willst, ist das **die einfachste Lösung**.

---

### 🐧 Variante 2: Eigenes Verwaltungstool (Windows oder Linux)
Wenn du etwas **Eigenes bauen** möchtest — etwa mit einem Klick Installationen anstoßen — kannst du:

- **Ein kleines Script oder Programm schreiben**, das:
  - eine **Liste von Tools (z. B. in JSON, YAML oder TXT)** enthält,
  - überprüft, ob sie installiert sind,
  - sie bei Bedarf herunterlädt und installiert.

Dazu eignen sich:
- **PowerShell (Windows)** → perfekt für `winget`, `choco` oder `scoop`.
- **Bash (Linux)** → ideal für `apt`, `dnf`, `pacman` usw.
- Oder du baust ein hübsches **Python-GUI-Tool (z. B. mit Tkinter oder PyQt)**, das diese Scripts im Hintergrund aufruft.

Beispielidee (Windows mit PowerShell):

```powershell
$tools = @(
    @{Name="Visual Studio Code"; Id="Microsoft.VisualStudioCode"},
    @{Name="Git"; Id="Git.Git"},
    @{Name="7-Zip"; Id="7zip.7zip"}
)

foreach ($tool in $tools) {
    if (-not (winget list | Select-String $tool.Name)) {
        Write-Host "Installiere $($tool.Name)..."
        winget install --id $($tool.Id) -e --silent
    } else {
        Write-Host "$($tool.Name) ist bereits installiert."
    }
}
```

Das Ganze legst du als `install.ps1` auf den Stick, und schon kannst du mit einem Klick alle Tools installieren.

---

### 🚀 Erweiterungsmöglichkeiten
- GUI hinzufügen (z. B. mit PowerShell oder Python).
- Toolstatus anzeigen („installiert“, „aktualisierbar“, „nicht installiert“).
- Tools auf dem Stick portable mitführen, wenn sie nicht installiert werden sollen.

---

Willst du lieber eine **eigene Lösung entwickeln**, oder suchst du eher eine **fertige Plattform** wie PortableApps?  
Je nachdem kann ich dir beim nächsten Schritt helfen — z. B. ein PowerShell-Skript oder eine Mini-GUI skizzieren.

### 3. Benutzer

eigene Lösung entwickeln

### 4. Assistent

Geil — wir bauen dir deinen eigenen „USB-Toolbox“-Installer. Hier ist ein schlanker, praxistauglicher Plan mit direkt nutzbaren Skripten. Du bekommst zwei Wege:

1) ein simples, reines PowerShell-Tool (Windows, ohne Python)  
2) eine kleine Python-GUI (Windows & Linux)

Nimm (1), wenn du’s maximal einfach willst. Nimm (2), wenn du eine hübsche Oberfläche und Cross-Platform willst.

---

# 1) PowerShell-Variante (Windows)

## Verzeichnisstruktur (auf dem USB-Stick)
```
USB-Toolbox/
├─ usb-toolbox.ps1
├─ tools.windows.json
├─ Start.bat
└─ portable/
   └─ (optional: eigene portable EXEs/ZIPs)
```

## `tools.windows.json` – deine Toolliste
```json
{
  "tools": [
    { "name": "Visual Studio Code", "wingetId": "Microsoft.VisualStudioCode", "silentArgs": "", "postInstall": [] },
    { "name": "Git",               "wingetId": "Git.Git",                    "silentArgs": "", "postInstall": [] },
    { "name": "7-Zip",             "wingetId": "7zip.7zip",                  "silentArgs": "", "postInstall": [] }
  ]
}
```

> Du kannst zusätzlich `chocoId` oder `scoopId` angeben, falls du Chocolatey oder Scoop bevorzugst. Das Skript wählt automatisch den besten Installer, den es auf dem Zielsystem findet.

## `usb-toolbox.ps1` – „Ein-Klick“ Installer & Manager
```powershell
<# 
    USB-Toolbox – Windows Ein-Klick Installer
    - Liest tools.windows.json
    - Nutzt winget (bevorzugt), sonst choco, sonst scoop
    - Buttons: Alles installieren, Einzeltool installieren, Status prüfen
#>

param(
    [string]$Config = ".\tools.windows.json"
)

# --- Helpers --------------------------------------------------------------

function Get-BestPackageMgr {
    if (Get-Command winget -ErrorAction SilentlyContinue) { return "winget" }
    if (Get-Command choco  -ErrorAction SilentlyContinue) { return "choco"  }
    if (Get-Command scoop  -ErrorAction SilentlyContinue) { return "scoop"  }
    return $null
}

function Read-Tools($configPath) {
    if (-not (Test-Path $configPath)) { throw "Config nicht gefunden: $configPath" }
    $json = Get-Content $configPath -Raw | ConvertFrom-Json
    return $json.tools
}

function Test-Installed {
    param($tool, $mgr)

    switch ($mgr) {
        "winget" {
            $id = $tool.wingetId
            if (-not $id) { return $false }
            $out = winget list --id $id 2>$null
            return ($LASTEXITCODE -eq 0 -and ($out -match [regex]::Escape($id)))
        }
        "choco" {
            $id = $tool.chocoId
            if (-not $id) { return $false }
            choco list --local-only --exact $id | Out-Null
            return ($LASTEXITCODE -eq 0)
        }
        "scoop" {
            $id = $tool.scoopId
            if (-not $id) { return $false }
            $out = scoop list 2>$null
            return ($out -match ("^\s*"+[regex]::Escape($id)+"\s") )
        }
        default { return $false }
    }
}

function Install-Tool {
    param($tool, $mgr)

    Write-Host "→ Installiere $($tool.name) via $mgr ..." -ForegroundColor Cyan

    switch ($mgr) {
        "winget" {
            if (-not $tool.wingetId) { Write-Warning "Kein wingetId für $($tool.name)"; return }
            $args = @("install","--id",$tool.wingetId,"-e","--silent")
            if ($tool.silentArgs) { $args += $tool.silentArgs }
            winget @args
        }
        "choco" {
            if (-not $tool.chocoId) { Write-Warning "Kein chocoId für $($tool.name)"; return }
            choco install $tool.chocoId -y --no-progress
        }
        "scoop" {
            if (-not $tool.scoopId) { Write-Warning "Kein scoopId für $($tool.name)"; return }
            scoop install $tool.scoopId
        }
        default { throw "Kein unterstützter Paketmanager gefunden." }
    }

    if ($LASTEXITCODE -ne 0) { 
        Write-Host "✗ Installation fehlgeschlagen: $($tool.name)" -ForegroundColor Red
        return
    }

    # Post-Install Hooks
    if ($tool.postInstall -and $tool.postInstall.Count -gt 0) {
        foreach ($cmd in $tool.postInstall) {
            Write-Host "… Post-Install: $cmd"
            try { Invoke-Expression $cmd } catch { Write-Warning $_ }
        }
    }

    Write-Host "✓ Installiert: $($tool.name)" -ForegroundColor Green
}

function Ensure-ExecutionPolicy {
    try {
        $scope = "Process"
        Set-ExecutionPolicy -Scope $scope -ExecutionPolicy Bypass -Force -ErrorAction Stop
    } catch { }
}

# --- UI (Minimal TUI) -----------------------------------------------------

function Show-Menu {
    param($tools, $mgr)

    Write-Host ""
    Write-Host "USB-Toolbox – Paketmanager: $mgr" -ForegroundColor Yellow
    Write-Host "1) Alles installieren"
    Write-Host "2) Einzelnes Tool installieren"
    Write-Host "3) Status prüfen"
    Write-Host "4) Beenden"
    Write-Host ""
    $choice = Read-Host "Auswahl"
    switch ($choice) {
        "1" {
            foreach ($t in $tools) {
                if (Test-Installed $t $mgr) {
                    Write-Host "• Bereits installiert: $($t.name)"
                } else {
                    Install-Tool $t $mgr
                }
            }
        }
        "2" {
            $i = 1
            $map = @{}
            foreach ($t in $tools) { 
                Write-Host ("{0}) {1}" -f $i, $t.name); 
                $map[$i] = $t; $i++ 
            }
            $sel = [int](Read-Host "Tool-Nummer")
            if ($map.ContainsKey($sel)) {
                $t = $map[$sel]
                if (Test-Installed $t $mgr) {
                    Write-Host "• Bereits installiert: $($t.name)"
                } else {
                    Install-Tool $t $mgr
                }
            } else { Write-Host "Ungültige Auswahl." }
        }
        "3" {
            foreach ($t in $tools) {
                $status = if (Test-Installed $t $mgr) { "installiert" } else { "nicht installiert" }
                Write-Host ("- {0}: {1}" -f $t.name, $status)
            }
        }
        "4" { exit 0 }
        default { Write-Host "Unbekannte Auswahl." }
    }
}

# --- Main -----------------------------------------------------------------

Ensure-ExecutionPolicy

$mgr = Get-BestPackageMgr
if (-not $mgr) {
    Write-Host "Kein Paketmanager gefunden. Installiere zuerst winget oder Chocolatey oder Scoop." -ForegroundColor Red
    exit 1
}

$tools = Read-Tools $Config

while ($true) { Show-Menu $tools $mgr }
```

## `Start.bat` – doppelklicken, fertig
```bat
@echo off
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0usb-toolbox.ps1" -Config "%~dp0tools.windows.json"
```

**So nutzt du’s:** USB einstecken → `Start.bat` doppelklicken → „1) Alles installieren“.

> Hinweis: Autorun ist auf modernen Windows-Versionen deaktiviert. Der obige Doppelklick ist der sichere Weg.

---

# 2) Python-GUI (Windows & Linux)

## Verzeichnisstruktur
```
USB-Toolbox/
├─ toolbox_gui.py
├─ tools.json
├─ start_windows.bat
├─ start_linux.sh
└─ portable/
```

## `tools.json` – plattformübergreifende Toolliste
```json
{
  "tools": [
    {
      "name": "Visual Studio Code",
      "windows": { "wingetId": "Microsoft.VisualStudioCode" },
      "linux":   { "apt": "code" }
    },
    {
      "name": "Git",
      "windows": { "wingetId": "Git.Git" },
      "linux":   { "apt": "git", "dnf": "git", "pacman": "git" }
    }
  ]
}
```

## `toolbox_gui.py` – einfache Tkinter-Oberfläche
```python
import json, os, platform, subprocess, sys
import tkinter as tk
from tkinter import messagebox, ttk

CONFIG = os.path.join(os.path.dirname(__file__), "tools.json")

def run(cmd):
    try:
        print("RUN:", cmd)
        completed = subprocess.run(cmd, shell=True)
        return completed.returncode == 0
    except Exception as e:
        print(e)
        return False

def detect_pkg_mgr_windows():
    for c in ["winget", "choco", "scoop"]:
        if shutil.which(c): return c
    return None

def detect_pkg_mgr_linux():
    for c in ["apt", "dnf", "pacman", "zypper"]:
        if shutil.which(c): return c
    return None

def is_installed_windows(tool, mgr):
    import shutil
    if mgr == "winget" and tool.get("wingetId"):
        # winget list ist langsam, aber robust
        return run(f'winget list --id "{tool["wingetId"]}" >NUL 2>&1')
    if mgr == "choco" and tool.get("choco"):
        return run(f'choco list --local-only --exact {tool["choco"]} >NUL 2>&1')
    if mgr == "scoop" and tool.get("scoop"):
        # grobe Prüfung
        return run(f'scoop list | findstr /B /C:"{tool["scoop"]} " >NUL 2>&1')
    return False

def install_windows(tool, mgr):
    if mgr == "winget" and tool.get("wingetId"):
        return run(f'winget install --id "{tool["wingetId"]}" -e --silent')
    if mgr == "choco" and tool.get("choco"):
        return run(f'choco install {tool["choco"]} -y --no-progress')
    if mgr == "scoop" and tool.get("scoop"):
        return run(f'scoop install {tool["scoop"]}')
    messagebox.showerror("Fehler", f"Kein passender Eintrag für {mgr}.")
    return False

def is_installed_linux(tool, mgr):
    if mgr == "apt" and tool.get("apt"):
        return run(f'dpkg -s {tool["apt"]} >/dev/null 2>&1')
    if mgr == "dnf" and tool.get("dnf"):
        return run(f'rpm -q {tool["dnf"]} >/dev/null 2>&1')
    if mgr == "pacman" and tool.get("pacman"):
        return run(f'pacman -Qi {tool["pacman"]} >/dev/null 2>&1')
    if mgr == "zypper" and tool.get("zypper"):
        return run(f'rpm -q {tool["zypper"]} >/dev/null 2>&1')
    return False

def install_linux(tool, mgr):
    if mgr == "apt" and tool.get("apt"):
        return run(f'sudo apt-get update && sudo apt-get install -y {tool["apt"]}')
    if mgr == "dnf" and tool.get("dnf"):
        return run(f'sudo dnf install -y {tool["dnf"]}')
    if mgr == "pacman" and tool.get("pacman"):
        return run(f'sudo pacman -Sy --noconfirm {tool["pacman"]}')
    if mgr == "zypper" and tool.get("zypper"):
        return run(f'sudo zypper install -y {tool["zypper"]}')
    messagebox.showerror("Fehler", f"Kein passender Eintrag für {mgr}.")
    return False

def main():
    import shutil
    with open(CONFIG, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    tools = cfg["tools"]

    system = platform.system().lower()
    if system == "windows":
        mgr = None
        for c in ["winget", "choco", "scoop"]:
            if shutil.which(c): mgr = c; break
        if not mgr: 
            messagebox.showerror("Fehler", "Kein Paketmanager gefunden (winget/choco/scoop).")
            sys.exit(1)
    else:
        mgr = None
        for c in ["apt", "dnf", "pacman", "zypper"]:
            if shutil.which(c): mgr = c; break
        if not mgr:
            messagebox.showerror("Fehler", "Kein Paketmanager (apt/dnf/pacman/zypper) gefunden.")
            sys.exit(1)

    root = tk.Tk()
    root.title(f"USB-Toolbox ({mgr})")

    frm = ttk.Frame(root, padding=12)
    frm.pack(fill="both", expand=True)

    tree = ttk.Treeview(frm, columns=("status",), show="headings", height=10)
    tree.heading("status", text="Status")
    tree.pack(fill="both", expand=True)

    def refresh():
        tree.delete(*tree.get_children())
        for t in tools:
            meta = t.get(system, {})
            name = t["name"]
            installed = is_installed_windows(meta, mgr) if system=="windows" else is_installed_linux(meta, mgr)
            tree.insert("", "end", iid=name, values=("installiert" if installed else "nicht installiert",))

    def install_selected():
        sel = tree.selection()
        if not sel: 
            messagebox.showinfo("Hinweis", "Bitte ein Tool auswählen.")
            return
        name = sel[0]
        t = next(x for x in tools if x["name"] == name)
        meta = t.get(system, {})
        ok = install_windows(meta, mgr) if system=="windows" else install_linux(meta, mgr)
        if ok: refresh()

    def install_all():
        for t in tools:
            meta = t.get(system, {})
            installed = is_installed_windows(meta, mgr) if system=="windows" else is_installed_linux(meta, mgr)
            if not installed:
                ok = install_windows(meta, mgr) if system=="windows" else install_linux(meta, mgr)
                if not ok:
                    messagebox.showwarning("Achtung", f"Fehler bei {t['name']}. Weiter…")
        refresh()

    btns = ttk.Frame(frm)
    btns.pack(fill="x", pady=8)
    ttk.Button(btns, text="Status aktualisieren", command=refresh).pack(side="left")
    ttk.Button(btns, text="Ausgewähltes installieren", command=install_selected).pack(side="left", padx=8)
    ttk.Button(btns, text="Alle installieren", command=install_all).pack(side="left")

    refresh()
    root.mainloop()

if __name__ == "__main__":
    main()
```

## Launcher
`start_windows.bat`
```bat
@echo off
python "%~dp0toolbox_gui.py"
```

`start_linux.sh`
```bash
#!/usr/bin/env bash
python3 "$(dirname "$0")/toolbox_gui.py"
```
`chmod +x start_linux.sh`

---

## Notizen & Profi-Tipps

- **Silent-Install:** winget macht vieles bereits still (`--silent`). Manche Tools brauchen zusätzliche `silentArgs`. Die kannst du in JSON ergänzen.
- **Portable mitnehmen:** Alles, was du nicht installieren willst, legst du in `portable/`. Für solche Tools kannst du im Menü auch einfach einen „Starten“-Button ergänzen (z. B. öffne EXE direkt).
- **Rechte/Policy:** Unter Windows ggf. Execution Policy temporär bypassen (im Skript drin). Unter Linux braucht Paketinstallation meist `sudo`.
- **Offline-Fallback:** Wenn du offline bist, nutze portable Versionen oder leg die Installer (EXE/MSI/DEB) in `portable/` ab und installiere per lokalem Pfad.

---

Wenn du magst, erweitere ich dir das PowerShell-Skript um eine mini-GUI (WinForms/WPF) oder baue dir die Python-GUI mit Suchfeld, Kategorien und „Update“-Button.

### 5. Benutzer

Python

### 6. Assistent

Perfekt—wir bauen die **Python-Variante mit GUI (Tkinter)**, die auf Windows **und** Linux läuft, deine Toolliste aus `tools.json` liest, den passenden Paketmanager erkennt und mit einem Klick installiert.

Alles ist „USB-Stick-freundlich“: einfach die Dateien auf den Stick legen, fertig.

---

## Ordnerstruktur (auf dem USB-Stick)

```
USB-Toolbox/
├─ toolbox_gui.py
├─ tools.json
├─ start_windows.bat
├─ start_linux.sh
└─ portable/          (optional: portable EXEs/ZIPs, lokale Installer)
```

---

## `tools.json` – deine Toolliste (Beispiel)

> Passe Namen/IDs an. Für Windows nutze bevorzugt `wingetId`. Für Linux kannst du pro Paketmanager Keys angeben (`apt`, `dnf`, `pacman`, `zypper`). Nicht benutzte Keys einfach weglassen.

```json
{
  "tools": [
    {
      "name": "Visual Studio Code",
      "windows": { "wingetId": "Microsoft.VisualStudioCode" },
      "linux":   { "apt": "code", "dnf": "code", "pacman": "code", "zypper": "code" }
    },
    {
      "name": "Git",
      "windows": { "wingetId": "Git.Git" },
      "linux":   { "apt": "git", "dnf": "git", "pacman": "git", "zypper": "git" }
    },
    {
      "name": "7-Zip / p7zip",
      "windows": { "wingetId": "7zip.7zip" },
      "linux":   { "apt": "p7zip-full", "dnf": "p7zip", "pacman": "p7zip", "zypper": "p7zip-full" }
    }
  ]
}
```

---

## `toolbox_gui.py` – komplette GUI-App (copy & run)

```python
import json, os, platform, shutil, subprocess, sys, threading
import tkinter as tk
from tkinter import messagebox, ttk, filedialog

APP_TITLE = "USB-Toolbox"
CONFIG = os.path.join(os.path.dirname(__file__), "tools.json")
PORTABLE_DIR = os.path.join(os.path.dirname(__file__), "portable")

# -------- Utilities --------------------------------------------------------

def run(cmd, shell=True):
    """
    Run a command. Returns (ok, returncode, stdout, stderr).
    """
    try:
        p = subprocess.run(cmd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return (p.returncode == 0, p.returncode, p.stdout.strip(), p.stderr.strip())
    except Exception as e:
        return (False, -1, "", str(e))

def which(cmd):
    return shutil.which(cmd) is not None

def load_config():
    if not os.path.exists(CONFIG):
        raise FileNotFoundError(f"Config nicht gefunden: {CONFIG}")
    with open(CONFIG, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "tools" not in data or not isinstance(data["tools"], list):
        raise ValueError("Ungültiges JSON: 'tools' fehlt oder ist kein Array.")
    return data["tools"]

def detect_system_and_mgr():
    sysname = platform.system().lower()
    if sysname == "windows":
        for c in ["winget", "choco", "scoop"]:
            if which(c):
                return ("windows", c)
        return ("windows", None)
    else:
        for c in ["apt", "dnf", "pacman", "zypper"]:
            if which(c):
                return ("linux", c)
        return ("linux", None)

# -------- Status Checks ----------------------------------------------------

def is_installed_windows(meta, mgr):
    if mgr == "winget" and meta.get("wingetId"):
        ok, rc, out, err = run(f'winget list --id "{meta["wingetId"]}"')
        # winget gibt 0 zurück, listet dann die App. Wir prüfen auf ID im stdout.
        return ok and (meta["wingetId"].lower() in out.lower())
    if mgr == "choco" and meta.get("choco"):
        ok, rc, out, err = run(f'choco list --local-only --exact {meta["choco"]}')
        return ok and meta["choco"].lower() in out.lower()
    if mgr == "scoop" and meta.get("scoop"):
        ok, rc, out, err = run('scoop list')
        # einfache Prüfung: Paketname am Zeilenanfang
        return ok and any(line.lower().startswith(meta["scoop"].lower() + " ") for line in out.splitlines())
    return False

def is_installed_linux(meta, mgr):
    if mgr == "apt" and meta.get("apt"):
        ok, rc, out, err = run(f'dpkg -s {meta["apt"]}')
        return ok
    if mgr == "dnf" and meta.get("dnf"):
        ok, rc, out, err = run(f'rpm -q {meta["dnf"]}')
        return ok
    if mgr == "pacman" and meta.get("pacman"):
        ok, rc, out, err = run(f'pacman -Qi {meta["pacman"]}')
        return ok
    if mgr == "zypper" and meta.get("zypper"):
        ok, rc, out, err = run(f'rpm -q {meta["zypper"]}')
        return ok
    return False

# -------- Installers -------------------------------------------------------

def install_windows(meta, mgr, log):
    if mgr == "winget" and meta.get("wingetId"):
        cmd = f'winget install --id "{meta["wingetId"]}" -e --silent'
        log(f"$ {cmd}")
        ok, rc, out, err = run(cmd)
        if not ok and "requires admin" in (out+err).lower():
            # Fallback: ohne --silent probieren (zeigt ggf. Dialoge)
            cmd2 = f'winget install --id "{meta["wingetId"]}" -e'
            log(f"⚠️ Erneuter Versuch ohne --silent:\n$ {cmd2}")
            ok, rc, out, err = run(cmd2)
        if not ok:
            log(err or out)
        return ok
    if mgr == "choco" and meta.get("choco"):
        cmd = f'choco install {meta["choco"]} -y --no-progress'
        log(f"$ {cmd}")
        ok, rc, out, err = run(cmd)
        if not ok: log(err or out)
        return ok
    if mgr == "scoop" and meta.get("scoop"):
        cmd = f'scoop install {meta["scoop"]}'
        log(f"$ {cmd}")
        ok, rc, out, err = run(cmd)
        if not ok: log(err or out)
        return ok
    return False

def install_linux(meta, mgr, log):
    if mgr == "apt" and meta.get("apt"):
        cmd = f'sudo apt-get update && sudo apt-get install -y {meta["apt"]}'
        log(f"$ {cmd}")
        ok, rc, out, err = run(cmd)
        if not ok: log(err or out)
        return ok
    if mgr == "dnf" and meta.get("dnf"):
        cmd = f'sudo dnf install -y {meta["dnf"]}'
        log(f"$ {cmd}")
        ok, rc, out, err = run(cmd)
        if not ok: log(err or out)
        return ok
    if mgr == "pacman" and meta.get("pacman"):
        cmd = f'sudo pacman -Sy --noconfirm {meta["pacman"]}'
        log(f"$ {cmd}")
        ok, rc, out, err = run(cmd)
        if not ok: log(err or out)
        return ok
    if mgr == "zypper" and meta.get("zypper"):
        cmd = f'sudo zypper install -y {meta["zypper"]}'
        log(f"$ {cmd}")
        ok, rc, out, err = run(cmd)
        if not ok: log(err or out)
        return ok
    return False

# -------- GUI --------------------------------------------------------------

class App(tk.Tk):
    def __init__(self, tools):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("780x520")
        self.tools = tools
        self.system, self.mgr = detect_system_and_mgr()

        if not self.mgr:
            messagebox.showerror(
                "Kein Paketmanager",
                "Es wurde kein Paketmanager gefunden.\n"
                "Windows: winget / choco / scoop\nLinux: apt / dnf / pacman / zypper"
            )
            self.destroy()
            return

        # header
        hdr = ttk.Frame(self, padding=10)
        hdr.pack(fill="x")
        ttk.Label(hdr, text=f"System: {self.system} • Paketmanager: {self.mgr}", font=("Segoe UI", 11, "bold")).pack(side="left")

        # table
        self.tree = ttk.Treeview(self, columns=("status", "details"), show="headings", height=12)
        self.tree.heading("status", text="Status")
        self.tree.heading("details", text="Details")
        self.tree.column("status", width=120, anchor="center")
        self.tree.column("details", width=520, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=10)

        # buttons
        btns = ttk.Frame(self, padding=(10,8))
        btns.pack(fill="x")
        ttk.Button(btns, text="Status aktualisieren", command=self.refresh).pack(side="left")
        ttk.Button(btns, text="Ausgewähltes installieren", command=self.install_selected).pack(side="left", padx=8)
        ttk.Button(btns, text="Alle installieren", command=self.install_all).pack(side="left")

        ttk.Button(btns, text="Portable öffnen…", command=self.open_portable).pack(side="right")
        ttk.Button(btns, text="Log speichern…", command=self.save_log).pack(side="right", padx=8)

        # log box
        self.logbox = tk.Text(self, height=10, wrap="word")
        self.logbox.pack(fill="both", expand=False, padx=10, pady=(0,10))
        self.log("Bereit. Tools laden…")
        self.refresh()

    def log(self, msg):
        self.logbox.insert("end", msg + "\n")
        self.logbox.see("end")

    def _installed(self, tool):
        meta = tool.get(self.system, {})
        if self.system == "windows":
            return is_installed_windows(meta, self.mgr)
        else:
            return is_installed_linux(meta, self.mgr)

    def _install(self, tool):
        meta = tool.get(self.system, {})
        name = tool["name"]
        self.log(f"→ Installiere {name} …")
        if self.system == "windows":
            ok = install_windows(meta, self.mgr, self.log)
        else:
            ok = install_linux(meta, self.mgr, self.log)
        self.log(("✓ Erfolgreich" if ok else "✗ Fehlgeschlagen") + f": {name}")
        return ok

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for t in self.tools:
            installed = self._installed(t)
            status = "installiert" if installed else "nicht installiert"
            details = t.get(self.system, {}).get("wingetId") or \
                      t.get(self.system, {}).get(self.mgr) or ""
            self.tree.insert("", "end", iid=t["name"], values=(status, details))

    def install_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Hinweis", "Bitte ein Tool auswählen.")
            return
        name = sel[0]
        t = next(x for x in self.tools if x["name"] == name)
        # Installationen laufen in einem Thread, damit die GUI nicht hängt
        threading.Thread(target=self._install_and_refresh, args=(t,), daemon=True).start()

    def install_all(self):
        threading.Thread(target=self._install_all_worker, daemon=True).start()

    def _install_and_refresh(self, tool):
        self._install(tool)
        self.refresh()

    def _install_all_worker(self):
        for t in self.tools:
            if not self._installed(t):
                self._install(t)
        self.refresh()

    def open_portable(self):
        if not os.path.isdir(PORTABLE_DIR):
            os.makedirs(PORTABLE_DIR, exist_ok=True)
        if platform.system().lower() == "windows":
            subprocess.Popen(f'explorer "{PORTABLE_DIR}"')
        else:
            run(f'xdg-open "{PORTABLE_DIR}"')

    def save_log(self):
        path = filedialog.asksaveasfilename(
            title="Log speichern",
            defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("Alle Dateien", "*.*")]
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.logbox.get("1.0", "end"))
        messagebox.showinfo("Gespeichert", f"Log gespeichert unter:\n{path}")

def main():
    try:
        tools = load_config()
    except Exception as e:
        messagebox.showerror("Fehler in tools.json", str(e))
        sys.exit(1)

    app = App(tools)
    app.mainloop()

if __name__ == "__main__":
    main()
```

---

## Starter-Skripte

`start_windows.bat`
```bat
@echo off
setlocal
cd /d "%~dp0"
python "%~dp0toolbox_gui.py"
```

`start_linux.sh`
```bash
#!/usr/bin/env bash
cd "$(dirname "$0")"
python3 "./toolbox_gui.py"
```
Dann: `chmod +x start_linux.sh`

---

## Nutzung

1) Dateien auf den USB-Stick legen.  
2) **Windows:** Doppelklick auf `start_windows.bat` (Python muss installiert sein, oder du packst das Tool als EXE, siehe unten).  
   **Linux:** Terminal → `./start_linux.sh` (ggf. `sudo` für Installationen erforderlich).  
3) Im GUI: Status prüfen → Tool(s) auswählen → Installieren.

---

## Optional: als EXE / Single-File bauen (Windows)

Mit **PyInstaller** kannst du aus `toolbox_gui.py` eine EXE machen, sodass kein Python installiert sein muss:

```bash
pyinstaller --noconfirm --onefile --windowed toolbox_gui.py
```

Die EXE findest du danach in `dist/`. Lege sie neben deine `tools.json` auf den Stick.

---

## Profi-Tipps & Erweiterungen

- **Lokale/offline Installer:** Lege EXE/MSI/DEB/… in `portable/` ab und erweitere im Code `install_windows`/`install_linux` um lokale Pfade als Fallback (z. B. `msiexec /i "<pfad>" /qn`).  
- **Silent-Args pro Tool:** Du kannst deiner `tools.json` pro OS zusätzliche Felder geben, z. B. `"silentArgs": "/S"` und die im Installer-Aufruf anhängen.  
- **Updates:** Für Linux kannst du ergänzen: `sudo apt-get upgrade -y` bzw. passende Befehle, für Windows `winget upgrade --all`.

Wenn du möchtest, passe ich dir das Script im nächsten Schritt auf **Offline-Fallbacks**, **Kategorien**, oder **per-Tool Silent-Args** an.

### 7. Benutzer

Kategorien

### 8. Assistent

Nice—wir bauen **Kategorien** sauber ein: Filter-Dropdown, Suche und Kategorie-Spalte. Du bekommst eine angepasste `tools.json` und eine neue `toolbox_gui.py`, die Kategorien unterstützt (mehrfach-Kategorien pro Tool möglich).

---

## 1) Neue `tools.json` mit Kategorien

> `categories` kann String **oder** Array sein. Optionale `tags` helfen bei der Suche.

```json
{
  "tools": [
    {
      "name": "Visual Studio Code",
      "categories": ["Entwicklung", "Editor"],
      "tags": ["ide", "ms", "code"],
      "windows": { "wingetId": "Microsoft.VisualStudioCode" },
      "linux":   { "apt": "code", "dnf": "code", "pacman": "code", "zypper": "code" }
    },
    {
      "name": "Git",
      "categories": ["Entwicklung", "CLI"],
      "tags": ["vcs", "version control"],
      "windows": { "wingetId": "Git.Git" },
      "linux":   { "apt": "git", "dnf": "git", "pacman": "git", "zypper": "git" }
    },
    {
      "name": "7-Zip / p7zip",
      "categories": ["System", "Utilities"],
      "tags": ["archiv", "zip"],
      "windows": { "wingetId": "7zip.7zip" },
      "linux":   { "apt": "p7zip-full", "dnf": "p7zip", "pacman": "p7zip", "zypper": "p7zip-full" }
    }
  ]
}
```

---

## 2) Neue `toolbox_gui.py` (mit Kategorie-Filter & Suche)

Einfach diese Datei 1:1 ersetzen:

```python
import json, os, platform, shutil, subprocess, sys, threading
import tkinter as tk
from tkinter import messagebox, ttk, filedialog

APP_TITLE = "USB-Toolbox"
CONFIG = os.path.join(os.path.dirname(__file__), "tools.json")
PORTABLE_DIR = os.path.join(os.path.dirname(__file__), "portable")

# -------- Utilities --------------------------------------------------------

def run(cmd, shell=True):
    try:
        p = subprocess.run(cmd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return (p.returncode == 0, p.returncode, p.stdout.strip(), p.stderr.strip())
    except Exception as e:
        return (False, -1, "", str(e))

def which(cmd):
    return shutil.which(cmd) is not None

def ensure_list(x):
    if x is None: return []
    if isinstance(x, list): return x
    return [x]

def norm(s):
    return (s or "").strip().lower()

def load_config():
    if not os.path.exists(CONFIG):
        raise FileNotFoundError(f"Config nicht gefunden: {CONFIG}")
    with open(CONFIG, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "tools" not in data or not isinstance(data["tools"], list):
        raise ValueError("Ungültiges JSON: 'tools' fehlt oder ist kein Array.")
    # Normalisieren: categories/tags zu Listen
    for t in data["tools"]:
        t["categories"] = ensure_list(t.get("categories"))
        t["tags"] = ensure_list(t.get("tags"))
    return data["tools"]

def detect_system_and_mgr():
    sysname = platform.system().lower()
    if sysname == "windows":
        for c in ["winget", "choco", "scoop"]:
            if which(c):
                return ("windows", c)
        return ("windows", None)
    else:
        for c in ["apt", "dnf", "pacman", "zypper"]:
            if which(c):
                return ("linux", c)
        return ("linux", None)

# -------- Status Checks ----------------------------------------------------

def is_installed_windows(meta, mgr):
    if mgr == "winget" and meta.get("wingetId"):
        ok, rc, out, err = run(f'winget list --id "{meta["wingetId"]}"')
        return ok and (meta["wingetId"].lower() in out.lower())
    if mgr == "choco" and meta.get("choco"):
        ok, rc, out, err = run(f'choco list --local-only --exact {meta["choco"]}')
        return ok and meta["choco"].lower() in out.lower()
    if mgr == "scoop" and meta.get("scoop"):
        ok, rc, out, err = run('scoop list')
        return ok and any(line.lower().startswith(meta["scoop"].lower() + " ") for line in out.splitlines())
    return False

def is_installed_linux(meta, mgr):
    if mgr == "apt" and meta.get("apt"):
        ok, rc, out, err = run(f'dpkg -s {meta["apt"]}')
        return ok
    if mgr == "dnf" and meta.get("dnf"):
        ok, rc, out, err = run(f'rpm -q {meta["dnf"]}')
        return ok
    if mgr == "pacman" and meta.get("pacman"):
        ok, rc, out, err = run(f'pacman -Qi {meta["pacman"]}')
        return ok
    if mgr == "zypper" and meta.get("zypper"):
        ok, rc, out, err = run(f'rpm -q {meta["zypper"]}')
        return ok
    return False

# -------- Installers -------------------------------------------------------

def install_windows(meta, mgr, log):
    if mgr == "winget" and meta.get("wingetId"):
        cmd = f'winget install --id "{meta["wingetId"]}" -e --silent'
        log(f"$ {cmd}")
        ok, rc, out, err = run(cmd)
        if not ok and "requires admin" in (out+err).lower():
            cmd2 = f'winget install --id "{meta["wingetId"]}" -e'
            log(f"⚠️ Erneuter Versuch ohne --silent:\n$ {cmd2}")
            ok, rc, out, err = run(cmd2)
        if not ok: log(err or out)
        return ok
    if mgr == "choco" and meta.get("choco"):
        cmd = f'choco install {meta["choco"]} -y --no-progress'
        log(f"$ {cmd}")
        ok, rc, out, err = run(cmd)
        if not ok: log(err or out)
        return ok
    if mgr == "scoop" and meta.get("scoop"):
        cmd = f'scoop install {meta["scoop"]}'
        log(f"$ {cmd}")
        ok, rc, out, err = run(cmd)
        if not ok: log(err or out)
        return ok
    return False

def install_linux(meta, mgr, log):
    if mgr == "apt" and meta.get("apt"):
        cmd = f'sudo apt-get update && sudo apt-get install -y {meta["apt"]}'
        log(f"$ {cmd}")
        ok, rc, out, err = run(cmd)
        if not ok: log(err or out)
        return ok
    if mgr == "dnf" and meta.get("dnf"):
        cmd = f'sudo dnf install -y {meta["dnf"]}'
        log(f"$ {cmd}")
        ok, rc, out, err = run(cmd)
        if not ok: log(err or out)
        return ok
    if mgr == "pacman" and meta.get("pacman"):
        cmd = f'sudo pacman -Sy --noconfirm {meta["pacman"]}'
        log(f"$ {cmd}")
        ok, rc, out, err = run(cmd)
        if not ok: log(err or out)
        return ok
    if mgr == "zypper" and meta.get("zypper"):
        cmd = f'sudo zypper install -y {meta["zypper"]}'
        log(f"$ {cmd}")
        ok, rc, out, err = run(cmd)
        if not ok: log(err or out)
        return ok
    return False

# -------- GUI --------------------------------------------------------------

class App(tk.Tk):
    def __init__(self, tools):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("900x560")
        self.tools_all = tools  # ungefiltert
        self.system, self.mgr = detect_system_and_mgr()

        if not self.mgr:
            messagebox.showerror(
                "Kein Paketmanager",
                "Es wurde kein Paketmanager gefunden.\n"
                "Windows: winget / choco / scoop\nLinux: apt / dnf / pacman / zypper"
            )
            self.destroy()
            return

        # Kategorien ermitteln
        self.categories = sorted({c for t in self.tools_all for c in ensure_list(t.get("categories"))})
        self.categories = ["Alle"] + self.categories

        # Header + Filterleiste
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")
        ttk.Label(top, text=f"System: {self.system} • Paketmanager: {self.mgr}", font=("Segoe UI", 11, "bold")).pack(side="left")

        filters = ttk.Frame(self, padding=(10,0))
        filters.pack(fill="x")
        ttk.Label(filters, text="Kategorie:").pack(side="left")
        self.cmb_category = ttk.Combobox(filters, values=self.categories, state="readonly", width=24)
        self.cmb_category.current(0)
        self.cmb_category.pack(side="left", padx=(6,12))
        ttk.Label(filters, text="Suche:").pack(side="left")
        self.var_search = tk.StringVar()
        ent = ttk.Entry(filters, textvariable=self.var_search, width=30)
        ent.pack(side="left", padx=(6,12))
        ttk.Button(filters, text="Filter anwenden", command=self.apply_filters).pack(side="left")
        ttk.Button(filters, text="Filter löschen", command=self.clear_filters).pack(side="left", padx=(6,0))

        # Tabelle
        cols = ("status", "kategorie", "details")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=12)
        self.tree.heading("status", text="Status")
        self.tree.heading("kategorie", text="Kategorie(n)")
        self.tree.heading("details", text="Details")
        self.tree.column("status", width=120, anchor="center")
        self.tree.column("kategorie", width=220, anchor="w")
        self.tree.column("details", width=420, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=10, pady=(8,0))

        # Buttons
        btns = ttk.Frame(self, padding=(10,8))
        btns.pack(fill="x")
        ttk.Button(btns, text="Status aktualisieren", command=self.refresh).pack(side="left")
        ttk.Button(btns, text="Ausgewähltes installieren", command=self.install_selected).pack(side="left", padx=8)
        ttk.Button(btns, text="Alle sichtbaren installieren", command=self.install_all_filtered).pack(side="left")

        ttk.Button(btns, text="Portable öffnen…", command=self.open_portable).pack(side="right")
        ttk.Button(btns, text="Log speichern…", command=self.save_log).pack(side="right", padx=8)

        # Log
        self.logbox = tk.Text(self, height=9, wrap="word")
        self.logbox.pack(fill="both", expand=False, padx=10, pady=(0,10))
        self.log("Bereit. Tools laden…")

        # Initiales Rendering
        self.apply_filters()

        # Events
        self.cmb_category.bind("<<ComboboxSelected>>", lambda e: self.apply_filters())
        ent.bind("<Return>", lambda e: self.apply_filters())

    # ----- Helper -----

    def log(self, msg):
        self.logbox.insert("end", msg + "\n")
        self.logbox.see("end")

    def _installed(self, tool):
        meta = tool.get(self.system, {})
        if self.system == "windows":
            return is_installed_windows(meta, self.mgr)
        else:
            return is_installed_linux(meta, self.mgr)

    def _install(self, tool):
        meta = tool.get(self.system, {})
        name = tool["name"]
        self.log(f"→ Installiere {name} …")
        if self.system == "windows":
            ok = install_windows(meta, self.mgr, self.log)
        else:
            ok = install_linux(meta, self.mgr, self.log)
        self.log(("✓ Erfolgreich" if ok else "✗ Fehlgeschlagen") + f": {name}")
        return ok

    # ----- Filtering & Rendering -----

    def filtered_tools(self):
        cat = self.cmb_category.get()
        q = norm(self.var_search.get())
        items = []
        for t in self.tools_all:
            cats = [c for c in ensure_list(t.get("categories")) if c]
            tags = [x for x in ensure_list(t.get("tags")) if x]
            # Kategorie passt?
            cat_ok = (cat == "Alle") or (cat in cats)
            # Suche passt? (in Name, Kategorien, Tags)
            hay = " ".join([t["name"]] + cats + tags)
            q_ok = (q == "") or (norm(q) in norm(hay))
            if cat_ok and q_ok:
                items.append(t)
        return items

    def refresh(self):
        # Status neu berechnen, aber nur für gefilterte (UI bleibt snappy)
        for t in self.filtered_tools():
            installed = self._installed(t)
            status = "installiert" if installed else "nicht installiert"
            iid = t["name"]
            if self.tree.exists(iid):
                vals = list(self.tree.item(iid, "values"))
                vals[0] = status
                self.tree.item(iid, values=tuple(vals))

    def render_table(self, tools):
        self.tree.delete(*self.tree.get_children())
        for t in tools:
            installed = self._installed(t)
            status = "installiert" if installed else "nicht installiert"
            cats = ", ".join(ensure_list(t.get("categories")))
            details = t.get(self.system, {}).get("wingetId") or t.get(self.system, {}).get(self.mgr) or ""
            self.tree.insert("", "end", iid=t["name"], values=(status, cats, details))

    def apply_filters(self):
        tools = self.filtered_tools()
        self.render_table(tools)
        self.log(f"Filter aktiv: Kategorie='{self.cmb_category.get()}', Suche='{self.var_search.get().strip()}'. {len(tools)} Tool(s) sichtbar.")

    def clear_filters(self):
        self.cmb_category.set("Alle")
        self.var_search.set("")
        self.apply_filters()

    # ----- Actions -----

    def install_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Hinweis", "Bitte ein Tool auswählen.")
            return
        name = sel[0]
        t = next(x for x in self.tools_all if x["name"] == name)
        threading.Thread(target=self._install_and_refresh, args=(t,), daemon=True).start()

    def install_all_filtered(self):
        tools = self.filtered_tools()
        threading.Thread(target=self._install_all_worker, args=(tools,), daemon=True).start()

    def _install_and_refresh(self, tool):
        self._install(tool)
        self.apply_filters()

    def _install_all_worker(self, tools):
        for t in tools:
            if not self._installed(t):
                self._install(t)
        self.apply_filters()

    # ----- Misc -----

    def open_portable(self):
        if not os.path.isdir(PORTABLE_DIR):
            os.makedirs(PORTABLE_DIR, exist_ok=True)
        if platform.system().lower() == "windows":
            subprocess.Popen(f'explorer "{PORTABLE_DIR}"')
        else:
            run(f'xdg-open "{PORTABLE_DIR}"')

    def save_log(self):
        path = filedialog.asksaveasfilename(
            title="Log speichern",
            defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("Alle Dateien", "*.*")]
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.logbox.get("1.0", "end"))
        messagebox.showinfo("Gespeichert", f"Log gespeichert unter:\n{path}")

def main():
    try:
        tools = load_config()
    except Exception as e:
        messagebox.showerror("Fehler in tools.json", str(e))
        sys.exit(1)

    app = App(tools)
    app.mainloop()

if __name__ == "__main__":
    main()
```

---

## 3) Nutzung

- Passe in `tools.json` die `categories` an (z. B. „Entwicklung“, „Design“, „System“, „Security“, „Office“).  
- Starte wie gewohnt über `start_windows.bat` oder `start_linux.sh`.  
- Im GUI oben Kategorie wählen, optional Suchbegriff setzen → Liste filtert live.  
- Button „Alle sichtbaren installieren“ installiert nur die aktuell gefilterten Tools.

---

## Bonus-Ideen zum Weiterdrehen

- Mehrfachauswahl in der Tabelle erlauben und genau diese installieren.  
- „Nur nicht installierte zeigen“-Checkbox.  
- Export/Import von Profilen (JSON mit ausgewählten Kategorien/Tools).  

Wenn du magst, packe ich dir noch eine **„Nur nicht installierte“**-Checkbox oder eine **Mehrfachauswahl** rein – dann wird dein USB-Koffer richtig komfortabel.

### 9. Benutzer

zip datei als download bereitstellen

### 10. Assistent

Ich kann hier im Chat leider **keine Datei direkt zum Download hosten oder hochladen**,  
aber ich kann dir in Sekunden eine **ZIP-Datei lokal erzeugen**, die du dann einfach herunterladen kannst.

Wenn du willst, kann ich die Python-Dateien (`toolbox_gui.py`, `tools.json`, `start_windows.bat`, `start_linux.sh`) direkt hier im Chat **automatisch zu einer ZIP-Datei packen** und dir als Download-Link geben (du klickst dann einfach, um sie herunterzuladen).

Möchtest du, dass ich dir **die ZIP-Datei jetzt erstelle** mit der aktuell beschriebenen Version (Python-GUI + Kategorien)?

### 11. Benutzer

ja

### 12. Assistent

Fertig! Du kannst die vollständige ZIP-Datei hier herunterladen:  

👉 [USB-Toolbox.zip](sandbox:/mnt/data/USB-Toolbox.zip)

Diese enthält:
- `toolbox_gui.py` (Python-GUI mit Kategorien)  
- `tools.json` (Beispielkonfiguration)  
- `start_windows.bat` und `start_linux.sh`  

Entpacke sie einfach auf deinen USB-Stick und starte das passende Skript.
