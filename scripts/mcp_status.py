from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
server = ROOT / "mcp-server" / "server.py"
req = ROOT / "mcp-server" / "requirements.txt"
claude = ROOT / "config" / "claude" / "claude_desktop_config_secondbrain.json"

print("MCP Direct Import Status")
print("server.py:", "OK" if server.exists() else "FEHLT")
print("requirements.txt:", "OK" if req.exists() else "FEHLT")
print("Claude Config Vorlage:", "OK" if claude.exists() else "FEHLT")
print("")
print("Installation:")
print(r"cd H:\SecondBrainAgent\SecondBrain-Agent\mcp-server")
print("pip install -r requirements.txt")
print("")
print("Claude Config:")
print(r"%APPDATA%\Claude\claude_desktop_config.json")

print("Neue Tools v8.1.2: create_project_folder, slash_command (/plan)")
