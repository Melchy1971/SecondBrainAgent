from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.agent_kernel_v106 import AgentKernel
from secondbrain.permissions_v106 import PermissionPolicy
from secondbrain.desktop_commands_v106 import DesktopCommandService
from secondbrain.config import load_settings

settings = load_settings(PROJECT_ROOT)
vault = Path(settings.get("vault_path", PROJECT_ROOT.parent / "SecondBrain"))
runtime = vault / "99_System" / "runtime_v106"
policy = PermissionPolicy.from_dict({"max_level": 2, "require_approval_from_level": 3})
kernel = AgentKernel(runtime, policy)
desktop = DesktopCommandService(vault)

kernel.register_handler("desktop.quick_capture", lambda p: desktop.quick_capture(p.get("text", ""), p.get("title", "Quick Capture")), level="write")
kernel.register_handler("desktop.notify", lambda p: desktop.notification(p.get("message", ""), p.get("severity", "info")), level="write")

if not kernel.queue.pending():
    kernel.submit("desktop.quick_capture", {"title": "v10.6 Agent Kernel", "text": "Agent Kernel initialisiert. Job Queue, Permission Gate und Desktop Commands aktiv."})

print(kernel.tick())
