# Dance-Music Gear Fingerprints

*A fingerprint reference for identifying the drum-machine and synth-preset sources behind dance-music tracks from measured audio evidence. Built for the `/dissect` workflow, where song-dissect extracts per-hit slices and computes spectral features + CLAP zero-shot character hints.*

Last compiled: 2026-07-13.

---

## Read this first — the epistemics

**Audio-based gear ID is INFERENCE, never proof.** There are three evidence types, in ascending order of trust:

1. **CLAP zero-shot "character hints"** — a neural model scoring a slice against text labels ("909 kick", "808 kick"). These are *hint-grade*. CLAP was trained on loose web audio-text pairs and routinely calls anything punchy-and-electronic a "909". Treat a high CLAP score as a weak prior, never a verdict.
2. **Spectral / MIR features** — real DSP measured off the actual samples: spectral centroid (Hz, ~brightness), low-band energy ratio (<120 Hz), spectral flatness (0 = pure tone, 1 = white noise), decay/duration (ms), transient character. This is objective and reliable *about the sound*, though not about the box that made it.
3. **Genre / provenance context** — who made the record, when, on what label, in what scene. Narrows the plausible gear set but never uniquely determines it.

The honest output of a gear ID is a **best-guess source + a confidence tier**, not a fact. Confidence tiers used throughout:

- **Documented** — a citable interview/liner-note/database confirms the specific gear on the specific record.
- **Strong-inference** — spectral evidence + genre convention converge hard on one source; no citation for the exact record.
- **Ambiguous** — evidence is mixed, band-limited, or consistent with several sources.

Two failure modes to guard against: (a) taking CLAP labels literally; (b) attributing scene-level conventions to a specific artist who may have worked differently (e.g. Blaze = played/soulful, *not* the SP-1200 sample-chop wing of the same NJ/NYC scene).

---

## How to identify a drum machine from measured evidence

song-dissect gives you, per hit: `centroid_hz`, `lowband_ratio` (share of energy <120 Hz), `flatness` (spectral flatness), `decay_ms`/duration, and CLAP hints. Map them like this:

### Kick decision guide

| Observed pattern | Most likely source class | Why |
|---|---|---|
| Very high lowband% (>80%) + near-zero flatness (<0.01) + long decay (>500 ms) + minimal/no click transient | **808-style pure sine sub** | Bridged-T sine → LPF → VCA; ~50–60 Hz fundamental, no beater click. Cleanest single discriminator. |
| Strong sub body + **elevated centroid / bright HF transient** (bimodal FFT) + shorter decay (~150–400 ms) | **909-style analog kick** | Pitch-envelope beater click sits on top of the sub → whole-slice FFT shows both a low fundamental *and* a raised centroid. |
| Realistic body + 8-bit quantization floor + acoustic transient/formants | **Sampled real-drum machine** (LinnDrum/LM-1, Oberheim DMX, TR-707) | Sampled acoustic drums carry body/formant content no synth voice produces. |
| Source-dependent timbre + heavy aliasing/grit + broadband crunch, HF ceiling ~13 kHz | **12-bit sampler** (SP-1200 / MPC60) | The *machine* is the sound; aliasing + quantization dirt is the fingerprint. |
| Small dry thud, low sub, short decay | **TR-606 / CR-78 / small analog boxes** | Budget analog voices; little low-end extension. |

### Other voices

- **Sub-only, flatness ≈ 0, decay long** on a hit labelled "perc" → probably a tonal/tuned percussion or a second layered sub, not a real perc.
- **Perc/clap:** centroid ~4–6 kHz, ~1% energy <120 Hz, moderate decay → noise-burst clap or hand-percussion. 909 clap = dry three-peak envelope; 808 clap = wetter/reverberant tail; LinnDrum/DMX clap = sampled real hands (that specific 80s clap).
- **Hats:** centroid >7 kHz, bright. 909 hats/ride = 6-bit sampled cymbals with quantization grit above ~8 kHz; 808 hats = six square-wave oscillators, sizzly/synthetic; 606 hats = thin sizzly electro; sampled machines = band-limited real hats.
- **Pitch-glide in the spectrogram** (descending fundamental) → Simmons SDS-V toms; no acoustic/sampled machine sweeps pitch like that.

