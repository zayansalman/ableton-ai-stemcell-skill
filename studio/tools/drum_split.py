#!/usr/bin/env python3
"""drum_split: split a drum loop with DrumSep, the way the Prolink Sync GRAB does it.

    python drum_split.py <loop.wav> <out_dir> [--mode grab|top|kit] [--group NAME=inst,inst ...]

DrumSep (MDX23C, vendored in the Prolink Sync repo as device/drumsplit.py) separates kick, snare, toms, hh, ride, crash.

  --mode grab (default)  exactly what GRAB does to a drums stem: KICK and REST OF DRUMS, using the kick-transient boost so the kick keeps its top
                         end (drumsplit.split_kick). kick + rest == the loop.
  --mode top             for a top loop (hats / snare / clap, no kick): HATS and SNARE_CLAP. hats = hh, ride, crash, kick, toms (the "rest"
                         is folded into the hats, never into the snare/clap), snare_clap = snare. Ratio masks of the original: the two add back up
                         to it exactly (max difference ~1e-7).
  --group NAME=insts     your own groups (repeat per output; instruments kick snare toms hh ride crash; any not named join the last group).

Writes "<loop name> - <group>.wav" (24-bit, same sample rate and length as the loop, so a warped clip lines up exactly) and prints one
JSON line: {"mode": ..., "files": {group: path}, "rms": {...}, "sum_error": float}.
Needs the Prolink Grab venv ("~/Library/Application Support/Prolink Grab/venv": torch, soundfile) and the DrumSep checkpoint that
tools/setup_stems.sh in the Prolink Sync repo downloads. Input must be 44.1 kHz (DrumSep's rate).
"""
import argparse, json, os, sys

REPO_DEVICE = os.environ.get("PROLINK_DEVICE_DIR", os.path.expanduser("~/Documents/Claude/Ableton CUE/device"))
CKPT = os.environ.get("DRUMSEP_CKPT", os.path.expanduser(
    "~/Library/Application Support/Prolink Grab/drumsep/MDX23C-DrumSep-aufr33-jarredou.ckpt"))
TOP_GROUPS = {"hats": ["hh", "ride", "crash", "kick", "toms"], "snare_clap": ["snare"]}


def parse_groups(specs):
    groups = {}
    for s in specs:
        name, _, insts = s.partition("=")
        groups[name] = [i.strip() for i in insts.split(",") if i.strip()]
    return groups


def grab_mode(a, ds):
    import numpy as np, soundfile as sf, torch
    x, sr = sf.read(a.loop, dtype="float32", always_2d=True)
    if sr != 44100:
        sys.exit("DrumSep needs 44.1 kHz audio, this file is %d Hz" % sr)
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    kick, rest, hits = ds.split_kick(ds.load_model(CKPT, dev), dev, torch.from_numpy(x.T.copy()))
    os.makedirs(a.out_dir, exist_ok=True)
    tag = os.path.splitext(os.path.basename(a.loop))[0]
    files, rms = {}, {}
    for g, y in (("kick", kick), ("rest", rest)):
        files[g] = os.path.join(a.out_dir, "%s - %s.wav" % (tag, g))
        sf.write(files[g], y, sr, subtype="PCM_24"); rms[g] = round(float(np.sqrt((y ** 2).mean())), 5)
    print(json.dumps({"mode": "grab", "kick_hits": int(hits), "files": files, "rms": rms, "sum_error": float(np.abs(kick + rest - x).max())}))


