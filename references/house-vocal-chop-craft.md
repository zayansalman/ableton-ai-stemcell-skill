# House / Garage Vocal-Chop Craft — Knowledge Base for a MIDI-Pattern Generator

Research notes distilled into codeable rules for a piano-roll generator that plays chopped-vocal slices in genre-authentic ways. Two target engines: **MK mode** (one chop, sampler in Classic/transpose — MIDI note = pitch) and **Todd mode** (many slices, sampler in Slice — MIDI note = slice index).

**Confidence legend:** `[DOC]` = documented in an interview / primary source · `[CONV]` = established production convention across multiple tutorials · `[LORE]` = commonly claimed but not directly verified.

---

## 1. MK (Marc Kinchen) — the "dub" vocal-as-organ-stab

**What's documented.** `[DOC]` For his early Def Mix / Nightcrawlers dubs, MK chopped in an **Akai S1100**. His own account: *"I'd have to import each vocal stem… sample each one back into the Akai, put them each on a different key group and then get them ready to chop"* (Attack Magazine interview). The *Push the Feeling On* "Nocturnal Dub" / "Dub of Doom" (1992) famously **used only one verse** to build the whole remix, pairing the cut-up vocal with the **Korg M1 "House Organ"** preset (Attack; Line Noise; Grokipedia). Later he moved to Maschine for the same chop-and-map workflow (Attack; MusicRadar).

**The mechanism.** `[DOC/CONV]` The chop becomes a *playable pitched instrument*: mapping one syllable across the sampler keybed means each MIDI note transposes it. Loopmasters describes the modern equivalent directly — *"set the sampler to pitch across the keyboard so you can play that vowel sound at any note, and write a melody in the piano roll that fits your chord progression."* This confirms the mental model: **MK's pitched vocal stab = Ableton Simpler "Classic" mode (MIDI note = transpose)**. SFX Engine's summary of the Dub of Doom: *"MK sliced the vocal into tiny, rhythmic fragments, pitched them around, and locked them into a swung groove."*

**Sample choice.** `[CONV]` Short word/syllable with a **sustained vowel** ("aah", "ooh", "yeah") reads best as a one-shot organ-like stab (Loopmasters; Splice). Semantic meaning is irrelevant — the hook works through repetition, not lyrics (Line Noise).

**Rhythm.** `[CONV/LORE]` The classic house "organ stab on the offbeat" (the *'and'* of the beat) is the characteristic feel, but note it is genre convention rather than a specific MK quote — his actual dubs vary between driving on-beat and syncopated. Treat "offbeat + one syncopated ghost, sparse and heavily repeated over a 1–2 bar cell" as the target. `[LORE]`

---

## 2. Todd Edwards ("Todd the God") — micro-sampling mosaic

**What's documented.** `[DOC]` Edwards **codified microsampling**: *"taking miniscule samples and rearranging them to create an entirely new melody,"* pulling fragments from **many different source songs** rather than one (Wikipedia; TV Tropes). Process on records like *Saved My Life*: vocals *"chopped up, filtered, panned, pitched and re-arranged, before being quantised in his distinctive skippy style"* (NITELIFE). He *"slic[es] it up into tiny parts and re-constructs it into a staccato vocal melody, sometimes mutating it so there are no recognisable words."* For Daft Punk's *Face to Face* he prepped **70 samples** on a **zip disk via an Akai S6000** the night before (MusicTech; MusicRadar). He is *"very particular about wanting everything to be pitch perfect"* and pitches elements *"up really high… and down, over an octave"* (RBMA 2013 lecture; 909originals).

**The mechanism.** `[DOC/CONV]` Because each fragment is a **different sample** assigned to a **different key**, and they are sequenced into a dense melodic-rhythmic honeycomb, the correct mental model is **Ableton Simpler "Slice" mode (each MIDI note triggers a different slice)**. Confirmed as the right engine. Slice sizes being sub-1/8-note / near-grain length is `[LORE]` — described as "miniscule/tiny" but no exact duration is documented.

**Feel.** `[DOC/CONV]` Dense staccato mosaic over a **heavily swung four-to-the-floor / 2-step garage** groove; layered so fragments overlap into a shimmering texture.

---

## 3. General house / garage conventions

### Rhythm & swing `[CONV]`
- **Tempo:** deep/soulful house 118–125 BPM; UK/speed garage 125–135 BPM (Attack "Garage Shuffle" cites 120–125; MusicRadar UKG uses 127).
- **Swing:** apply **16th-note swing**. Tutorials converge on **54–62%** for vocals/hats — Attack "Garage Shuffle" 60–65%; NITELIFE vocal cuts ~60%; MusicRadar UKG 50–60%; MusicRadar retro house 50–56%. Push chops slightly *later* than the drums for the extra "skip." `[CONV]`
- **2-step drum bed** (context for chop placement): kick on **1** + an eighth after **3**; claps/snare on **2 & 4** with a ghost near the bar end; offbeat open hats (MusicRadar UKG; Attack).

**Concrete 16-step grids** (steps 1–16 = 16th notes; beats land on 1,5,9,13; offbeats/'ands' on 3,7,11,15):

```
Sparse MK-style offbeat stab (one chop, transposed to chord tones):
step:  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16
stab:  .  .  x  .  .  .  x  .  .  .  x  .  .  .  x  (.)   ← 'and' of each beat
ghost: .  .  .  .  .  .  .  .  .  .  .  x  .  .  .  .    ← one syncopated push
```

```
Busy Todd-style mosaic (many slices, ~10 hits/bar, swung):
step:  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16
hit:   x  .  x  x  .  x  .  x  x  .  x  .  x  x  .  x
```