### Caveats that dominate in practice

- **Slice contamination.** A "kick" slice that shows a surprisingly high centroid/rolloff often contains bleed from a hat or the transient of the next hit. Read centroid *together with* lowband% — a genuine 808/909 kick keeps ~90% energy <120 Hz regardless of what the centroid says.
- **Processing masks the source.** EQ, saturation, sampling-off-vinyl, and layering all move these numbers. Layered kicks (sub sample + click sample) mimic a 909's bimodal signature without being a 909.
- **CLAP's 808/909 axis is really a "sub vs. click" axis.** A high 909 score just means "has a click / is punchy-electronic." Confirm with lowband% + flatness + decay before believing it.

---

## Drum machines

*Each entry separates **sourced** fact (spec/synthesis) from **consensus/lore** (production wisdom). Spectral descriptors use terms an MIR tool computes.*

### Roland TR-909 (1983)

**Engine — hybrid.** Kick, snare, toms, rimshot, clap are **analog**; hi-hats, crash, ride are **6-bit digital samples** (cymbals recorded by Atsushi Hoshiai to reel-to-reel via a Sony C-38 mic on Paiste/Zildjian hats). Kick circuit by Tadao Kikumoto. *(sourced)*

- **Kick** — analog with a **pitch-modulation envelope**: pitch snaps high at the transient then drops to the fundamental → punchy beater **click**. Front-panel *Tune* sets the *decay of that pitch envelope* (CW = hard/thumpy, CCW = round/hollow). Shorter decay, more midrange than an 808. *(sourced)*
- **Snare** — analog noise + tone; thick, tunable. Clap and snare share one noise generator → subtle phasing when both fire. *(sourced)*
- **Clap** — digital-noise burst, **three-peak (T-T-T) envelope**, dry diffuse tail. *(sourced)*
- **Hats/ride/crash** — bright metallic 6-bit samples; long sizzly open hat and splashy ride are house/techno signatures. *(sourced)*

**Tell it apart.** *Ear:* tight punchy kick with audible click, crisp bright metallic hats/ride, thick snare, dry clap — "driving/aggressive" where the 808 "floats." *DSP:* kick is **bimodal** (strong sub **plus** raised HF transient → low fundamental + elevated centroid); decay ~150–400 ms; hats carry 6-bit grit above ~8 kHz.

**Defines:** Chicago house, Detroit techno, acid, trance, hard techno — the definitional 4/4 club machine.

