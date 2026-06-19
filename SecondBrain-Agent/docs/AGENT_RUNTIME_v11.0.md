# SecondBrain OS v11.0 Autonomous Agent Runtime

## Ziel

Jarvis verarbeitet Ziele über einen kontrollierten Agentenzyklus. Keine Ausführung erfolgt ohne registrierte Tools und Governance-Schicht.

## Zyklus

```text
Observe -> Plan -> Execute -> Verify -> Learn -> Persist
```

## Neue Dateien

```text
secondbrain/autonomous_agent_v110.py
runtime/agent_runs_v110.json
docs/AGENT_RUNTIME_v11.0.md
tests/test_autonomous_agent_v110.py
```

## Launcher-Kommandos

```powershell
python launcher.py agent-status
python launcher.py agent-run "Fasse mein Wissen zu Real Connectors zusammen"
python launcher.py agent-run "Synchronisiere Connectoren" --max-steps 4
```

## Tool-Modell

Der Agent ruft keine beliebigen Systembefehle auf. Er nutzt nur registrierte Aktionen:

```text
rag.search
rag.answer
ai.ask
connectors.sync
desktop.quick_capture
desktop.notify
agent.verify
```

## Sicherheitsgrenze

v11.0 ist absichtlich deterministisch. LLM-basierte Planung wird erst nach stabiler Policy Engine aktiviert.
