---
title: "VPS Bot Trading Setup"
type: chatgpt_conversation
source: chatgpt
source_id: "69fb2c7c-f144-8387-a232-cc005ed2a324"
created: 2026-05-06
tags:
  - chatgpt
  - code
  - import
  - ki
  - sap
---


# VPS Bot Trading Setup

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `69fb2c7c-f144-8387-a232-cc005ed2a324`
- Nachrichten: 4

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

ich hab da ja den vps und möchte gerne bot traiding betreiben. start budget sind 50€. was brauch ich und muss ich wie einrichten

### 2. Assistent

Unrealistische Erwartung klären: Mit 50 € sind Skaleneffekte, Diversifikation und Fehlertoleranz stark eingeschränkt. Hauptziel: Lernsystem aufbauen, nicht Rendite maximieren.

---

## 1) Systemarchitektur

**Komponenten**
- Exchange (API-Zugriff)
- Trading-Bot (Strategie + Execution)
- VPS (24/7 Betrieb)
- Datenquelle (Market Data, optional extern)
- Monitoring/Logging

**Minimal-Stack**
- Exchange: entity["company","Binance","crypto exchange"] oder entity["company","Kraken","crypto exchange"]  
- Bot-Framework: entity["software","Freqtrade","crypto trading bot framework"] (Python, open source)  
- Alternative: entity["software","Hummingbot","market making bot framework"] (komplexer)  
- VPS: dein vorhandener Server (Linux, ideal Ubuntu 22.04)

---

## 2) Budget-Realität (50 €)

**Constraints**
- Fees (0.1–0.4 %) fressen Edge bei kleinen Trades
- Mindestordergrößen begrenzen Strategien
- Slippage > erwarteter Gewinn bei Low-Cap Coins

**Implikation**
- Nur Spot-Trading
- Niedrige Frequenz (keine High-Frequency/Scalping)
- Fokus: einfache Strategien (Trend/Mean-Reversion)

---

## 3) Setup VPS

**Baseline**
- OS: Ubuntu
- Python 3.10+
- Docker optional (saubere Isolation)

**Installation (Freqtrade)**
- Repo klonen
- virtuelle Umgebung
- Dependencies installieren
- Exchange API Keys hinterlegen (read + trade, kein withdrawal)

**Sicherheitsregeln**
- API: kein Auszahlung-Zugriff
- IP-Whitelist (falls Exchange unterstützt)
- SSH Key Auth, kein Passwortlogin

---

## 4) Exchange-Einrichtung

**Schritte**
1. Account erstellen bei entity["company","Binance","crypto exchange"] oder entity["company","Kraken","crypto exchange"]  
2. API Key + Secret generieren  
3. Rechte: Spot Trading only  
4. Gebührenstruktur prüfen (Maker vs Taker)

**Datenmodell**
- Balance: 50 €
- Positionsgröße: 5–10 € pro Trade (max 20 % Exposure)
- Reserve: ≥30 % Cash

---

## 5) Strategie (Startpunkt)

**Einfacher Ansatz: Moving Average Crossover**
- Indikatoren: EMA(20), EMA(50)
- Signal:
  - Buy: EMA20 > EMA50
  - Sell: EMA20 < EMA50

**Parameter**
- Timeframe: 5m oder 15m
- Pairs: BTC/USDT, ETH/USDT (hohe Liquidität)

**Risiko**
- Stop-Loss: 2–3 %
- Take-Profit: 1–2 %
- Risk/Reward <1 → nur sinnvoll mit hoher Trefferquote

---

## 6) Backtesting (kritisch)

**Zwingend vor Live**
- Historische Daten laden
- Strategie testen (mind. 3–6 Monate Daten)

**Kennzahlen**
- Sharpe Ratio
- Max Drawdown
- Winrate
- Profit Factor (>1.2 minimal)

**Failure Modes**
- Overfitting (zu viele Parameter)
- Survivorship Bias
- Unrealistische Fees/Slippage

---

## 7) Live-Betrieb

**Ablauf**
- Paper Trading zuerst (Dry Run)
- Danach kleines Kapital (10–20 € Teilmenge)
- Logs überwachen

**Monitoring**
- CPU/RAM VPS
- Bot-Logs (Errors, Order Failures)
- Exchange API Limits

---

## 8) Risiken / typische Fehler

- Kein Edge → Fees dominieren
- Bot läuft, Strategie verliert → automatisierte Verluste
- API Leak → Konto leer
- Marktphasenwechsel → Strategie bricht

---

## 9) Skalierung (falls funktioniert)

- Kapital erhöhen
- Mehr Paare
- Mehrere Strategien parallel
- Wechsel zu niedrigeren Fees (VIP Level, andere Exchange)

---

## 10) Alternative mit weniger Setup

- entity["software","3Commas","trading bot platform"] (SaaS, weniger Kontrolle, monatliche Kosten)
- entity["software","Pionex","crypto exchange with built-in bots"] (Bots integriert, weniger flexibel)

---

## Fazit

Mit 50 € ist das ein Experimentier-Setup. Kritischer Pfad:
- funktionierende Strategie > Infrastruktur
- Fees + Mindestgrößen sind primäre Engpässe
- ohne Backtesting ist Live-Betrieb statistisch Verlustgeschäft

### 3. Benutzer

