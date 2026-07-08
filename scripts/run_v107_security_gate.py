from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.security_v107 import SecureCommandGateway, PolicyEngine
from secondbrain.config import load_settings

settings = load_settings(PROJECT_ROOT)
vault = Path(settings.get("vault_path", PROJECT_ROOT.parent / "SecondBrain"))
runtime = vault / "99_System" / "security"

gateway = SecureCommandGateway(runtime, PolicyEngine(max_level=2, approval_threshold=60))
gateway.register("note.create", lambda p: {"created": p.get("title", "Untitled")}, level="write")
gateway.register("system.shell", lambda p: {"executed": p.get("cmd")}, level="execute")

print("SAFE_WRITE", gateway.execute("note.create", {"title": "v10.7 Security Gate"}))
print("EXECUTE_BLOCKED", gateway.execute("system.shell", {"cmd": "rm -rf /"}))
print("PENDING_APPROVALS", gateway.approvals.pending())
print("AUDIT_LOG", str(gateway.audit.path))
