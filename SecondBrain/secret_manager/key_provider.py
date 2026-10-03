"""Master-Key-Provider mit OS-Keyring als bevorzugtem Backend (Phase A).

Der Master-Key wird niemals im Repository, in Klartextdateien oder Logs
abgelegt. Bevorzugt liegt er im OS-Keyring (Windows Credential Manager, macOS
Keychain, Freedesktop Secret Service). Eine Environment-Variable ist nur als
ausdruecklich aktivierter CI-/Testmodus zulaessig. Im Produktionsprofil startet
die Secret-Funktion nicht, wenn kein sicheres Backend verfuegbar ist -- kein
stiller Wechsel auf ein unsicheres Backend.

Lifecycle je Provider: create, load, rotate, revoke, health.

Rotation
--------
``rotate`` erzeugt einen neuen Master-Key und legt ihn ab, gibt aber den alten
UND den neuen Key zurueck. Damit kann der Aufrufer bestehende AES-GCM-Daten
umschluesseln; bis zum Abschluss bleiben die alten Daten mit dem alten Key
lesbar.

Alle Health-/Fehlerausgaben sind redigiert: kein Key, kein Alias-Klartext, kein
Benutzer, kein Pfad.
"""

from __future__ import annotations

import hashlib
import os
from typing import Any, Mapping, Protocol

from secondbrain.secret_manager.crypto import KEY_LEN, b64d, b64e, random_key

SERVICE_NAME = "secondbrain-secret-vault"
DEFAULT_ALIAS = "master-key"

# Umgebungsschluessel.
ENV_PROFILE = "SECONDBRAIN_ENV"
ENV_BACKEND = "SECRET_KEY_BACKEND"          # "keyring" | "env" | "" (auto)
ENV_MASTER_KEY = "SECRET_MASTER_KEY_B64"    # nur fuer Env-Backend
ENV_ALLOW_ENV_IN_PROD = "SECRET_KEY_ALLOW_ENV_IN_PROD"  # muss "1" sein


class KeyProviderError(RuntimeError):
    """Basisfehler. Die Meldung traegt nie einen Key oder Klartext-Alias."""


class KeyProviderUnavailable(KeyProviderError):
    """Kein sicheres Backend verfuegbar."""


class KeyLocked(KeyProviderError):
    """Das Keyring ist gesperrt und kann nicht gelesen werden."""


class KeyNotFound(KeyProviderError):
    """Unter dem Alias liegt kein Key."""


def _alias_fingerprint(alias: str) -> str:
    """Redigierte Alias-Kennung fuer Reports -- nie der Klartext-Alias."""
    return hashlib.sha256(alias.encode("utf-8")).hexdigest()[:12]


def _validate_key(raw: bytes) -> bytes:
    if len(raw) != KEY_LEN:
        raise KeyProviderError("invalid_key_length")
    return raw


class KeyProvider(Protocol):
    name: str
    secure: bool

    def available(self) -> bool: ...
    def create(self, alias: str = DEFAULT_ALIAS) -> bytes: ...
    def load(self, alias: str = DEFAULT_ALIAS) -> bytes: ...
    def rotate(self, alias: str = DEFAULT_ALIAS) -> tuple[bytes, bytes]: ...
    def revoke(self, alias: str = DEFAULT_ALIAS) -> None: ...
    def health(self) -> dict[str, Any]: ...