def kick_template(x, sr):
    """Rebuild the kick from the loop's own hits: returns (kick, info) with kick shaped like x, or (None, info).

    A loop's kick is usually one sample repeated. Masking it out of the mix lets whatever lands on the same beat (a snare or
    clap) leak into it, so its top end swings from hit to hit. Instead: find the hits from the 40-200 Hz band, call a hit
    CLEAN when little 1-8 kHz energy sits on it (two clusters >= 6 dB apart, else all are clean), take the sample-aligned
    MEDIAN of the clean hits as the template, align every hit to it on the 30-90 Hz band (where nothing else lives) and
    fit its gain there, then lay the template back. A hit cut off by the loop start is handled by zero padding.
    Only the kick's own sound is kept: the median would also keep e.g. an off-beat open hat that follows every clean hit, so the
    template's top end (> 400 Hz) stops once the kick's click has decayed; its low end runs the whole window.
    """
    import numpy as np
    n = len(x)
    L, pre = int(0.40 * sr), int(0.004 * sr)
    pad = L
    xp = np.concatenate([np.zeros((pad, x.shape[1])), x, np.zeros((pad, x.shape[1]))])

    def band(v, lo, hi):
        X = np.fft.rfft(v, axis=0); f = np.fft.rfftfreq(len(v), 1 / sr)
        X[(f < lo) | (f >= hi)] = 0
        return np.fft.irfft(X, len(v), axis=0)

    m = xp.mean(1); low = band(m, 40, 200); vl = band(m, 30, 90); mid = band(m, 1000, 8000)
    hop = sr // 200
    env = np.array([np.abs(low[i:i + hop]).max() for i in range(0, len(low) - hop, hop)])
    coarse, last = [], -99
    for i, v in enumerate(env):
        if v > 0.3 * env.max() and i - last > 40:
            coarse.append(int(i / 200 * sr)); last = i
    coarse = [c for c in coarse if pad - int(0.05 * sr) <= c < pad + n]
    if len(coarse) < 3:
        return None, {"reason": "fewer than 3 kick hits"}
    E = np.array([10 * np.log10((mid[c:c + int(0.06 * sr)] ** 2).sum() + 1e-12) for c in coarse])
    o = np.argsort(E); gaps = np.diff(E[o]); g = int(np.argmax(gaps))
    clean = sorted(int(i) for i in o[:g + 1]) if gaps[g] >= 6 else list(range(len(coarse)))
    if len(clean) < 2:
        return None, {"reason": "fewer than 2 clean kick hits"}

    def start_of(c):
        a = c - int(0.03 * sr); seg = np.abs(low[a:c + int(0.03 * sr)])
        return a + int(np.argmax(seg > 0.2 * seg.max())) - pre

    S = {i: start_of(coarse[i]) for i in range(len(coarse))}

    def xalign(i, tb, rng):
        best, bv = S[i], -1e18
        for d in range(-rng, rng + 1):
            a = S[i] + d
            if a < 0 or a + L > len(vl):
                continue
            v = float(np.dot(vl[a:a + L], tb))
            if v > bv:
                bv, best = v, a
        return best

    tb = vl[S[clean[0]]:S[clean[0]] + L]
    for i in clean:
        S[i] = xalign(i, tb, int(0.003 * sr))
    T = np.median(np.stack([xp[S[i]:S[i] + L] for i in clean]), axis=0)
    for _ in range(2):
        tb = band(T, 30, 90).mean(1)
        for i in range(len(coarse)):
            S[i] = xalign(i, tb, int(0.002 * sr) if i in clean else int(0.010 * sr))
        T = np.median(np.stack([xp[S[i]:S[i] + L] for i in clean]), axis=0)
    # The median keeps anything that sits at the same spot after EVERY clean hit, e.g. an open hat on the off-beat. Keep only
    # what belongs to the kick: its low end (< 400 Hz) for the whole window, but its top end only until it has decayed
    # (first time its > 400 Hz envelope stays below 5% of its click for 20 ms, plus 10 ms); later top end goes to the hats.
    LF = 400
    T_lf, T_hf = band(T, 0, LF), band(T, LF, sr)
    h5 = sr // 200
    env_hf = np.array([np.abs(T_hf[i:i + h5]).max() for i in range(0, L - h5, h5)])
    pk = int(np.argmax(env_hf[:6])); click = env_hf[pk]
    cut = len(env_hf)
    for k in range(pk + 1, len(env_hf) - 3):
        if (env_hf[k:k + 4] < 0.05 * click).all():
            cut = k + 2; break                                          # 5 ms steps: +10 ms after the decay
    cut_s = min(L, cut * h5); f2 = int(0.015 * sr)
    w_hf = np.zeros(L); w_hf[:cut_s] = 1.0
    if cut_s < L:
        a0 = max(0, cut_s - f2); w_hf[a0:cut_s] = np.linspace(1, 0, cut_s - a0)
    fade = int(0.03 * sr); win = np.ones(L); win[-fade:] = np.linspace(1, 0, fade)
    T = T_lf + T_hf * w_hf[:, None]
    tb = band(T, 30, 90).mean(1)
    kick = np.zeros_like(xp)
    gains = []
    for i in range(len(coarse)):
        gn = float(np.dot(vl[S[i]:S[i] + L], tb) / np.dot(tb, tb)); gains.append(round(gn, 2))
        kick[S[i]:S[i] + L] += gn * T * win[:, None]
    info = {"hits": len(coarse), "clean": clean, "gains": gains, "top_end_kept_ms": round(cut_s / sr * 1000),
            "starts_s": [round((S[i] - pad) / sr, 4) for i in range(len(coarse))]}
    return kick[pad:pad + n].astype(x.dtype), info