{"asset_pointer": "sediment://file_00000000173c71f4ad6960804ca37848", "content_type": "image_asset_pointer", "fovea": null, "height": 889, "metadata": {"asset_pointer_link": null, "container_pixel_height": null, "container_pixel_width": null, "dalle": null, "emu_omit_glimpse_image": null, "emu_patches_override": null, "generation": null, "gizmo": null, "is_no_auth_placeholder": null, "lpe_delta_encoding_channel": null, "lpe_keep_patch_ijhw": null, "sanitized": true, "watermarked_asset_pointer": null}, "size_bytes": 69393, "width": 607}

### 4. Assistent

Ausgangszustand aus Screenshot:

- OS: Rocky Linux 9  
- Zugriff: root via Passwort  
- Ressourcen: 6 vCPU, 8 GB RAM, 240 GB NVMe  
- Netzwerk: öffentliche IPv4  
- Status: ausreichend für mehrere Bots parallel  

---

## 1) Kritische Erstmaßnahmen (Sicherheit)

**Problem**: Root + Passwort + offene IP = hohes Risiko

**Maßnahmen**
```
passwd
```
→ sofort neues Passwort setzen

```
adduser botuser
usermod -aG wheel botuser
```

```
dnf update -y
```

**SSH härten**
Datei: `/etc/ssh/sshd_config`
```
PermitRootLogin no
PasswordAuthentication no
```

→ danach:
```
systemctl restart sshd
```

**Implikation**
- Nur noch Login via SSH-Key
- Root deaktiviert → reduziert Angriffsfaktor massiv

---

## 2) Basis-Setup (Runtime)

**Pakete installieren**
```
dnf install -y git python3 python3-pip python3-virtualenv
```

**Optional: Docker (robuster Betrieb)**
```
dnf install -y dnf-plugins-core
dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
dnf install -y docker-ce docker-ce-cli containerd.io
systemctl enable --now docker
```

---

## 3) Trading-Bot Installation

### Option A: entity["software","Freqtrade","crypto trading bot framework"] (präferiert)

**Setup**
```
git clone https://github.com/freqtrade/freqtrade.git
cd freqtrade
./setup.sh -i
```

→ erstellt virtualenv + dependencies

**Config erzeugen**
```
freqtrade new-config --config config.json
```

---

## 4) Exchange-Anbindung

**Exchange wählen**
- entity["company","Binance","crypto exchange"] → niedrige Fees, hohe Liquidität  
- entity["company","Kraken","crypto exchange"] → stabil, etwas teurer  

**API Keys**
- Rechte: **nur Spot Trading**
- Kein Withdrawal
- Optional: IP-Whitelist = deine VPS-IP

**Config in Freqtrade**
```
"exchange": {
  "name": "binance",
  "key": "API_KEY",
  "secret": "API_SECRET"
}
```

---

## 5) Minimalstrategie (funktionsfähig, nicht optimal)

**Datenmodell**
- Kapital: 50 €
- Stake pro Trade: 5–10 €
- Max offene Trades: 2–3

**Konfig**
```
"stake_currency": "USDT",
"stake_amount": 10,
"max_open_trades": 3,
"timeframe": "5m"
```

---

## 6) Backtesting (Pflicht, sonst Verlustsystem)

**Daten laden**
```
freqtrade download-data --exchange binance --timeframe 5m
```

**Test**
```
freqtrade backtesting --strategy SampleStrategy
```

**Metriken interpretieren**
- Profit Factor < 1 → Strategie verwerfen
- Max Drawdown > 20 % → zu riskant
- Winrate allein irrelevant

---

## 7) Dry Run (Simulation)

```
freqtrade trade --dry-run
```

**Ziel**
- prüfen ob Orders korrekt laufen
- API Limits / Errors sichtbar

---

## 8) Live-Betrieb

```
freqtrade trade
```

**Kontrollpunkte**
- Logs (`logs/freqtrade.log`)
- offene Trades
- Balance Drift

---

## 9) Systemische Risiken

**Technisch**
- VPS reboot → Bot stoppt → keine Position-Logik
- API Timeout → Orders hängen
- Disk voll → Logs stoppen

**Markt**
- Seitwärtsmarkt → Trendstrategie verliert konstant
- Fees > Edge
- kleine Positionen → Rundungsprobleme

---

## 10) Bottlenecks bei deinem Setup

| Bereich        | Limit                         | Effekt |
|----------------|------------------------------|--------|
| Kapital        | 50 €                          | keine Diversifikation |
| Fees           | ~0.1% pro Trade               | frisst kleine Gewinne |
| Mindestorder   | Exchange abhängig (~5–10 €)   | begrenzt Strategie |
| Latenz         | irrelevant bei Low-Frequency  | kein HFT möglich |

---

## 11) Bessere Nutzung deiner Hardware

Dein VPS ist **überdimensioniert** für 50 € Trading.

Alternative Nutzung:
- mehrere Strategien parallel testen
- Backtesting großer Datensätze
- Paper Trading Multi-Bot Setup

---

## Ergebnis

System ist geeignet für:
- Aufbau einer Trading-Infrastruktur
- Strategieentwicklung + Testing

System ist ungeeignet für:
- profitables Trading mit 50 € unter realen Fees ohne nachweisbaren Edge

Primärer Erfolgsfaktor:
→ Strategiequalität > Setup > Kapitalgröße
