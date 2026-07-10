"""Secret references.

Callers store and pass around references like ``secret://<workspace>/<name>``
instead of plaintext values. The plaintext is resolved from the vault only at the
point of use, so it never has to live in configs, reports, or prompt history.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from secondbrain.vault.errors import SecretReferenceError

SCHEME = "secret://"
_REF_RE = re.compile(r"^secret://(?P<workspace>[A-Za-z0-9_.\-]+)/(?P<name>[A-Za-z0-9_.\-]+)$")


@dataclass(frozen=True)
class SecretRef:
    workspace: str
    name: str

    def __str__(self) -> str:
        return f"{SCHEME}{self.workspace}/{self.name}"


def is_reference(value: object) -> bool:
    return isinstance(value, str) and value.startswith(SCHEME)


def format_reference(workspace: str, name: str) -> str:
    return str(SecretRef(workspace, name))


def parse_reference(value: str) -> SecretRef:
    match = _REF_RE.match(value or "")
    if not match:
        raise SecretReferenceError(f"malformed secret reference: {value!r}")
    return SecretRef(match.group("workspace"), match.group("name"))
