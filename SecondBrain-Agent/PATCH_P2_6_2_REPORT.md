# PATCH P2.6.2 - Settings Provider Configuration

## Inhalt
- ProviderProfile-Modell für Embedding, LLM, OCR, Storage und Connectoren
- ProviderRegistry mit Default-Providern
- ProviderProfileValidator mit Pflichtfeld-, Typ-, Choice- und Bounds-Prüfung
- ProviderProfileStore für JSON-Persistenz
- ProviderProfileService für Create/Update/Delete/Enable/Disable/Import/Export
- Secret-Referenzen werden bei normalem Read/Export maskiert

## Validierung
- `14 passed in 0.30s`

## Risiko
- Noch keine echte UI-Komponente, nur Desktop-Settings-Domainlogik.
- Keine echte Vault-Auflösung, nur Secret-Referenz-Verwaltung.
