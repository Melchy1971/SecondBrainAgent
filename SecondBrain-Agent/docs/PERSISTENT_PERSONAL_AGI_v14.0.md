# SecondBrain OS v14.0 – Persistent Personal AGI

## Ziel
v14.0 liefert einen überwachten Personal-AGI-Kern mit Runtime, kognitivem Zyklus und kontrollierter Selbstoptimierung.

## Komponenten
- Persistent Daemon
- Governance Policy
- Observe / Think / Plan / Act / Verify / Learn Cycle
- Proactive Assistant
- Self Optimizer
- Optimization Backlog
- Persistent JSON Store

## Befehle
```powershell
python launcher.py agi-status
python launcher.py agi-start
python launcher.py agi-tick
python launcher.py agi-cycle "Prüfe meinen Tagesplan"
python launcher.py agi-briefing
python launcher.py agi-recommendations
python launcher.py agi-optimize
python launcher.py agi-optimization-backlog
python launcher.py agi-policy calendar_write --risk high
python launcher.py agi-stop
```

## Autonomiegrenzen
- Riskante Aktionen benötigen Approval.
- Blockierte Aktionen werden nicht ausgeführt.
- Keine automatische Codeänderung.
- Keine echten Systemeingriffe ohne Tool-Integration und Freigabe.
