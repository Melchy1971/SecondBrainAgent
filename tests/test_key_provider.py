"""Master-Key-Provider (Phase A): Backend-Auswahl, Lifecycle, Redaction.

Hermetisch ueber den In-Memory-Fake und injizierte Keyring-Provider -- kein
echtes OS-Keyring, kein Netzwerk, keine Persistenz auf Platte.
"""

from __future__ import annotations

import json

import pytest

from secondbrain.secret_manager.crypto import KEY_LEN, decrypt, encrypt
from secondbrain.secret_manager.key_provider import (
    DEFAULT_ALIAS,
    EnvKeyProvider,
    InMemoryKeyProvider,
    KeyLocked,
    KeyNotFound,
    KeyProviderError,
    KeyProviderUnavailable,
    key_provider_health,
    resolve_key_provider,
)


# --------------------------------------------------------------------------
# Lifecycle: create / load / rotate / revoke / health
# --------------------------------------------------------------------------


def test_create_and_load_roundtrip() -> None:
    p = InMemoryKeyProvider()
    key = p.create()
    assert len(key) == KEY_LEN
    assert p.load() == key


def test_load_without_create_raises() -> None:
    with pytest.raises(KeyNotFound):
        InMemoryKeyProvider().load()


def test_revoke_removes_key() -> None:
    p = InMemoryKeyProvider()
    p.create()
    p.revoke()
    with pytest.raises(KeyNotFound):
        p.load()
    # Revoke ohne vorhandenen Key ist idempotent.
    p.revoke()


def test_rotation_keeps_existing_aes_gcm_readable() -> None:
    """Bestehende AES-GCM-Daten muessen nach Rotation weiter lesbar sein."""
    p = InMemoryKeyProvider()
    old_key = p.create()
    blob = encrypt(old_key, b"streng geheim", aad=b"vault")

    returned_old, new_key = p.rotate()
    assert returned_old == old_key
    assert new_key != old_key
    assert p.load() == new_key  # Keyring haelt jetzt den neuen Key

    # Waehrend des Umschluesselns bleibt der alte Key gueltig.
    plain = decrypt(returned_old, blob, aad=b"vault")
    assert plain == b"streng geheim"
    # Nach Umschluesselung ist der Wert mit dem neuen Key lesbar.
    rewrapped = encrypt(new_key, plain, aad=b"vault")
    assert decrypt(new_key, rewrapped, aad=b"vault") == b"streng geheim"


def test_wrong_key_cannot_decrypt() -> None:
    p1 = InMemoryKeyProvider()
    p2 = InMemoryKeyProvider()
    k1 = p1.create()
    k2 = p2.create()
    blob = encrypt(k1, b"data", aad=b"x")
    from secondbrain.secret_manager.crypto import CryptoError

    with pytest.raises(CryptoError):
        decrypt(k2, blob, aad=b"x")


# --------------------------------------------------------------------------
# Fehlendes / gesperrtes Keyring
# --------------------------------------------------------------------------


def test_missing_keyring_is_unavailable() -> None:
    p = InMemoryKeyProvider(available=False)
    assert p.available() is False
    with pytest.raises(KeyProviderUnavailable):
        p.create()


def test_locked_keyring_raises_keylocked() -> None:
    p = InMemoryKeyProvider(locked=True)
    with pytest.raises(KeyLocked):
        p.load()
    with pytest.raises(KeyLocked):
        p.create()


# --------------------------------------------------------------------------
# Auswahl: fail-closed, kein stiller Wechsel
# --------------------------------------------------------------------------


def test_production_without_keyring_is_fail_closed() -> None:
    with pytest.raises(KeyProviderUnavailable, match="no_secure_keyring_in_production"):
        resolve_key_provider(
            {"SECONDBRAIN_ENV": "production"},
            keyring_provider=InMemoryKeyProvider(available=False),
        )


def test_production_prefers_secure_keyring() -> None:
    secure = InMemoryKeyProvider(available=True)
    chosen = resolve_key_provider({"SECONDBRAIN_ENV": "production"}, keyring_provider=secure)
    assert chosen is secure
    assert chosen.secure is True


def test_env_backend_forbidden_in_production_without_optin() -> None:
    with pytest.raises(KeyProviderError, match="env_backend_forbidden_in_production"):
        resolve_key_provider({
            "SECONDBRAIN_ENV": "production",
            "SECRET_KEY_BACKEND": "env",
            "SECRET_MASTER_KEY_B64": "x",
        })


def test_env_backend_allowed_in_production_with_explicit_optin() -> None:
    from secondbrain.secret_manager.crypto import b64e, random_key

    provider = resolve_key_provider({
        "SECONDBRAIN_ENV": "production",
        "SECRET_KEY_BACKEND": "env",
        "SECRET_KEY_ALLOW_ENV_IN_PROD": "1",
        "SECRET_MASTER_KEY_B64": b64e(random_key()),
    })
    assert isinstance(provider, EnvKeyProvider)
    assert provider.secure is False  # bleibt als unsicher gekennzeichnet


def test_no_silent_switch_to_insecure_in_dev() -> None:
    """Ohne konfiguriertes Backend und ohne Keyring: kein automatischer Env-Fallback."""
    with pytest.raises(KeyProviderUnavailable):
        resolve_key_provider(
            {"SECONDBRAIN_ENV": "development"},
            keyring_provider=InMemoryKeyProvider(available=False),
        )


def test_dev_env_backend_requires_explicit_selection() -> None:
    from secondbrain.secret_manager.crypto import b64e, random_key

    provider = resolve_key_provider(
        {"SECONDBRAIN_ENV": "development", "SECRET_KEY_BACKEND": "env",
         "SECRET_MASTER_KEY_B64": b64e(random_key())},
        keyring_provider=InMemoryKeyProvider(available=False),
    )
    assert isinstance(provider, EnvKeyProvider)


# --------------------------------------------------------------------------
# Redaction: keine Secrets in Health, Exception oder Report
# --------------------------------------------------------------------------


def test_health_contains_no_key_or_plaintext_alias() -> None:
    secure = InMemoryKeyProvider(available=True)
    secure.create()
    health = key_provider_health({"SECONDBRAIN_ENV": "production"}, keyring_provider=secure)
    blob = json.dumps(health)
    # Kein Base64-Key, kein Klartext-Alias.
    assert "master-key" not in blob            # Klartext-Alias
    assert health["alias_fingerprint"] != DEFAULT_ALIAS
    assert "SECRET_MASTER_KEY" not in blob
    assert health["secure_backend"] is True


def test_health_blocked_in_production_without_keyring() -> None:
    health = key_provider_health(
        {"SECONDBRAIN_ENV": "production"},
        keyring_provider=InMemoryKeyProvider(available=False),
    )
    assert health["status"] == "blocked"
    assert health["secure_backend"] is False
    # Nur Fehlerklasse, kein Detail.
    assert health["reason"] == "KeyProviderUnavailable"


def test_exceptions_do_not_leak_key_material() -> None:
    p = InMemoryKeyProvider()
    key = p.create()
    # Ein manipulierter Store-Wert -> Fehler ohne Rohdaten.
    p._store[DEFAULT_ALIAS] = "!!!not-base64!!!"
    try:
        p.load()
    except KeyProviderError as exc:
        assert "!!!" not in str(exc)
        assert str(exc) in {"master_key_unreadable", "invalid_key_length"}
    else:
        pytest.fail("erwarteter Fehler blieb aus")
