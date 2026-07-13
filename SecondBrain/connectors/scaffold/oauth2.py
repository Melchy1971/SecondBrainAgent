"""Generic OAuth2 authenticator: device-code flow (+ auth-code exchange) + refresh.

Token requests are form-urlencoded. Tokens persist via the existing TokenRepository;
the refresh-window decision uses the existing TokenRefreshService.
"""

from __future__ import annotations

import json
import time
import urllib.parse
from dataclasses import dataclass
from typing import Callable

from secondbrain.connectors.token_repository import TokenRepository
from secondbrain.connectors.token_refresh import TokenRefreshService
from secondbrain.connectors.scaffold.approval import ApprovalGate
from secondbrain.connectors.scaffold.transport import Transport, UrllibTransport


class OAuth2Error(RuntimeError):
    pass


@dataclass(frozen=True)
class OAuth2Config:
    client_id: str
    scopes: tuple[str, ...]
    token_url: str
    devicecode_url: str | None = None
    auth_url: str | None = None
    redirect_uri: str | None = None
    client_secret: str | None = None
    provider: str = "provider"
    token_store_path: str = "runtime/connectors/tokens.json"
    device_scope_separator: str = " "

    def scope_string(self) -> str:
        return self.device_scope_separator.join(self.scopes)


@dataclass(frozen=True)
class DeviceCodeStart:
    device_code: str
    user_code: str
    verification_uri: str
    expires_in: int
    interval: int
    message: str

    def to_public_dict(self) -> dict:
        return {"user_code": self.user_code, "verification_uri": self.verification_uri,
                "expires_in": self.expires_in, "message": self.message}


