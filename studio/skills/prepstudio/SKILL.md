---
name: prepstudio
description: Use when the user says "prepstudio", is going into studio mode, or wants the master and any external outputs put back on 1/2. Reads every track, return and Main output in the open Live set and moves any Ext. Out that is not on 1/2 (usually 5/6 from working out of the DJM) to 1/2.
---

# prepstudio: external outs back to 1/2

The user usually works out of the DJM as an aggregated audio device, so the **Main (master) output is often on Ext. Out 5/6**. In studio mode they want it on **Ext. Out 1/2**. The same goes for any track whose output is an external out (for example the resample track): make it **1/2**.

## 1. Read everything
MCP tool `get_output_routings` returns every track, return and the Main as `{scope, index, name, type, channel}`. Only look at rows where `type` is `Ext. Out` (and the Main); the list is long. Re-read each time, indices shift.

## 2. Fix
- **Main** (`scope:"master"`): must be `type "Ext. Out"`, `channel "1/2"`. If it is anything else on Ext. Out (5/6, 3/4...), set it to 1/2. If the Main is not on an Ext. Out at all (e.g. a different device), report it and ask; do not force it.
- **Any track or return with `type "Ext. Out"`** and a channel other than `1/2`: set channel to `1/2`. Include tracks that are armed, sounding, in the Arrangement, or the resample track.
- **Leave alone** anything routed to Main, a group, Sends Only, or another track. Those are normal.
- Set with MCP tool `set_track_output_routing(scope="master"|"track"|"return", index=N, type="Ext. Out", channel="1/2")`. Names are exact; a wrong name returns the valid choices and changes nothing.
- Pass `type` only if it is not already `Ext. Out`; otherwise pass just `channel`, so the device choice is not touched.

## 3. Report
List each change as "name: old -> 1/2" and the final Main output. If nothing needed changing, say so.

## Notes
- The output-routing commands were verified read-only on 2026-10-18 (the Main was on Ext. Out 1/2); setting has not been run yet. If `get_output_routings` says "unknown command" the Remote Script predates it: the user restarts Live, or sets Live's output by hand (Main output dropdown at the bottom right of the mixer).
- If the aggregated device has no 1/2 pair under `available_output_routing_channels`, report the valid channels instead of guessing.
- This skill is the opposite of the DJM/live setup: when the user says they are going back to the DJM, ask before moving anything to 5/6.
