# Release Process v6.1

## 1. Vorbereitung

```powershell
python scripts\create_backup.py
```

## 2. Diagnose

```powershell
python scripts\runtime_diagnostics.py
```

## 3. Tests

```powershell
python scripts\run_hardening_tests.py
```

## 4. Backup/Restore

```powershell
python scripts\backup_restore_test.py
```

## 5. Release Gate

```powershell
python scripts\release_gate.py
```

## 6. Ergebnis

Release nur bei PASS.
