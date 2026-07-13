# Update Policy

## Vor jedem Update

1. Backup erstellen
2. `secrets.local.yaml` sichern
3. Update einspielen
4. Production Gate ausführen
5. Smoke Tests ausführen

## Niemals überschreiben

```text
config/secrets.local.yaml
archive/
backups/
logs/
```
