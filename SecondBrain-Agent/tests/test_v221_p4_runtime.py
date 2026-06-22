from secondbrain.connectors.delta_sync import DeltaSynchronizer
from secondbrain.connectors.token_refresh import TokenRefreshService
from secondbrain.connectors.conflict_resolution import ConflictResolver
from secondbrain.gates.p4_production_gate import P4ProductionGate


def test_delta_sync():
    sync = DeltaSynchronizer()
    sync.save_checkpoint("gmail", "cursor1")
    assert sync.get_checkpoint("gmail").cursor == "cursor1"


def test_token_refresh():
    assert TokenRefreshService().should_refresh(0)


def test_conflict_resolution():
    result = ConflictResolver().resolve(
        {"updated_at": 1},
        {"updated_at": 2},
    )
    assert result["updated_at"] == 2


def test_p4_gate():
    caps = {k: True for k in P4ProductionGate.REQUIRED}
    assert P4ProductionGate().evaluate(caps)["status"] == "PASS"
