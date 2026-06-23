# Dependency Inventory v18.8

## Ziel

`dependency-inventory` erzeugt ein statisches Import-Inventar des Repositorys.

Das Werkzeug reduziert Release-Risiko durch transparente Abhängigkeitsklassen:

- Standardbibliothek
- interne Module
- externe Runtime-Abhängigkeiten
- optionale Provider-Abhängigkeiten
- unbekannte oder fehlerhafte Imports

## Befehl

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
python launcher.py dependency-inventory
```

Mit Report-Datei:

```powershell
python launcher.py dependency-inventory --write-report
```

Zielartefakt:

```text
release/dependency_inventory_latest.json
```

## Klassifizierung

| Klasse | Bedeutung | Release-Wirkung |
|---|---|---|
| `standard_library` | Python-Standardbibliothek | keine Requirements-Pflege nötig |
| `internal` | Projektmodule, z. B. `secondbrain` | Architektur-/Importgraph relevant |
| `external` | externe Pakete | Kandidaten für `requirements-runtime.txt` |
| `optional_provider` | Provider-spezifische Pakete, z. B. `openai`, `google`, `ollama` | Kandidaten für optionale Requirements |
| `unknown` | Syntax-/Decode-/Klassifizierungsfehler | blockierend für Inventarqualität |

## Exit Codes

| Exit Code | Bedeutung |
|---:|---|
| 0 | Inventar erzeugt, keine unbekannten Imports |
| 1 | Projektwurzel fehlt oder unbekannte Imports vorhanden |
| 2 | falsche Argumente / unbekannter Kommandozustand |

## Designentscheidung

Das Werkzeug nutzt ausschließlich Python-Standardbibliothek:

- `ast`
- `sys`
- `sysconfig`
- `importlib.util`
- `pathlib`
- `json`

Grund: Dependency-Analyse darf nicht von den Dependencies abhängen, die sie prüfen soll.

## Requirements-Ableitung

Das JSON enthält:

```json
{
  "requirements_suggestion": [],
  "optional_requirements_suggestion": []
}
```

Diese Listen sind Vorschläge, keine automatische Wahrheit.

Mapping-Beispiele:

| Import | Package-Vorschlag |
|---|---|
| `yaml` | `PyYAML` |
| `fitz` | `PyMuPDF` |
| `PIL` | `Pillow` |
| `cv2` | `opencv-python` |
| `bs4` | `beautifulsoup4` |
| `sklearn` | `scikit-learn` |
| `google` | `google-generativeai or google-api-python-client` |

## Empfohlene Verwendung

Vor Release:

```powershell
python launcher.py repo-doctor
python launcher.py dependency-inventory --write-report
python launcher.py p0-gate
python launcher.py p1-gate
```

Danach manuell prüfen:

```text
release/dependency_inventory_latest.json
requirements-runtime.txt
requirements-dev.txt
```

## Grenzen

Nicht erkannt werden zuverlässig:

- dynamische Imports über Strings
- optionale Extras in Provider-Plugins
- plattformspezifische Imports, die nur unter bestimmten Betriebssystemen aktiv sind
- Package-Namen, die stark vom Importnamen abweichen

Diese Grenzen sind bewusst akzeptiert. Das Tool ist ein statisches Gate, kein vollständiger Package Resolver.
