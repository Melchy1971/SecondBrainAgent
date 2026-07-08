from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.agent_kernel_v106 import AgentKernel
from secondbrain.permissions_v106 import PermissionPolicy
from secondbrain.desktop_commands_v106 import DesktopCommandService


def test_permission_policy_blocks_high_level():
    policy = PermissionPolicy(max_level=2)
    assert policy.evaluate("read.mail", "read").allowed
    assert not policy.evaluate("system.shutdown", "system").allowed


def test_agent_kernel_runs_allowed_job(tmp_path):
    kernel = AgentKernel(tmp_path, PermissionPolicy(max_level=2, require_approval_from_level=3))
    output = []
    kernel.register_handler("note.create", lambda p: output.append(p["text"]), level="write")
    kernel.submit("note.create", {"text": "ok"})
    result = kernel.tick()
    assert result["processed"] == 1
    assert output == ["ok"]
    assert kernel.load_state().cycles == 1


def test_agent_kernel_blocks_unapproved_execute(tmp_path):
    kernel = AgentKernel(tmp_path, PermissionPolicy(max_level=3, require_approval_from_level=3))
    kernel.register_handler("cmd.run", lambda p: None, level="execute")
    kernel.submit("cmd.run", {})
    result = kernel.tick()
    assert result["blocked"] == 1


def test_desktop_quick_capture_writes_note(tmp_path):
    service = DesktopCommandService(tmp_path)
    target = service.quick_capture("Hallo", "Test Note")
    assert target.exists()
    assert "Hallo" in target.read_text(encoding="utf-8")
