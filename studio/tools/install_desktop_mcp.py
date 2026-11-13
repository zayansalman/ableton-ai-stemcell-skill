#!/usr/bin/env python3
"""Add the ableton-mcp server to the Claude DESKTOP app's config (chat / Cowork sessions).

Why a script: the desktop app rewrites claude_desktop_config.json from memory when it quits or starts, so an
edit made while the app is running is overwritten (this happened on 2026-10-19). Run this in Terminal:

    python3 tools/install_desktop_mcp.py

then quit the Claude app (Cmd+Q). The script waits until the app has fully quit, patches the file, and
reopens the app. A timestamped backup of the old config is kept next to it.
"""
import json
import os
import shutil
import subprocess
import sys
import time

CONFIG = os.path.expanduser("~/Library/Application Support/Claude/claude_desktop_config.json")
ENTRY = {
    "command": "/opt/homebrew/bin/uv",
    "args": ["run", "--directory", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ableton-mcp"),
             "ableton-mcp"],
    "env": {"ABLETON_MCP_DISABLE_TELEMETRY": "true", "ABLETON_MCP_DISABLE_DATASET": "true"},
}


def running():
    out = subprocess.run(["ps", "-axo", "command"], capture_output=True, text=True).stdout
    return any(l.strip() == "/Applications/Claude.app/Contents/MacOS/Claude" for l in out.splitlines())


def main():
    if running():
        print("Quit the Claude app now (Cmd+Q). Waiting for it to close...")
        while running():
            time.sleep(1)
        time.sleep(2)  # let it finish writing its own config
    shutil.copy(CONFIG, CONFIG.replace(".json", ".backup-%s.json" % time.strftime("%Y%m%d-%H%M%S")))
    cfg = json.load(open(CONFIG))
    cfg.setdefault("mcpServers", {})["ableton-mcp"] = ENTRY
    json.dump(cfg, open(CONFIG, "w"), indent=2)
    json.load(open(CONFIG))  # must stay valid
    print("ableton-mcp added to", CONFIG)
    subprocess.run(["open", "-a", "Claude"])
    print("Claude reopened. Start a NEW chat and check the Ableton tools.")


if __name__ == "__main__":
    sys.exit(main())
