"""Google Workspace integration (v30.79) built on the shared connector scaffold."""
from secondbrain.connectors.google.config import GoogleConfig, GoogleConfigError
from secondbrain.connectors.google.runtime import GoogleRuntime

__all__ = ["GoogleConfig", "GoogleConfigError", "GoogleRuntime"]
