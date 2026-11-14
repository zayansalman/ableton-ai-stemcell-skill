#!/usr/bin/env python3
"""hat_split: split a hat stem into OPEN and CLOSED hats by how long each hit rings.

    python hat_split.py "<hats.wav>" [--out-dir DIR] [--open-ms 60]

DrumSep gives one `hh` part, so open and closed hats arrive together. Every hat hit is found from the amplitude envelope
(a hit = a sharp rise above 8% of the loudest peak, 60 ms apart at least); its ring time is how long it takes to fall 20 dB
below its own peak. Rings of --open-ms (default 60 ms) or longer are OPEN, shorter ones CLOSED. Each hit keeps its whole
tail: the file is cut at the start of every hit and each segment goes to one part, with a 3 ms complementary crossfade,
so OPEN + CLOSED equals the input (error ~1e-7), the same length and sample rate (24-bit), so a warped clip lines up.

Writes "<name> - OPEN HATS.wav" and "<name> - CLOSED HATS.wav" next to the input (or in --out-dir) and prints one JSON line
{"open": path, "closed": path, "hits": [{"time_s", "ring_ms", "peak", "part"}], "sum_error": float}.
This is an energy-decay heuristic, not a model: check the hit list. A ghost note or a hat that is choked early reads as closed.
Needs numpy and soundfile only (both are in the main Stemcell environment).
"""
import argparse, json, os
import numpy as np
import soundfile as sf


def find_hits(m, sr, rel=0.08, refractory_ms=60):
    hop = max(1, sr // 1000)                      # 1 ms envelope
    n = len(m) // hop
    e = np.abs(m[:n * hop]).reshape(n, hop).max(1)
    e = np.convolve(e, np.ones(3) / 3, "same")
    hits, last = [], -10 ** 9
    for i in range(8, n):
        if e[i] > rel * e.max() and e[i] > 3 * max(e[i - 8:i - 2].max(), 1e-9) and i - last > refractory_ms:
            j = i
            while j + 1 < n and e[j + 1] >= e[j]:
                j += 1
            hits.append(j)
            last = i
    return e, hits


def classify(e, hits, open_ms):
    out = []
    for a, b in zip(hits, hits[1:] + [len(e)]):
        seg = e[a:b]
        peak = float(seg.max())
        ring = int(np.argmax(seg < peak * 0.1)) if (seg < peak * 0.1).any() else len(seg)
        out.append({"time_s": round(a / 1000, 3), "ring_ms": ring, "peak": round(peak, 3),
                    "part": "open" if ring >= open_ms else "closed"})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("hats")
    ap.add_argument("--out-dir")
    ap.add_argument("--open-ms", type=int, default=60)
    a = ap.parse_args()
    x, sr = sf.read(a.hats, dtype="float64", always_2d=True)
    e, hits = find_hits(x.mean(1), sr)
    if not hits:
        raise SystemExit("no hat hits found")
    info = classify(e, hits, a.open_ms)
    # segment boundaries: 6 ms before each hit's peak (the attack), complementary 3 ms crossfade
    mask = np.zeros(len(x))                         # 1 = OPEN
    bounds = [max(0, int(h / 1000 * sr) - int(0.006 * sr)) for h in hits] + [len(x)]
    state = 1.0 if info[0]["part"] == "open" else 0.0
    mask[:bounds[0]] = state
    for k, (s, t) in enumerate(zip(bounds, bounds[1:])):
        mask[s:t] = 1.0 if info[k]["part"] == "open" else 0.0
    fade = int(0.003 * sr)
    kern = np.hanning(2 * fade + 1); kern /= kern.sum()
    mask = np.convolve(np.pad(mask, fade, mode="edge"), kern, "same")[fade:-fade]
    op, cl = x * mask[:, None], x * (1 - mask[:, None])
    d = a.out_dir or os.path.dirname(os.path.abspath(a.hats))
    os.makedirs(d, exist_ok=True)
    base = os.path.basename(a.hats)
    base = base.rsplit(" - ", 1)[0] if " - " in base else os.path.splitext(base)[0]
    po, pc = os.path.join(d, base + " - OPEN HATS.wav"), os.path.join(d, base + " - CLOSED HATS.wav")
    sf.write(po, op, sr, subtype="PCM_24"); sf.write(pc, cl, sr, subtype="PCM_24")
    print(json.dumps({"open": po, "closed": pc, "hits": info, "sum_error": float(np.abs(op + cl - x).max()),
                      "rms": {"open": round(float(np.sqrt((op ** 2).mean())), 5), "closed": round(float(np.sqrt((cl ** 2).mean())), 5)}}))


if __name__ == "__main__":
    main()
