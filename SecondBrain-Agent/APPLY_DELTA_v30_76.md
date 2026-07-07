# APPLY DELTA v30.76

## Umfang

- Deklarativer `PluginLoader`; Discovery fuehrt keinen Plugin-Code aus.
- Versioniertes JSON-`PluginManifest` mit validierten Entry-Points, Permissions, Settings und Marketplace-Metadaten.
- Eingeschraenkte `PluginAPI` fuer Settings, Workspace-Dateien und namespaced Tools.
- `PluginPermissionPolicy` auf Basis der vorhandenen Permission-Logik.
- `PluginSandbox` als Host-API-/Pfadgrenze; Python-Aktivierung nur nach explizitem Host-Trust.
- Schema-validierte `PluginSettings`; Secrets nur als `secret://`-Referenz.
- Offline `PluginMarketplace`-Katalogvorbereitung ohne Installations-/Netzwerkfunktion.

Plugins registrieren Tools ausschliesslich in der bestehenden `ToolRegistry`. Bei Aktivierungsfehlern werden Teilregistrierungen zurueckgerollt.

## Sicherheitsgrenze

Die Sandbox begrenzt die vom Host bereitgestellte API. Aktivierter Python-Code ist kein OS-Prozess-Sandboxing und wird deshalb nur fuer explizit hostseitig vertraute Plugin-IDs ausgefuehrt.

## Pruefung

```powershell
python -m compileall .
pytest -q
```
