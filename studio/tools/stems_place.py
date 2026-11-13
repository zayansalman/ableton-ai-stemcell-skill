"""Place stems under a cut-up resample (see memory studio-method-stems). Thin CLI over the same code the MCP
tool `stemsync_place` uses (ableton-mcp/MCP_Server/stemsync.py).

Usage: python3 tools/stems_place.py            # every stem track
       python3 tools/stems_place.py "<track>"  # one track

Every clip on every stem track (any start, any length, looped or not, MIDI or audio, one or many) is mapped
through the resample pieces by where it sat in the ORIGINAL timeline, so it keeps its place relative to the
resample. Overwrites the originals: work on a saved copy. Needs the Remote Script `arrangement_clip_ops`.
"""
import json, os, socket, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ableton-mcp"))
import importlib.util

spec = importlib.util.spec_from_file_location(
    "stemsync", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ableton-mcp", "MCP_Server", "stemsync.py"))
stemsync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stemsync)


def send(cmd, params=None):
    s = socket.create_connection(("127.0.0.1", 9877))
    s.settimeout(120)
    s.sendall(json.dumps({"type": cmd, "params": params or {}}).encode())
    d = b""
    while True:
        d += s.recv(1 << 20)
        try:
            j = json.loads(d)
            return j.get("result", j)
        except ValueError:
            pass


if __name__ == "__main__":
    out = stemsync.place_all(send, sys.argv[1] if len(sys.argv) > 1 else None)
    print("\n".join(out["report"]))
