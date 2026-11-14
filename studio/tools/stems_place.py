"""Place stems under a cut-up resample. Thin CLI over the same code the MCP tool `stemsync_place` uses.

Usage: python3 stems_place.py            # every stem track
       python3 stems_place.py "<track>"  # one track

Every clip on every stem track (any start, any length, looped or not, MIDI or audio, one or many) is mapped
through the resample pieces by where it sat in the ORIGINAL timeline, so it keeps its place relative to the
resample. Overwrites the originals: work on a saved copy.

Requires an ableton-mcp checkout that includes the `MCP_Server/stemsync.py` module and the Remote Script
command `arrangement_clip_ops`. These are NOT part of upstream ahujasid/ableton-mcp. Point ABLETON_MCP_DIR at
that checkout (default: ../ableton-mcp next to this tools folder). The Remote Script must be listening on
127.0.0.1:9877 (Live open, control surface enabled).
"""
import importlib.util
import json
import os
import socket
import sys

HOST, PORT = "127.0.0.1", 9877
STUDIO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MCP_DIR = os.environ.get("ABLETON_MCP_DIR", os.path.join(STUDIO, "ableton-mcp"))


def load_stemsync():
    path = os.path.join(MCP_DIR, "MCP_Server", "stemsync.py")
    if not os.path.isfile(path):
        sys.exit(f"stemsync.py not found at {path}.\n"
                 "Set ABLETON_MCP_DIR to an ableton-mcp checkout that includes MCP_Server/stemsync.py "
                 "(not in upstream ableton-mcp).")
    sys.path.insert(0, MCP_DIR)
    spec = importlib.util.spec_from_file_location("stemsync", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def send(cmd, params=None):
    """Send one command to the Remote Script and return its result."""
    with socket.create_connection((HOST, PORT), timeout=10) as s:
        s.settimeout(120)
        s.sendall(json.dumps({"type": cmd, "params": params or {}}).encode())
        data = b""
        while True:
            chunk = s.recv(1 << 20)
            if not chunk:
                raise ConnectionError(f"Remote Script closed the connection before a full reply to {cmd!r}")
            data += chunk
            try:
                reply = json.loads(data)
            except ValueError:
                continue
            return reply.get("result", reply)


def main():
    stemsync = load_stemsync()
    try:
        out = stemsync.place_all(send, sys.argv[1] if len(sys.argv) > 1 else None)
    except (ConnectionRefusedError, socket.timeout) as e:
        sys.exit(f"cannot reach the Ableton Remote Script on {HOST}:{PORT} ({e}). Is Live open with ableton-mcp enabled?")
    print("\n".join(out["report"]))


if __name__ == "__main__":
    main()