class _BaseProvider:
    name = "base"
    secure = False

    def _get(self, alias: str) -> str | None:  # pragma: no cover - abstrakt
        raise NotImplementedError

    def _set(self, alias: str, value: str) -> None:  # pragma: no cover
        raise NotImplementedError

    def _delete(self, alias: str) -> None:  # pragma: no cover
        raise NotImplementedError

    def available(self) -> bool:
        return True

    def create(self, alias: str = DEFAULT_ALIAS) -> bytes:
        if not self.available():
            raise KeyProviderUnavailable(f"backend_unavailable:{self.name}")
        key = random_key()
        self._set(alias, b64e(key))
        return key

    def load(self, alias: str = DEFAULT_ALIAS) -> bytes:
        if not self.available():
            raise KeyProviderUnavailable(f"backend_unavailable:{self.name}")
        stored = self._get(alias)
        if stored is None:
            raise KeyNotFound("master_key_not_found")
        try:
            return _validate_key(b64d(stored))
        except KeyProviderError:
            raise
        except Exception as exc:  # noqa: BLE001 - keine Rohdaten in der Meldung
            raise KeyProviderError("master_key_unreadable") from None

    def rotate(self, alias: str = DEFAULT_ALIAS) -> tuple[bytes, bytes]:
        old = self.load(alias)
        new = random_key()
        self._set(alias, b64e(new))
        return old, new

    def revoke(self, alias: str = DEFAULT_ALIAS) -> None:
        try:
            self._delete(alias)
        except KeyNotFound:
            pass

    def health(self) -> dict[str, Any]:
        return {
            "component": "key_provider",
            "backend": self.name,
            "secure": self.secure,
            "available": self.available(),
        }


class OSKeyringKeyProvider(_BaseProvider):
    """Bevorzugtes Backend: OS-Keyring via ``keyring``-Bibliothek."""

    name = "os_keyring"
    secure = True

    def __init__(self, *, service: str = SERVICE_NAME) -> None:
        self.service = service

    def _keyring(self):
        try:
            import keyring
        except Exception as exc:  # noqa: BLE001
            raise KeyProviderUnavailable("keyring_module_missing") from None
        return keyring

    def available(self) -> bool:
        try:
            import keyring
            from keyring.backends import fail as _fail
        except Exception:  # noqa: BLE001
            return False
        try:
            backend = keyring.get_keyring()
        except Exception:  # noqa: BLE001
            return False
        # Das Null-Backend (fail.Keyring) gilt nicht als sicher verfuegbar.
        return not isinstance(backend, _fail.Keyring)

    def _get(self, alias: str) -> str | None:
        keyring = self._keyring()
        try:
            return keyring.get_password(self.service, alias)
        except Exception as exc:  # noqa: BLE001 - z. B. gesperrtes Keyring
            raise KeyLocked("keyring_locked_or_unreadable") from None

    def _set(self, alias: str, value: str) -> None:
        keyring = self._keyring()
        try:
            keyring.set_password(self.service, alias, value)
        except Exception:  # noqa: BLE001
            raise KeyLocked("keyring_locked_or_readonly") from None

    def _delete(self, alias: str) -> None:
        keyring = self._keyring()
        try:
            keyring.delete_password(self.service, alias)
        except Exception:  # noqa: BLE001 - fehlender Eintrag oder gesperrt
            raise KeyNotFound("master_key_not_found") from None

    def health(self) -> dict[str, Any]:
        base = super().health()
        try:
            import keyring
            base["keyring_backend"] = type(keyring.get_keyring()).__name__
        except Exception:  # noqa: BLE001
            base["keyring_backend"] = "unavailable"
        return base


class EnvKeyProvider(_BaseProvider):
    """CI-/Testbackend: Master-Key aus einer Environment-Variable.

    Ausdruecklich unsicher und nur nach expliziter Aktivierung. Wird nie
    automatisch gewaehlt.
    """

    name = "env"
    secure = False

    def __init__(self, env: Mapping[str, str]) -> None:
        self._env = dict(env)

    def available(self) -> bool:
        return bool(self._env.get(ENV_MASTER_KEY))

    def _get(self, alias: str) -> str | None:
        return self._env.get(ENV_MASTER_KEY)

    def _set(self, alias: str, value: str) -> None:
        # Bewusst prozesslokal: der Env-Modus persistiert nichts auf Platte.
        self._env[ENV_MASTER_KEY] = value

    def _delete(self, alias: str) -> None:
        self._env.pop(ENV_MASTER_KEY, None)


