---
name: drum-rack-pad-tracks
description: Use when the user wants audio tracks that record individual Drum Rack pads (for example the Garage Kit): which pads need a track, how to route each pad's audio into its own track, and arming them for recording.
---

# Audio tracks for individual Drum Rack pads

The user's example (`909 Clap` after the `20-Garage Kit` track): an **audio track** with Audio From = the drum-rack's
track (`20-Garage Kit`) and channel **`<Rack> | <pad> | Post Mixer`** (Post Mixer, so the rack's effect bus,
e.g. Core Drum Master, is included), monitoring **In**. Copy that exactly. Use `get_track_input_routing`
(shows every option) and `set_track_input_routing` (set the type first, then the channel).

## Which pads need a track: unmuted AND actually played
A pad needs a track only if it is **unmuted and receives MIDI notes**. Muted pads make no sound even when notes exist
(the Garage Kit's most-played pad, the Tamb, is muted). Unplayed pads need nothing.
1. **Mute state:** Live's API doesn't show it. Have the user save, then read the saved `.als` (the set currently
   open is in Live's log under "Loading document"; the user may have saved under another name, check file times).
   In the file, a pad (`DrumGroupDevice/Branches/*`) is **muted when `MixerDevice/Speaker/Manual` is `false`**.
2. **Which notes are played:** read the rack track's clips (session and arrangement) with
   `get_session_snapshot(include_notes=true)`; count unmuted notes per pitch.
3. **Pad to note:** the file stores `BranchInfo/ReceivingNote` as **128 minus the real MIDI note** (stored 92 = note 36).
   Never compare the stored number to clip pitches directly.
4. Pad order in the file equals the order of the routing options in Live.

## Gotchas
- Two pads can share a name (Garage Kit has two `Tom High DMX Tonic`). Live lists them identically and a name
  match always picks the first, so the second can't be targeted by name. Tell the user to pick it by hand, and don't
  arm a track with no route (set it to No Input). Neither was played, so it didn't matter there.
- Arm the pad tracks and leave everything else unarmed; verify with `get_track_meters`. After recording, disarm and set
  Auto monitoring so the takes play instead of the live input.
- Don't create tracks for pads that won't be recorded; if some were made, delete only tracks you created that are empty,
  with names checked (`delete_tracks` verifies names and refuses on a mismatch).

## Garage Kit (the user's project "F min GLide", 2026-10-13)
Played in `Garage Beat 130 bpm`: notes 36 Kick TL, 37 Rim GR, 38 Snare Jethro, 39 Snare Trap, 40 Snare Room (all muted),
42 Hihat Closed Sharp Garage, 44 Hihat Closed Stick Garage, 46 Hihat Closed Beyond (unmuted), 50 Tamb Chop (muted),
52 909 Clap (unmuted). Tracks made: 909 Clap (user's), Hihat Closed Beyond, Hihat Closed Stick Garage, Hihat Closed Sharp Garage.
