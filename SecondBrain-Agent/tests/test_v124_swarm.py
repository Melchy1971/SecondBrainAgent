
from secondbrain.launcher_runtime_v124 import SecondBrainLauncherV124
from secondbrain.swarm.kernel import SwarmKernel

def test_swarm_kernel_run(tmp_path):
    swarm = SwarmKernel(tmp_path)
    result = swarm.run("Analysiere Jarvis Knowledge Graph und erstelle einen sicheren Plan")
    assert result["status"] == "completed"
    assert result["review"]["passed"] is True
    assert result["consensus"]["decision"] == "accepted"
    assert swarm.status()["completed"] == 1
    assert swarm.task(result["task_id"])["task"]["status"] == "completed"

def test_launcher_swarm_commands(tmp_path):
    launcher = SecondBrainLauncherV124(tmp_path)
    assert launcher.core124_status()["version"] == "12.4"
    assert len(launcher.swarm_agents()) >= 6
    result = launcher.swarm_run("Plane die Integration von Multi Agent Swarm")
    assert result["task_id"].startswith("swarm_")
    assert launcher.swarm_task(result["task_id"])["context"]["plan"]
    assert launcher.swarm_consensus(result["task_id"])[0]["decision"] == "accepted"

def test_swarm_tool_registry_integration(tmp_path):
    launcher = SecondBrainLauncherV124(tmp_path)
    tools = [t["name"] for t in launcher.tool_registry_v121.list()]
    assert "swarm.run" in tools
    result = launcher.tool_registry_v121.execute(
        "swarm.run",
        {"objective": "Teste Tool Registry Integration"},
        scopes=["swarm.write"],
        approved=True,
    )
    assert result["status"] == "success"
    assert result["result"]["status"] == "completed"