### Pitch & scale `[DOC/CONV]`
- **Scales:** natural minor and **Dorian** dominate; minor pentatonic for hooks. Masters at Work "To Be In Love" sits in **F Dorian** (natural minor with a raised 6th) (Attack "Passing Notes").
- **Voicings:** deep/soulful house lives on **7th and 9th chords**, not bare triads — jazz/gospel colour (Attack; LANDR; Unison).
- **Documented progressions** (Attack): `Fm7 → AbMaj7 → Cm7` (MAW, F Dorian); `Am7 → Em7 → Dm7` (natural minor, descending 7th voice-lead). Also common: **i–VII–VI** and the gospel **bVI → bVII → i** lift; Dorian `Am7–D7` vamp.
- **Chops land on chord tones** (root/3rd/5th/7th) on strong steps; passing tones only as fast in-between fills. Stay diatonic to the key.

### Arrangement `[CONV]`
- **1–2 bar repeating cell**; keep bar 1, vary bar 2 (extra ghost, an octave lift, a dropped hit).
- **Call-and-response** between the chopped hook and space/drums.
- "**Hook in a bar**" — one memorable cell, heavily repeated, tension/release via 8- or 16-bar mutes and filter opens.

---

## 4. Practical MIDI-generation rules

### MK mode — one chop, Classic/transpose (MIDI note = pitch)
1. **Inputs:** key, mode (natural minor / Dorian), a 2–4 chord progression (default `i7 – VII7 – VI7` or MAW `i7 – III7 – v7` in Dorian).
2. **Pitch pool:** per active chord, allowed notes = its chord tones (root, 3, 5, 7, optional 9) within **one octave** (e.g. C3–C4). No note leaves the octave — organ-stab range.
3. **Rhythm:** place stabs on the **offbeats** (16th steps **3, 7, 11, 15** = the 'and' of beats 1–4) + **one** syncopated ghost (step 12 or 16). Not all four offbeats need fire — 2–3 per bar is sparser and more authentic.
4. **Note→pitch:** each stab takes the nearest chord tone to the previous stab (smooth voice-leading, small leaps). Short gate (~1/16, staccato).
5. **Swing:** quantise to 16th, swing **56–60%**; nudge the whole vocal lane a hair later than drums.
6. **Repetition:** generate a **1-bar cell**, repeat, then mutate bar 2 (drop one stab, or lift the last stab +1 chord tone). Change the pitch set when the chord changes so the *same* rhythmic stab tracks the harmony.

### Todd mode — many slices, Slice (MIDI note = slice index)
1. **Inputs:** N available slices (e.g. 8–24), key/scale, swing.
2. **Density:** **8–12 hits per bar** on a 16-step grid at **~58% swing**.
3. **Grid:** favour a busy syncopated mask (e.g. steps `1,3,4,6,8,9,11,13,14,16`); leave 1–2 deliberate gaps per beat so the groove breathes.
4. **Slice sequencing → melody:** map slice indices to an **ascending / arch contour** across the bar (rise over beats 1–2, apex mid-bar, fall over 3–4) so the mosaic implies a melodic line; keep chosen slices' pitches diatonic (pre-tune slices to scale, or transpose the triggering notes to chord tones).
5. **Micro-variation:** every repeat, swap 1–3 slice indices and re-roll one gap position — never a static loop.
6. **Layering:** optionally generate a **second lane** an octave up or offset by one 16th for the overlapping-honeycomb density; pan the two lanes.
7. **Pitch-perfect rule** `[DOC]`: reject any slice whose pitch falls outside the key — Todd's defining constraint is everything staying in tune.

---

## Sources
- Attack Magazine — MK interview: https://www.attackmagazine.com/features/interview/mk-marc-kinchen/3/
- Attack Magazine — "Garage Shuffle" (Beat Dissected): https://www.attackmagazine.com/technique/beat-dissected/garage-shuffle/
- Attack Magazine — "Passing Notes: Deep House Chords": https://www.attackmagazine.com/technique/passing-notes/passing-notes-deep-house-chords/
- Line Noise (Ben Cardew) — "10 songs to know MK": https://linenoise.substack.com/p/10-songs-to-know-mk-part-one
- MusicRadar — "How to make a UK garage beat": https://www.musicradar.com/how-to/uk-garage-tutorial
- MusicRadar — Marc "MK" Kinchen's essential studio lessons: https://www.musicradar.com/how-to/mark-mk-kinchens-10-essential-studio-lessons
- NITELIFE Audio — "Classic Techniques: UK Garage Vocal Cuts": https://nitelifeaudio.com/classic-techniques-uk-garage-vocal-cuts/
- Loopmasters — "How to create your own vocal chops": https://www.loopmasters.com/articles/4799-How-to-create-your-own-vocal-chops-
- SFX Engine — "A Modern Vocal Chops Tutorial": https://sfxengine.com/blog/vocal-chops-tutorial
- MusicTech — Todd Edwards / Daft Punk "Face to Face" 70 samples: https://musictech.com/news/music/daft-punk-face-to-face-todd-edwards-samples/
- MusicRadar — Daft Punk "Face to Face" samples / Todd Edwards: https://www.musicradar.com/news/daft-punk-face-to-face-samples
- Wikipedia — Todd Edwards: https://en.wikipedia.org/wiki/Todd_Edwards
- Red Bull Music Academy — Todd Edwards 2013 lecture: https://www.redbullmusicacademy.com/lectures/todd-edwards/
- 909originals — Todd Edwards interview (production style): https://909originals.com/2021/03/22/interview-todd-edwards-discusses-new-single-the-chant-whats-next-for-daft-punk-and-the-inspiration-behind-his-idiosyncratic-production-style/
- Native Instruments Blog — UK garage guide: https://blog.native-instruments.com/uk-garage-music/
