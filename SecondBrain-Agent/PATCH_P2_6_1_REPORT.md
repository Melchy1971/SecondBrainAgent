# PATCH P2.6.1 — Settings Center Foundation

## Inhalt
- `secondbrain.desktop.settings.settings_models`
- `settings_registry` mit Default-Kategorien
- `settings_validation` für Typen, Choices und Grenzen
- `settings_store` für JSON-Persistenz
- `settings_service` mit get/set/reset/snapshot/export
- Secret-Masking für UI-Snapshots
- Tests für Defaults, Persistenz, Validierung, Reset und Registry-Konflikte

## Validierung
- `8 passed in 0.25s`

## Wirkung
- Settings-Center besitzt ein stabiles, testbares Fundament.
- Secrets werden nicht im UI-Snapshot offengelegt.
- Ungültige Konfiguration wird vor Persistenz geblockt.
