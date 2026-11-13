---
name: arm-inputs
description: Use when the user says to arm their inputs, arm what is playing, or record-arm everything with incoming audio or MIDI. Finds sounding tracks and playing clips in the open Live set and arms them. Moving clips to Arrangement is the separate `arrangement` skill.
---

# Arm inputs

Goal: the user can see everything that is sounding in one place. Work from the **open set**, not the template. Never trust track indices (they shift when a track is inserted) or names; re-read every time and arm **by name**.

## 1. Find what is sounding
- Call MCP tool `sample_track_meters` (15 samples, 0.3 s apart, while the set plays). It returns only tracks that sounded above 0.01, plus every armed track and every track with a playing Session clip, with `peak`, `arm`, `monitoring`, `input`, `group`, `is_group`, `playing_slot_index`. Re-read each time; indices shift.
- Sounding = peak above 0.01 on an ordinary track.
- Also take every track with a **playing clip** (`playing_slot_index >= 0`), even if it is silent right now.
- Count **MIDI sources** too: instrument MIDI tracks show a level; plain MIDI tracks (for example `Freak Midi IN`) show nothing, so only arm those when the user says they are receiving.
- **Drums are intermittent**: a single hit can fall between samples, so a pad track can read 0 while the kit is playing. Judge by the **group**: if the `Maschine Drums` group (or any group) peaks above 0.01, arm **all its audio children** (Kick, Snare, Perc, Hat, Break, Shaker), not only the ones that happened to read above 0. Maschine Drums is NOT excluded; on 2026-10-18 they were all missed because only per-track peaks were used.
- Dyad: when a Dyad MIDI track sounds, also arm its audio outs (Flerp: Low, Top; melodic: the two Audio 3 tracks), even if they read silent.

## 2. Resample track
- A resample track is any audio track whose input is **Resampling**. Do not match on the name (the user's was once a typo, "WHoel Resample", now "Whole Resample"; names change).
- Make sure at least one is armed. If there are several, arming one is enough. If none exists, tell the user.
- Also arm `Dub Return` (the B-Retur capture) when it exists; see the `retur` skill.

## 3. Skip
- `Korg Out`: not a track the user records.
- Groups and returns (cannot be armed); the B return is covered by its capture track.
- Do not arm a track only because a clip plays on it **if the user says it is a playback loop**, such as the Rekordbox Loops children, unless the user asked for playing clips (see below).

## 4. Arm, monitoring, automation
- `set_track_arm` by index looked up from the fresh list. Retry once on a timeout.
- Leave monitoring alone, except `Freak Midi IN`: arm it with monitoring **Off**.
- **Automation arm: turn it ON** (the user confirmed 2026-10-18; earlier "keep it off" is superseded): MCP tool `set_automation_arm(arm=true)`. If it errors with an unknown command, the Remote Script predates it: tell the user to restart Live, or press the Automation Arm button themselves.
- After arming, re-read meters and report the armed list.

## 5. Arrangement
Moving playing clips into Arrangement is a separate job: use the `arrangement` skill. This skill only arms.