def kit_mode(a, ds):
    """KICK, SNARE, HATS (open + closed together) from a full drum loop; the three add back up to the loop.

    1. KICK is rebuilt from the loop's own hits (kick_template): the median of the hits that have nothing else on them,
       laid back on every hit. A mask on the mix, or the GRAB kick step, lets a snare/clap on the same beat leak into the
       kick, so its top end swung ~20 dB from hit to hit. No repeatable kick found: it falls back to the GRAB kick step.
       rest = loop - kick.
    2. DrumSep runs again on the rest (kick gone), and ratio masks of the REST split it into SNARE (snare) and
       HATS (hh, ride, crash, toms, any kick leftover). snare + hats = rest exactly.
    3. Gate: the snare is only real near a snare hit. Hits are the broadband transients of the snare part
       whose tone is low (centroid < --snare-centroid, hats are ~7-8 kHz; loudness alone picked leaked hats); it is kept from 20 ms before a hit to --tail ms after (default 150) and whatever sits
       outside moves to the hats, with 10 ms fades, so the sum still holds.
    """
    import numpy as np, soundfile as sf, torch
    x, sr = sf.read(a.loop, dtype="float32", always_2d=True)
    if sr != 44100:
        sys.exit("DrumSep needs 44.1 kHz audio, this file is %d Hz" % sr)
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    model = ds.load_model(CKPT, dev)
    kick, kinfo = kick_template(x, sr)
    if kick is None:                                   # no repeatable kick found: fall back to the GRAB kick step
        kick, rest, hits = ds.split_kick(model, dev, torch.from_numpy(x.T.copy()))
        kick, rest = np.asarray(kick, dtype=np.float32), np.asarray(rest, dtype=np.float32)
        kinfo = {"fallback": "grab kick step", **kinfo}
    else:
        rest = (x - kick).astype(np.float32)
    restw = torch.from_numpy(rest.T.copy())
    stems = ds.demix(model, dev, restw)
    S = {k: stems[i] for i, k in enumerate(ds.INSTRUMENTS)}
    NF, HOP = 1024, 128
    win = torch.hann_window(NF)
    st = lambda t: torch.stft(t, NF, HOP, window=win, return_complex=True)
    R = st(restw)
    p_sn = st(S["snare"]).abs() ** 2
    p_ha = sum(st(S[i]).abs() ** 2 for i in ds.INSTRUMENTS if i != "snare")
    tot = p_sn + p_ha + 1e-12
    inv = lambda M: torch.istft(R * M, NF, HOP, window=win, length=restw.shape[1]).numpy().T.copy()
    snare, hats = inv(p_sn / tot), inv(p_ha / tot)
    # gate the snare to the neighbourhood of its hits. Candidates = broadband transients of the snare part; a candidate is a
    # real snare/clap hit only if its sound is low enough: the average frequency (spectral centroid) of its first 80 ms is
    # below --snare-centroid (backbeat claps/snares ~4-5 kHz, leaked hats ~7-8 kHz). Loudness alone picked leaked open hats.
    n = snare.shape[0]
    hop = sr // 200
    e = np.array([np.abs(snare[i:i + hop]).max() for i in range(0, n - hop, hop)])      # 5 ms peak envelope
    thr, last, cand = a.snare_thresh * e.max(), -10 ** 9, []
    for i in range(1, len(e) - 1):
        if e[i] > thr and e[i] >= e[i - 1] and e[i] >= e[i + 1] and i - last > 0.10 * 200:
            j = i
            while j > i - 6 and e[j - 1] > 0.2 * e[i]:
                j -= 1
            cand.append(j * hop); last = i
    onsets, centroids = [], {}
    mono = snare.mean(1)
    for t in cand:
        seg = mono[t:t + int(0.08 * sr)]
        if len(seg) < 64:
            continue
        sp = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))); f = np.fft.rfftfreq(len(seg), 1 / sr)
        c = float((sp * f).sum() / max(sp.sum(), 1e-12)); centroids[round(t / sr, 3)] = int(c)
        if c < a.snare_centroid:
            onsets.append(t)
    HOP = hop
    gate = np.zeros(n)
    for t in onsets:
        gate[max(0, t - int(0.02 * sr)):min(n, t + int(a.tail / 1000 * sr))] = 1.0
    fade = int(0.01 * sr); kern = np.hanning(2 * fade + 1); kern /= kern.sum()
    gate = np.convolve(np.pad(gate, fade, mode="edge"), kern, "same")[fade:-fade]
    snare_g, hats_g = snare * gate[:, None], hats + snare * (1 - gate[:, None])
    os.makedirs(a.out_dir, exist_ok=True)
    tag = os.path.splitext(os.path.basename(a.loop))[0]
    files, rms = {}, {}
    for g, y in (("KICK", kick), ("SNARE", snare_g), ("HATS", hats_g)):
        files[g] = os.path.join(a.out_dir, "%s - %s.wav" % (tag, g))
        # a part can exceed full scale (hats = loop - kick - snare); 24-bit would clip it and break the sum: write float then
        sf.write(files[g], y, sr, subtype="FLOAT" if float(np.abs(y).max()) >= 0.999 else "PCM_24"); rms[g] = round(float(np.sqrt((y ** 2).mean())), 5)
    print(json.dumps({"mode": "kit", "kick": kinfo, "snare_hits_s": [round(t / sr, 3) for t in onsets], "candidates_centroid_hz": centroids,
                      "files": files, "rms": rms, "sum_error": float(np.abs(kick + snare_g + hats_g - x).max())}))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("loop"); ap.add_argument("out_dir")
    ap.add_argument("--mode", choices=["grab", "top", "kit"], default="grab")
    ap.add_argument("--snare-thresh", type=float, default=0.25, help="kit mode: candidate snare hit = a broadband transient above this share of the snare part's peak")
    ap.add_argument("--snare-centroid", type=float, default=5200, help="kit mode: a candidate is a snare hit only if its average frequency (first 80 ms) is below this (Hz)")
    ap.add_argument("--tail", type=float, default=150, help="kit mode: ms the snare is kept after a hit (shorter than the gap to the next hat)")
    ap.add_argument("--group", action="append", help="NAME=inst,inst  (instruments: kick snare toms hh ride crash); repeat per output")
    a = ap.parse_args()
    sys.path.insert(0, REPO_DEVICE)
    import numpy as np, soundfile as sf, torch
    import drumsplit as ds

    if a.mode == "kit" and not a.group:
        return kit_mode(a, ds)
    groups = parse_groups(a.group) if a.group else (TOP_GROUPS if a.mode == "top" else None)
    if groups is None:
        return grab_mode(a, ds)
    used = [i for v in groups.values() for i in v]
    bad = [i for i in used if i not in ds.INSTRUMENTS]
    if bad or len(set(used)) != len(used):
        sys.exit("groups must use each of %s at most once (bad/duplicate: %s)" % (ds.INSTRUMENTS, bad or sorted({i for i in used if used.count(i) > 1})))
    missing = [i for i in ds.INSTRUMENTS if i not in used]
    if missing:                                         # anything not named goes with the last group, so the groups still sum to the loop
        groups[list(groups)[-1]] = groups[list(groups)[-1]] + missing

    x, sr = sf.read(a.loop, dtype="float32", always_2d=True)
    if sr != 44100:
        sys.exit("DrumSep needs 44.1 kHz audio, this file is %d Hz" % sr)
    wav = torch.from_numpy(x.T.copy())
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    stems = ds.demix(ds.load_model(CKPT, dev), dev, wav)
    S = {k: stems[i] for i, k in enumerate(ds.INSTRUMENTS)}
    NF, HOP = 1024, 128
    win = torch.hann_window(NF)
    st = lambda t: torch.stft(t, NF, HOP, window=win, return_complex=True)
    X = st(wav)
    power = {g: sum(st(S[i]).abs() ** 2 for i in insts) for g, insts in groups.items()}
    tot = sum(power.values()) + 1e-12
    os.makedirs(a.out_dir, exist_ok=True)
    tag = os.path.splitext(os.path.basename(a.loop))[0]
    files, rms, parts = {}, {}, []
    for g, p in power.items():
        y = torch.istft(X * (p / tot), NF, HOP, window=win, length=wav.shape[1]).numpy().T.copy()
        path = os.path.join(a.out_dir, "%s - %s.wav" % (tag, g))
        sf.write(path, y, sr, subtype="PCM_24")
        files[g] = path; rms[g] = round(float(np.sqrt((y ** 2).mean())), 5); parts.append(y)
    print(json.dumps({"mode": "top" if a.mode == "top" and not a.group else "custom", "files": files, "rms": rms, "sum_error": float(np.abs(sum(parts) - x).max())}))


if __name__ == "__main__":
    main()