class OAuth2Authenticator:
    def __init__(
        self,
        config: OAuth2Config,
        *,
        transport: Transport | None = None,
        token_repo: TokenRepository | None = None,
        refresh_service: TokenRefreshService | None = None,
        clock: Callable[[], float] = time.time,
        scope_gate: ApprovalGate | None = None,
    ) -> None:
        self.config = config
        self.transport = transport or UrllibTransport()
        self.token_repo = token_repo or TokenRepository(config.token_store_path)
        self.refresh_service = refresh_service or TokenRefreshService()
        self.clock = clock
        self.provider = config.provider
        self.scope_gate = scope_gate or ApprovalGate(
            project_root=self._project_root(),
            connector_id=self.provider,
            effective_scopes=self._effective_scopes(),
            clock=clock,
        )

    # ---- device code -----------------------------------------------------
    def begin_device_login(self) -> DeviceCodeStart:
        if not self.config.devicecode_url:
            raise OAuth2Error("device code flow not configured for this provider")
        effective_scopes = self._effective_scopes()
        payload = self.scope_gate.guard(
            action="oauth.scope.update",
            resource=self.provider,
            method="GET",
            target=self.provider,
            payload={"requested_scopes": list(self.config.scopes)},
            effective_scopes=effective_scopes,
            requested_scopes=self.config.scopes,
            execute=lambda: self._form_post(self.config.devicecode_url, {
                "client_id": self.config.client_id,
                "scope": self.config.scope_string(),
            }),
        )
        code = payload.get("device_code")
        if not code:
            raise OAuth2Error(f"device code request failed: {payload.get('error_description') or payload}")
        return DeviceCodeStart(
            device_code=code,
            user_code=payload.get("user_code", ""),
            verification_uri=payload.get("verification_uri") or payload.get("verification_url", ""),
            expires_in=int(payload.get("expires_in", 900)),
            interval=int(payload.get("interval", 5)),
            message=payload.get("message", ""),
        )

    def _effective_scopes(self) -> tuple[str, ...]:
        token = self.token_repo.load_all().get(self.provider) or {}
        raw = token.get("scope") or token.get("scopes")
        if isinstance(raw, str):
            scopes = tuple(scope for scope in raw.replace(",", " ").split() if scope)
        elif isinstance(raw, (list, tuple, set)):
            scopes = tuple(str(scope) for scope in raw if str(scope))
        else:
            scopes = ()
        # Initial login establishes the explicitly configured baseline. Only later
        # expansion relative to a persisted grant needs a separate approval.
        return scopes or tuple(self.config.scopes)

    def _project_root(self):
        path = self.token_repo.path.resolve()
        parent = path.parent
        if parent.name == "connectors" and parent.parent.name == "runtime":
            return parent.parent.parent
        return parent

    def poll_once(self, device_code: str) -> tuple[str, dict | None]:
        form = {
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "client_id": self.config.client_id,
            "device_code": device_code,
        }
        if self.config.client_secret:
            form["client_secret"] = self.config.client_secret
        payload = self._form_post(self.config.token_url, form)
        if "access_token" in payload:
            return "ok", self._store_token(payload)
        error = payload.get("error", "error")
        if error in ("authorization_pending",):
            return "pending", None
        if error in ("slow_down",):
            return "slow_down", None
        raise OAuth2Error(payload.get("error_description") or error)

    def complete_device_login(self, start: DeviceCodeStart, *, sleeper: Callable[[float], None] = time.sleep) -> dict:
        interval = max(1, start.interval)
        deadline = self.clock() + start.expires_in
        while self.clock() < deadline:
            state, token = self.poll_once(start.device_code)
            if state == "ok" and token is not None:
                return token
            if state == "slow_down":
                interval += 5
            sleeper(interval)
        raise OAuth2Error("device login timed out before authorization")

    # ---- auth-code (optional) --------------------------------------------
    def exchange_code(self, code: str, *, code_verifier: str | None = None) -> dict:
        form = {
            "grant_type": "authorization_code",
            "client_id": self.config.client_id,
            "code": code,
            "redirect_uri": self.config.redirect_uri or "",
        }
        if self.config.client_secret:
            form["client_secret"] = self.config.client_secret
        if code_verifier:
            form["code_verifier"] = code_verifier
        payload = self._form_post(self.config.token_url, form)
        if "access_token" not in payload:
            raise OAuth2Error(payload.get("error_description") or "code exchange failed")
        return self._store_token(payload)

    # ---- token lifecycle -------------------------------------------------
    def access_token(self) -> str:
        token = self.token_repo.load_all().get(self.provider)
        if not token or not token.get("access_token"):
            raise OAuth2Error(f"not authenticated - run {self.provider}-login")
        if self.refresh_service.should_refresh(float(token.get("expires_at", 0.0))):
            rt = token.get("refresh_token")
            if not rt:
                raise OAuth2Error(f"token expired and no refresh_token - run {self.provider}-login")
            token = self.refresh(rt)
        return token["access_token"]

    def refresh(self, refresh_token: str) -> dict:
        form = {
            "grant_type": "refresh_token",
            "client_id": self.config.client_id,
            "refresh_token": refresh_token,
            "scope": self.config.scope_string(),
        }
        if self.config.client_secret:
            form["client_secret"] = self.config.client_secret
        payload = self._form_post(self.config.token_url, form)
        if "access_token" not in payload:
            raise OAuth2Error(payload.get("error_description") or "refresh failed")
        return self._store_token(payload)

    def is_authenticated(self) -> bool:
        token = self.token_repo.load_all().get(self.provider)
        return bool(token and token.get("access_token"))

    def status(self) -> dict:
        token = self.token_repo.load_all().get(self.provider) or {}
        expires_at = float(token.get("expires_at", 0.0))
        return {"provider": self.provider, "authenticated": bool(token.get("access_token")),
                "expires_at": expires_at,
                "seconds_to_expiry": max(0, int(expires_at - self.clock())) if expires_at else 0,
                "scopes": token.get("scope", self.config.scope_string())}

    def forget(self) -> bool:
        data = self.token_repo.load_all()
        existed = self.provider in data
        if existed:
            del data[self.provider]
            self.token_repo.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return existed

    # ---- internals -------------------------------------------------------
    def _store_token(self, payload: dict) -> dict:
        now = self.clock()
        token = {
            "access_token": payload["access_token"],
            "refresh_token": payload.get("refresh_token"),
            "expires_at": now + float(payload.get("expires_in", 3600)),
            "scope": payload.get("scope", self.config.scope_string()),
            "token_type": payload.get("token_type", "Bearer"),
        }
        if token["refresh_token"] is None:
            prev = self.token_repo.load_all().get(self.provider) or {}
            token["refresh_token"] = prev.get("refresh_token")
        self.token_repo.save(self.provider, token)
        return token

    def _form_post(self, url: str, form: dict[str, str]) -> dict:
        body = urllib.parse.urlencode(form).encode("utf-8")
        resp = self.transport.request("POST", url,
                                      headers={"Content-Type": "application/x-www-form-urlencoded",
                                               "Accept": "application/json"}, body=body)
        try:
            return resp.json()
        except Exception:
            return {"error": "invalid_response",
                    "error_description": resp.body[:200].decode("utf-8", "replace")}
