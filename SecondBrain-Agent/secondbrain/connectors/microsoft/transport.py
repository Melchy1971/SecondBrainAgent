"""M365 transport (canonical implementation lives in the scaffold)."""
from secondbrain.connectors.scaffold.transport import (
    HttpResponse, Transport, UrllibTransport, FakeTransport, Route,
)
__all__ = ["HttpResponse", "Transport", "UrllibTransport", "FakeTransport", "Route"]