class InMemoryKeyProvider(_BaseProvider):
    """Hermetischer Fake fuer Tests. Kein echtes Backend."""

    name = "memory"
    secure = True  # fuer Tests als sicher behandelt

    def __init__(self, *, available: bool = True, locked: bool = False) -> None:
        self._store: dict[str, str] = {}
        self._available = available
        self._locked = locked

    def available(self) -> bool:
        return self._available

    def _guard(self) -> None:
        if self._locked:
            raise KeyLocked("keyring_locked")

    def _get(self, alias: str) -> str | None:
        self._guard()
        return self._store.get(alias)

    def _set(self, alias: str, value: str) -> None:
        self._guard()
        self._store[alias] = value

    def _delete(self, alias: str) -> None:
        self._guard()
        if alias not in self._store:
            raise KeyNotFound("master_key_not_found")
        del self._store[alias]


# --------------------------------------------------------------------------
# Auswahl -- fail-closed in Produktion, kein stiller Wechsel
# --------------------------------------------------------------------------


def _is_production(env: Mapping[str, str]) -> bool:
    return str(env.get(ENV_PROFILE) or "development").lower().startswith("prod")


def resolve_key_provider(env: Mapping[str, str] | None = None, *,
                         keyring_provider: KeyProvider | None = None) -> KeyProvider:
    """Waehlt das Backend. Sicheres OS-Keyring bevorzugt.

    * Explizit ``SECRET_KEY_BACKEND=env``: Env-Backend, in Produktion nur mit
      ``SECRET_KEY_ALLOW_ENV_IN_PROD=1``.
    * Sonst OS-Keyring, wenn verfuegbar.
    * In Produktion ohne sicheres Keyring -> fail-closed.
    * In Entwicklung ohne Keyring -> nur mit explizitem Env-Backend, sonst Fehler.
    """
    values = dict(os.environ if env is None else env)
    production = _is_production(values)
    backend = str(values.get(ENV_BACKEND) or "").lower()
    osk = keyring_provider if keyring_provider is not None else OSKeyringKeyProvider()

    if backend == "env":
        if production and values.get(ENV_ALLOW_ENV_IN_PROD) != "1":
            raise KeyProviderError("env_backend_forbidden_in_production")
        provider = EnvKeyProvider(values)
        if not provider.available():
            raise KeyProviderUnavailable("env_backend_selected_but_no_master_key")
        return provider

    if backend in {"keyring", "os_keyring", ""} and osk.available():
        return osk

    if production:
        # Kein sicheres Backend -> Secret-Funktionen bleiben aus.
        raise KeyProviderUnavailable("no_secure_keyring_in_production")

    # Entwicklung: nur mit ausdruecklich aktiviertem Env-Backend.
    dev_env = EnvKeyProvider(values)
    if backend == "env" or dev_env.available():
        return dev_env
    raise KeyProviderUnavailable(
        "no_secure_backend; set SECRET_KEY_BACKEND explicitly for development")


def key_provider_health(env: Mapping[str, str] | None = None, *,
                        keyring_provider: KeyProvider | None = None) -> dict[str, Any]:
    """Redigierte Health-Ausgabe. Enthaelt nie Key, Alias-Klartext oder Pfad."""
    values = dict(os.environ if env is None else env)
    try:
        provider = resolve_key_provider(values, keyring_provider=keyring_provider)
    except KeyProviderError as exc:
        return {
            "component": "key_provider",
            "status": "blocked",
            "secure_backend": False,
            "reason": type(exc).__name__,
            "production": _is_production(values),
        }
    health = provider.health()
    health.update({
        "status": "ok" if provider.secure else "insecure_dev_backend",
        "secure_backend": bool(provider.secure),
        "production": _is_production(values),
        "alias_fingerprint": _alias_fingerprint(DEFAULT_ALIAS),
    })
    return health