Sources: [Wikipedia: TR-909](https://en.wikipedia.org/wiki/Roland_TR-909) · [Attack Magazine — Hoshiai](https://www.attackmagazine.com/features/interview/atsushi-hoshiai-the-man-behind-the-tr-909/) · [LearnMusicProduction](https://learnmusicproduction.substack.com/p/classic-drum-machines-the-tr-909)

### Roland TR-808 (1980)

**Engine — fully analog** subtractive/bridged-T synthesis; no samples. *(sourced)*

- **Kick** — bridged-T sine osc → LPF → VCA. *Decay* lengthens a long pure **sub boom**, fundamental ~**50–60 Hz**, minimal attack. Pitched/sustained, this becomes the modern trap "808 bass." *(sourced; trap usage = lore)*
- **Snare** — noise + tuned tone; thin, papery. *(sourced)*
- **Clap** — all-analog, notably **wetter/reverberant** tail than digital clones. *(sourced)*
- **Hats/cymbal** — six square-wave oscillators; sizzly, unmistakably synthetic. **Cowbell** (two of the six oscs) and congas are cult favorites. *(sourced)*

**Tell it apart.** *Ear:* long booming sub kick with no click, papery snare, sizzly synthetic hats, that cowbell — "boomy" not "punchy." *DSP:* kick has **>80% energy <120 Hz**, **very low flatness** (near-pure sine, low centroid), **long decay** (can exceed ~1 s), minimal onset. Cleanest single discriminator vs. the 909.

**Defines:** hip-hop, electro, Miami bass, early Detroit techno, modern trap. Landmarks: "Planet Rock" (1982), "Sexual Healing."

Sources: [Wikipedia: TR-808](https://en.wikipedia.org/wiki/Roland_TR-808) · [SOS — Snare Synthesis](https://www.soundonsound.com/techniques/practical-snare-drum-synthesis) · [Vintage Synth: TR-808](https://www.vintagesynth.com/roland/tr-808) · [MusicRadar — the 808 kick](https://www.musicradar.com/news/what-is-the-808-kick-and-why-do-we-all-still-love-it)

### Roland TR-707 (1985)

**Engine — fully PCM-sampled** (first all-sampled Roland). ~25 kHz playback, 8-bit drums / 6-bit crash & ride. Non-decaying waveforms + downstream **analog VCA** decay → clean tails. TR-727 = Latin percussion sibling. *(sourced)*

Two kicks, two snares, three toms, rimshot, cowbell, clap, crash, ride, hats — **clean, dry, thin, "80s digital."** *DSP:* steep band-limiting (HF ceiling ~12 kHz), 8-bit floor on sustained voices, but artificially clean decay tails; little sub extension.

**Defines:** mid-80s freestyle, early house/techno, synthpop.

Sources: [Wikipedia: TR-707](https://en.wikipedia.org/wiki/Roland_TR-707) · [Vintage Synth: TR-707](https://www.vintagesynth.com/roland/tr-707)

### Roland TR-606 "Drumatix" (1981)

**Engine — fully analog**, budget sibling to the TB-303. Kick, snare, two toms, cymbal, closed/open hat. *(sourced)* Small tight kick (little sub), snappy thin snare, and standout **bright sizzly "electro" hi-hats**. *DSP:* low sub energy, high flatness/centroid on metallic voices, short decays — reads "small and gritty."

**Defines:** acid house/techno, electro, IDM (Aphex Twin, Autechre), often paired with a 303.

Sources: [Wikipedia: TR-606](https://en.wikipedia.org/wiki/Roland_TR-606) · [Vintage Synth: TR-606](https://www.vintagesynth.com/roland/tr-606)

### Linn LM-1 (1980) / LinnDrum LM-2 (1982)

**Engine — PCM samples of real acoustic drums** (LM-1 = first sampling drum machine). LM-1: twelve **8-bit** samples @ ~28 kHz, no cymbals; claps recorded by Tom Petty & the Heartbreakers. LinnDrum: 15 sounds @ ~35 kHz, adds crash/ride. *(sourced)* Punchy real-drum body with lo-fi 8-bit character; the clap/percussion are the most-sampled elements. *DSP:* 8-bit quantization floor, HF ceiling ~14–17 kHz, realistic transients/formants, mild aliasing on pitched voices.

**Defines:** 80s synthpop, new wave, R&B, the Prince/Minneapolis sound.

Sources: [Wikipedia: Linn LM-1](https://en.wikipedia.org/wiki/Linn_LM-1) · [Wikipedia: LinnDrum](https://en.wikipedia.org/wiki/LinnDrum)

### Oberheim DMX (1980–81)

**Engine — 8-bit PCM** of real drums with **µ-law companding** (~12-bit effective range); per-voice tuning + swing. *(sourced)* Chest-thumping round kick, **cracking/sharp snare** (harder than LinnDrum or 808), punchy realistic hats. *DSP:* µ-law nonlinear noise floor (quieter tails noisier), realistic body/transients, HF band-limiting, midrange punch.

**Defines:** early/golden-era hip-hop and 80s electro-pop — Run-DMC, "Blue Monday," "Rockit," Madonna "Holiday."

Sources: [Wikipedia: Oberheim DMX](https://en.wikipedia.org/wiki/Oberheim_DMX) · [Vintage Synth: DMX](https://www.vintagesynth.com/oberheim/dmx)

### E-mu SP-1200 (1987)

**Engine — 12-bit sampler/sequencer** (Dave Rossum). 26.04 kHz, ~10 s RAM in four 2.5 s banks, analog SSM2044 filters, **drop-sample (non-interpolating) pitch-shift**. *(sourced)* No built-in kit — **the machine is the sound**: anything run through it gets gritty/crunchy/aliased. Classic technique: pitch a break down to fit the short RAM → grittier playback (the boom-bap aesthetic). *DSP:* strong **aliasing** (inharmonic partials above ~13 kHz, worse when pitched), 12-bit quantization noise, SSM2044 HF rolloff. Distinguish from MPC: SP-1200 is grittier/more aliased at fixed 26 kHz.

**Defines:** 90s boom-bap (Pete Rock, RZA, Premier) and sample-based house.

Sources: [Wikipedia: SP-1200](https://en.wikipedia.org/wiki/E-mu_SP-1200) · [Vintage Synth: SP-1200](https://www.vintagesynth.com/e-mu/sp-1200) · [LANDR](https://blog.landr.com/sp-1200/)

### Akai MPC60 (1988) / MPC3000 (1994)

**Engine — sampler + sequencer**, co-designed by **Roger Linn**. MPC60: 12-bit / 40 kHz; MPC3000: 16-bit / 44.1 kHz. *(sourced)* Character = **machine + feel**: MPC60 adds gentle 12-bit warmth (cleaner/fuller than SP-1200 — higher rate, interpolating); MPC3000 is clean 16-bit. **The swing** — Linn's implementation delays the second 16th within each 8th — is the most-copied trait. *DSP:* MPC60 mild 12-bit quantization, far less aliasing than SP-1200; MPC3000 near-transparent; a measurable delayed-offbeat microtiming signature.

**Defines:** boom-bap and 90s+ sample-based hip-hop, neo-soul.

Sources: [Wikipedia: Akai MPC](https://en.wikipedia.org/wiki/Akai_MPC) · [Attack Magazine — Roger Linn on Swing](https://www.attackmagazine.com/features/interview/roger-linn-swing-groove-magic-mpc-timing/) · [Vintage Synth: MPC60](https://www.vintagesynth.com/akai/mpc60)

### Roland CR-78 "CompuRhythm" (1978)

**Engine — fully analog**, first microprocessor Roland rhythm box (user-programmable via WS-1). 14 analog voices incl. a ring-modulated **"metal beat."** *(sourced)* Sounds **soft, warm, mellow, toy-like** — nothing hits hard. *DSP:* low output/soft transients, limited HF, low sub; noise percussion high-flatness, tonal voices very-low-flatness.

**Defines:** late-70s/early-80s pop, proto-synthpop, ambient. Definitive: Phil Collins "In the Air Tonight" (slowed Disco 2 preset).

Sources: [Wikipedia: CR-78](https://en.wikipedia.org/wiki/Roland_CR-78) · [Vintage Synth: CR-78](https://www.vintagesynth.com/roland/cr-78)

### Simmons SDS-V / SDS5 (1981)

**Engine — analog drum synthesizer** (first viable electronic kit; Burgess & Simmons). Voice cards: pitched oscillator + noise, SSM/Curtis filters; hexagonal pads. *(sourced)* Signature = **toms with a downward pitch-sweep envelope** (the "dooo/pew-pew"), huge oscillator kick, cutting snare. *DSP:* toms show a clear **descending fundamental in the spectrogram** — a pitch glide no acoustic/sampled machine produces. The single cleanest fingerprint.

**Defines:** 80s rock/new-wave/pop — Duran Duran, Prince, Genesis, Rush.

Sources: [Wikipedia: Simmons SDS-V](https://en.wikipedia.org/wiki/Simmons_SDS-V) · [Simmons — History](https://simmonsdrums.net/history)

### Quick discriminator cheat-sheet

| Machine | Synthesis | Kick fingerprint | Cleanest "tell" |
|---|---|---|---|
| TR-909 | analog + 6-bit cymbals | punchy, click transient, short decay | sub **+** bright attack (bimodal FFT); metallic sampled hats/ride |
| TR-808 | fully analog | long pure-sine sub ~50–60 Hz, no click | >80% <120 Hz, very low flatness, long decay |
| TR-707 | 8-bit PCM (6-bit cymbals) | thin, clean, dry | clean tails (analog-VCA decay) + band-limited |
| TR-606 | fully analog | small dry thud | sizzly electro hats, low sub |
| LinnDrum/LM-1 | 8-bit PCM real drums | real body, lo-fi | acoustic transients + 8-bit floor; that clap |
| Oberheim DMX | 8-bit µ-law PCM | round, thumping | cracking snare, µ-law noise floor, punchy mids |
| SP-1200 | 12-bit / 26 kHz sampler | (source-dependent) | heavy aliasing + crunch, SSM2044 rolloff |
| MPC60 / 3000 | 12-bit / 16-bit sampler | (source-dependent) | the **swing** (delayed 2nd 16th) + chops; cleaner than SP |
| CR-78 | fully analog | soft warm thud | low-level, mellow, metal-beat buzz |
| Simmons SDS-V | analog drum synth | huge oscillator sub | **downward pitch-sweep** toms in spectrogram |

---

## Synth presets

*Iconic factory presets that defined dance music (house, garage, deep/soulful house, techno, trance, Eurodance, ~late-80s–2000s). Program numbers use the factory "Internal" bank (I-prefix); **numbering shifts across ROM cards/expansions — treat exact indices as canonical-but-not-universal.** Verified-vs-lore flags preserved.*

### Korg M1 (1988) — the ROMpler that built house

The single most important dance workstation. Two presets carry almost the entire house canon.

- **I01 "Piano 16" — the house piano stab.** Bright, percussive, slightly tinny sampled piano with fast attack; cuts as a stab. *Verified records:* Black Box "Ride on Time" (1989), Snap! "Rhythm Is a Dancer" (1992), CeCe Peniston "Finally" (1991), Londonbeat, Madonna "Vogue" (1990), Beyoncé "Break My Soul" (2022, layered with Organ 2). **Note:** "Ride on Time" *piano riff* is M1 Piano 16 (verified); the *vocal* is a separate Loleatta Holloway "Love Sensation" sample — **do not attribute the vocal to the M1.** *(sourced)*
- **I17 "Organ 2" — the house organ bassline.** Punchy percussive-organ single-cycle tone played as a **monophonic bassline in the low register** — that low-played Organ 2 *is* the "M1 organ bass." *Verified:* Robin S "Show Me Love" (1993 re-release) is literally factory Organ 2 played low; Crystal Waters "Gypsy Woman" (1991); Nightcrawlers "Push the Feeling On" (1992). **Correction to lore:** the widely-shared "Vogue = Organ 2" claim is **commonly claimed, unverified** — Vogue's stab is Piano 16. *(sourced)*
- **I00 "Universe" — the pad.** Lush choir/synth pad, the first program on power-up. Verified on Queen "Don't Try So Hard" (1991); dance use is texture/breakdown, specific anthem attributions **thin/unverified.**
- **Secondary house layers:** I62 Tenor Sax, I69 FingerSnap, I19 Pole (per MusicRadar). "Fretless"/"Brass" as dance signatures = **commonly claimed, unverified.**

**So-what:** for a house doc the M1 collapses to two presets (I01, I17); everything else is secondary.

Sources: [SonicState](https://sonicstate.com/news/2024/07/22/korg-m1-famous-songs-sounds/) · [MusicRadar — Show Me Love organ](https://www.musicradar.com/how-to/classic-house-organ-robin-s-show-me-love) · [ProducerStack](https://producerstack.com/blogs/the-stack/the-m1-piano-16-the-sound-that-built-house-music)

### Korg Trinity (1995) / Triton (1999)

Triton was a best-seller that "shaped the 2000s." Dance fingerprint = the **EXB-PCM09 "Trance Attack"** expansion (trance leads, saw stabs, supersaw pads, gate arps), later in Triton Extreme (2004) — a preset *set*, not a named single. Record-specific attributions **not cleanly verifiable** — general-use.

Sources: [Wikipedia: Korg Triton](https://en.wikipedia.org/wiki/Korg_Triton) · [zZounds EXB-PCM09](https://www.zzounds.com/item--KOREXBPCM09)

### Roland Juno-60 (1982) / Juno-106 (1984)

Single-DCO analog poly; the **BBD stereo chorus** is the identity (instant lush width, hollow PWM basses/pads). *Verified (Juno-60):* Mr. Fingers (Larry Heard) "Can You Feel It" (1986) = Juno-60 + TR-909 only — foundational deep-/acid-house. Junos are a **character** (chorus + hollow bass), not a numbered ROM anthem.

Sources: [Roland Articles](https://articles.roland.com/can-you-feel-it-mr-fingers/) · [Wikipedia](https://en.wikipedia.org/wiki/Can_You_Feel_It_(Larry_Heard_song))

### Roland D-50 (1987) — LA-synthesis (Persing/Scott presets)

- **"Fantasia"** — shimmering bell/choir/pad hybrid, the defining D-50 sound (Bangles "Hazy Shade of Winter"; New Order "Vanishing Point").
- **"Pizzagogo"** — plucked string; Enya "Orinoco Flow" (1988).
- **"Digital Native Dance"** — bright ethnic-percussive sequence; on MJ *Bad* = **commonly claimed, weakly verified** (timing).
- **Reality-check:** D-50 is a **late-80s pop/synth-pop/new-age** signature; "D-50 as a rave staple" is **unverified.**

Sources: [Wikipedia: D-50](https://en.wikipedia.org/wiki/Roland_D-50)

### Roland Alpha Juno / MKS-50 (1985) — the "Hoover"

Factory patch **"What The"** by **Eric Persing** ("as a joke") — the "Hoover"/"Mentasm": detuned PWM-**sawtooth** swarm with a vacuum-cleaner sweep. Slot inconsistently reported → **preset number unverified**; name/origin verified. *Verified first appearances (1991):* Second Phase "Mentasm," Human Resource "Dominator," Prodigy "Charly." **Key correction:** it's an Alpha Juno patch, **not** a JD-800/JV patch.

**Defines:** rave, hardcore, gabber, trance, hard house, jungle stabs.

Sources: [Wikipedia: Hoover sound](https://en.wikipedia.org/wiki/Hoover_sound) · [Wikipedia: Alpha Juno](https://en.wikipedia.org/wiki/Roland_Alpha_Juno)

### Roland JD-800 (1991) / JV-1080 (1994) / JV-2080 (1997)

JD-800 = evolving pads / hollow textures / bell stabs (a **texture** signature, not a one-preset anthem). JV-1080/2080 = ubiquitous 90s trance/Eurodance rack, but **no single record-defining named preset** — flag "the JV trance patch" as **unverified.** **Myth-bust:** Robert Miles "Children" was written on a **Kurzweil K2000**, not the JV-1080.

Sources: [Roland Articles: JD-800](https://articles.roland.com/listening-guide-sounds-of-the-jd-800/) · [Vintage Synth: JV-1080](https://www.vintagesynth.com/roland/jv-1080) · [Wikipedia: Children](https://en.wikipedia.org/wiki/Children_(composition))

### E-mu Proteus family (1989–2002)

Vintage Keys (1993) = workhorse vintage-emulation ROMpler, no signature dance record verified. **Orbit "The Dance Planet" (1996)** = the explicitly techno/dance-targeted module (analog-style multisamples, basses, leads). Specific anthem-to-preset mappings **not verifiable** — general-use.

Sources: [Wikipedia: E-mu Proteus](https://en.wikipedia.org/wiki/E-mu_Proteus)

### Ensoniq ASR-10 (1992)

16-bit sampling workstation with synth filters + resampling. Canon is **boom-bap hip-hop** (RZA/Wu-Tang, early Kanye), *not* house. Include as a **sampling backbone**; house-specific attributions are **weak** — flag.

Sources: [Reverb](https://reverb.com/news/history-of-ensoniq-samplers-mirage-eps-16-plus-asr-10)

### Yamaha DX7 (1983) — FM in dance

**"E.PIANO 1" (ROM 1A/11)** = the FM Rhodes; verified canon is power ballads/pop — its house/dance use as a preset is **commonly claimed, not verified.** The DX7's real dance contribution is its **punchy FM bass** in bouncy octaves (80s electro/freestyle), broadly documented but **not tied to a single named dance anthem.**

Sources: [Reverb Machine](https://reverbmachine.com/blog/exploring-the-yamaha-dx7-pt2/)

### Synth-preset verification ledger

| Claim | Status |
|---|---|
| Robin S "Show Me Love" bass = M1 **Organ 2 (I17)**, played low | **Verified** |
| M1 Piano 16 (I01) on Ride on Time / Rhythm Is a Dancer / Finally / Vogue | **Verified** |
| Madonna "Vogue" = M1 **Organ 2** | **Unverified / conflation** — it's Piano 16 |
| "Ride on Time" *vocal* = M1 | **False** — Loleatta Holloway sample; only piano is M1 |
| Hoover = Alpha Juno "What The" (Persing, PWM saw); Mentasm/Dominator/Charly 1991 | **Verified** (patch *number* unverified) |
| Mr Fingers "Can You Feel It" = Juno-60 + TR-909 | **Verified** |
| D-50 as a *techno/rave* staple | **Unverified** (pop/new-age canon) |
| Robert Miles "Children" = JV-1080 | **False** — Kurzweil K2000 |
| ASR-10 / DX7 E.PIANO 1 as *house* signatures | **Weak / unverified** |
| M1 program numbers (I01, I17, I00, …) | Verified vs SonicState + MusicRadar; **indices vary by ROM card** |

---

## Genre → typical kit (quick reference)

| Genre | Drum machine(s) | Signature synth / preset | Notes |
|---|---|---|---|
| **House (Chicago/piano/Italo)** | TR-909 (backbone), TR-808, some TR-707 | **Korg M1 Piano 16 (I01)**; Juno chorus | 909 is the definitional 4/4 club kick. |
| **Deep / soulful house (NJ/NYC garage)** | TR-909 programmed drums, often layered with samples; live/played feel in the soulful wing | **Korg M1 Organ 2 (I17)** bass, Fender Rhodes, gospel piano | Played/musical wing (Blaze) is distinct from the SP-1200 sample-chop wing (Todd Terry) of the *same* scene. |
| **Techno (Detroit/hard)** | TR-909 (+808 for early Detroit), TR-606 | Juno-60/106, JD-800 textures | 909 hats/ride + punchy kick define it. |
| **Trance / rave / hardcore** | TR-909 | **Alpha Juno "Hoover"**, JV-1080 workhorse, Triton "Trance Attack" | Hoover = Alpha Juno, not JV. |
| **Hip-hop / boom-bap / trap** | **SP-1200 / MPC** (boom-bap), **TR-808** (electro/trap sub-bass), Oberheim DMX / LinnDrum (golden-era) | ASR-10 sampling; DX7 FM bass (electro) | Sampler *is* the sound; 808 kick = the trap melodic sub. |
| **Garage (UK/US)** | TR-909, MPC swing + chops | M1 Organ 2, played bass | MPC swing/microtiming carries the groove. |
| **Disco / boogie (pre-drum-machine → early)** | live kit → LinnDrum/LM-1, CR-78, early 808 | Rhodes, DX7, M1 | Sampled disco loops feed later house via SP-1200/MPC. |

---

*Facts above are web-sourced (compiled 2026-07-13) per inline links; production-feel claims are marked "consensus/lore." Gear ID from audio remains inference — see the epistemics section.*
