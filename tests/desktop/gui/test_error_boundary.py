from secondbrain.desktop.gui.error_boundary import ErrorBoundary

def test_error_boundary_captures_recoverable_error():
    boundary = ErrorBoundary()
    err = boundary.capture("dashboard", RuntimeError("boom"))
    assert err.source == "dashboard"
    assert "dashboard" in boundary.disabled_modules

def test_error_boundary_guard_returns_fallback():
    boundary = ErrorBoundary()
    result = boundary.guard("search", lambda: (_ for _ in ()).throw(ValueError("bad")), fallback="safe")
    assert result == "safe"
    assert boundary.errors
