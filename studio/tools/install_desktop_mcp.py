#!/usr/bin/env python3
"""Add the ableton-mcp server to the Claude Desktop app's config (macOS).

The desktop app rewrites claude_desktop_config.json from memory when it quits or starts, so an edit made
while the app is running is overwritten. Run this in Terminal:

    ABLETON_MCP_DIR=/path/to/ableton-mcp python3 install_desktop_mcp.py

then quit the Claude app (Cmd+Q). The script waits until the app has fully quit, patches the file, and
reopens the app. A timestamped backup of the old config is kept next to it.

ABLETON_MCP_DIR defaults to ../ableton-mcp next to this tools folder. `uv` must be on PATH.
"""
import json
import os
import shutil
import subprocess
import sys
import time

CONFIG = os.path.expanduser("~/Library/Application Support/Claude/claude_desktop_config.json")
STUDIO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MCP_DIR = os.path.abspath(os.environ.get("ABLETON_MCP_DIR", os.path.join(STUDIO, "ableton-mcp")))


def running():
    out = subprocess.run(["ps", "-axo", "command"], capture_output=True, text=True).stdout
    return any(l.strip() == "/Applications/Claude.app/Contents/MacOS/Claude" for l in out.splitlines())


def main():
    if sys.platform != "darwin":
        sys.exit("this installer is for the macOS Claude Desktop app")
    uv = shutil.which("uv")
    if uv is None:
        sys.exit("uv not found on PATH (https://docs.astral.sh/uv/)")
    if not os.path.isdir(MCP_DIR):
        sys.exit(f"ableton-mcp not found at {MCP_DIR}; set ABLETON_MCP_DIR")
    entry = {
        "command": uv,
        "args": ["run", "--directory", MCP_DIR, "ableton-mcp"],
        "env": {"ABLETON_MCP_DISABLE_TELEMETRY": "true", "ABLETON_MCP_DISABLE_DATASET": "true"},
    }
    if running():
        print("Quit the Claude app now (Cmd+Q). Waiting for it to close...")
        while running():
            time.sleep(1)
        time.sleep(2)  # let it finish writing its own config
    cfg = {}
    if os.path.exists(CONFIG):
        shutil.copy(CONFIG, CONFIG.replace(".json", ".backup-%s.json" % time.strftime("%Y%m%d-%H%M%S")))
        with open(CONFIG) as f:
            cfg = json.load(f)
    else:
        os.makedirs(os.path.dirname(CONFIG), exist_ok=True)
    cfg.setdefault("mcpServers", {})["ableton-mcp"] = entry
    tmp = CONFIG + ".tmp"
    with open(tmp, "w") as f:
        json.dump(cfg, f, indent=2)
    with open(tmp) as f:
        json.load(f)  # must stay valid before it replaces anything
    os.replace(tmp, CONFIG)
    print("ableton-mcp added to", CONFIG)
    subprocess.run(["open", "-a", "Claude"])
    print("Claude reopened. Start a new chat and check the Ableton tools.")


if __name__ == "__main__":
    sys.exit(main())
