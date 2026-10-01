# ADR 13: Sync folder layout

Status: **decided: device-log+copies.** Date: 2026-10-01. Opened by SPEC §10.9, because no earlier ADR says how rows sit in the folder. Owners: all four apps. The transport is Syncthing-fork on Android and Syncthing on Windows (`Tendril/tendril-spec.md`).

## Constraints

- **ADR 01's merge.** Each field group keeps its higher `(hlc, device)` stamp. The merge is idempotent, its result does not depend on arrival order, and the purge registry is permanent. Any layout that eventually delivers every version is therefore lossless. The contest is about what each layout costs and what it risks.
- **Fresh start, one person, a few devices.** There is no server (ADR 01; SPEC §0.1).

## Evidence

- **`verify/13-folder/real-world.md`.** How comparable apps lay out a synced folder, and what broke for them. Syncthing's conflict, atomicity, ordering and block rules, with sources. On Android 11+ scanning slows past 10,000–16,000 files.
- **`verify/13-folder/workload.md`.** What the four owner apps write, and when, with file:line evidence. It adds five requirements that hold whatever the layout: firing writes nothing that syncs; folder exports are debounced; every write is an atomic replace; JSON is compact; the device-id file is excluded from Android backup and device transfer.

## Options

There are 14 options in `options/13-folder.json`:
- the source apps' layouts: Tendril per-area, Chronicle device-snapshot, Mnemo per-row;
- the single shared file as the control;
- variants that merge conflict copies;
- four improvements: device-log, device-chunks, device-chunks-own, device-chunks-area.

## Method

- **Simulator.** `tools/folder_sim.py` is event-driven. Every device runs ADR 01's merge, over a Syncthing model:
  - conflicts go to the older mtime, and the copy propagates;
  - each file is replaced atomically, with no order between files;
  - transfer is per block (128 KiB);
  - sessions are cut part-way 5% of the time.
- **Shared layouts** use the best reasonable writer. It reads and merges before writing, and re-exports when the folder holds an older version than its database.
- **Measurements** run 14 days on top of a year of already-synced data (`tools/folder_cases.py`, 2 seeds).
- **Tuned settings:**
  - Each tunable layout runs at the settings `tools/folder_tune.py` found, over two or more compaction cycles: 30 s debounce; logs use 16 KiB segments with a snapshot every 64; chunks compact after 1,024.
  - The ranking holds for light and heavy page editing and for three devices (`options/13-folder.tune.json`).
- **Review.**
  - An adversarial Opus review of the model found eight issues that could move the ranking:
    - a settle step that forced a relay export the app never makes;
    - snapshot rewrites costed as appends;
    - appends costed below the atomic-replace rule;
    - a dataset 1/30 of its one-year size;
    - a delay metric that measured the laptop's schedule, not the layout;
    - a one-year join projection that does not hold for logs;
    - a lossless result for the shared-file control that depended on that relay export;
    - several smaller Syncthing-fidelity gaps, among them two deletions counted as a conflict.
  - All were fixed before these scores.
  - The simulator's own first finding, "per-row loses data", was a real failure of a writer that does not re-export a stale file. The healing writer above closes it for every shared layout.

## Cases (`cases/13-folder.jsonl`; scores in `13-folder-scores.md`)

| Case | Owner | Source |
|---|---|---|
| No `.sync-conflict-` copies in ordinary use (0.5 if the app merges and removes them) | syncthing | docs.syncthing.net/users/syncing.html |
| A conflict loser whose device is wiped before it syncs again keeps its change | syncthing | same |
| Fewer than 10,000 files after a year | android | syncthing-android #1630 |
| Nothing is lost after cut sessions and settling | factotum | ADR 01 |

The control (`one-file`) fails the two cases it was expected to fail. Seven options pass all four cases: device-snapshot, device-area, device-log, device-log+copies, and the three chunk variants.

## Measured costs (two devices, a year of data, per day; `options/13-folder.metrics.json`)

| Layout | Written | Sent | Files | Created/day | Join | Worst single-file share |
|---|---|---|---|---|---|---|
| device-snapshot (Chronicle) | 900 MB | 219 MB | 2 | 0 | 15.9 MB | 0.4% |
| device-area | 410 MB | 123 MB | 16 | 0 | 15.9 MB | 0.4% |
| device-log, ±copies | 0.91 MB | 0.92 MB | 103 | 7 | 17.4 MB | 10% |
| device-chunks | 0.63 MB | 1.37 MB | 1,034 | 220 | 16.9 MB | 11% |
| device-chunks-area | 0.63 MB | 1.19 MB | 1,048 | 220 | 16.9 MB | 10% |
| device-chunks-own | 0.44 MB | 0.98 MB | 1,034 | 220 | 8.4 MB | 100% |
| per-area+copies (Tendril, for reference) | 411 MB | 87 MB | 8 | 0 | 7.9 MB | 100% |

An edit reaches the other online device within about 12–14 minutes (p95) in every layout. The 15-minute import cycle sets that figure, not the layout.

## What the front means

- **Whole-state rewrites** (device-snapshot, device-area, and Tendril's per-area) cost hundreds of MB of flash writes a day at one year: 900 MB/day is about 330 GB a year on the phone. Under heavy page editing it runs into GB/day. Rewriting everything you hold, every time, is what fails at scale.
- **device-log** has the fewest files and file creations, and the least sent.
- **device-chunks** writes slightly less, but creates about 220 files a day and keeps about 1,000 in the folder.
- **device-chunks-own** is cheapest everywhere, but each version lives only in its author's files. If a file is damaged and its author retired, that data is gone.
- **The +copies variant** costs nothing measurable. It only matters if a device id is ever cloned, which requirement 5 prevents.

## Decision

**device-log+copies**, picked by the owner on 2026-10-01 from the front, the recommended option.

- **Device-owned files.** Each device writes only under `devices/<device-id>/`, so Syncthing never sees two writers on one file and makes no conflict copies in ordinary use.
- **Log segments.**
  - Each export appends the field-group versions of the rows written since the last export. That includes versions imported from peers, which keeps every version in at least two devices' files.
  - Segments are `log-<seq>.jsonl` of up to 16 KiB. Each write replaces the whole segment atomically (temp file, then rename).
- **Snapshots.** Every 64 segments the device writes `snapshot.json` (its merged state, compact JSON) and deletes its older segments.
- **Debounce.** The export follows the last local write by 30 s.
- **Reading.**
  - Each device reads every other device's new segments from a local read position (device-local, never synced). It reads a peer's snapshot only when that file has changed.
  - It also merges any `.sync-conflict-` copy, then deletes it. That is defence in depth if a device id is ever cloned.
- **Requirements carried with it.** The five in `verify/13-folder/workload.md`: firing writes nothing that syncs; exports are debounced; every write is an atomic replace; JSON is compact; the device-id file is excluded from Android backup and device transfer.

## Consequences

- The importer of SPEC §3.1 can now be built. It reads segments and snapshots into ADR 01's `Merger`, keeps the per-row base and the pending-question tables locally, and keeps per-file read positions.
- Folder legibility: a person sees one folder per device, each with about 50 small log files and a snapshot. Rows are not human-readable one per file.
- **Built 2026-10-01** (SPEC §3.13). Snapshots are named `snapshot-<seq>.jsonl` rather than `snapshot.json`, so a reader can tell a new one from its name.
- The settings in use are those of the tuning run, chosen on two or more compaction cycles. They can be retuned with `tools/folder_tune.py` if the real workload differs.
