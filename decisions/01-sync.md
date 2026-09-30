# ADR 01: Sync identity and conflict

Status: **decided: hybrid+**. Date: 2026-09-30. Owners: Tendril, Chronicle, Mnemo, and Equipoise (import only; the map missed this).

## Constraints from the owner

- Fresh start: no existing rows to convert, so migration cost is not scored.
- Folder sync with no server: one person, several devices, a folder they choose. No compatibility with the old apps' sync files.

## Verified facts

These were checked with the measured brief (`tools/verify.py`, Sonnet 5.5). The raw output is in `verify/01-sync/`. Spot-checked by hand with Read: Tendril `SnapshotSyncOrchestrator.kt:1562-1575` and `PurgeRegistry.kt:88-115`; Chronicle `FieldStamp.kt:30-42,86-102`, `Syncable.kt:22` and `ReminderMerge.kt:8-30`; Mnemo `ReminderSyncManager.kt` in full; Equipoise `Transfer.kt:50-75`; the fresh-eyes audit re-read `ReminderEntity.kt:22-44` and `SnapshotSyncOrchestrator.kt:1862-1875`.

| App | Fact | Source | Map said |
|---|---|---|---|
| Tendril | Entries and habits merge as a whole row, last writer wins on `updatedAt`. The comparison is a strict isAfter on wall-clock time. On a tie each device keeps its own copy, so a tie never converges. | `SnapshotSyncOrchestrator.kt:1571` | "snapshot union merge" (partial) |
| Tendril | For **entries and habits**, moving a row to the trash sets `deletedAt`, an ordinary field of the whole-row merge, so a later edit on another device beats it. For **reminders, check-ins and habit completions** the tombstone wins ("the delete wins"). | `:1571,1616` (entries); `:1869` (reminders); `:1984` (completions); `:2028` (check-ins) | implied "tombstones win" (**partial**: true for reminders, check-ins and completions; false for entries and habits) |
| Tendril | `PurgedRecord` (a permanent delete) never expires. A record newer than `purgedAt` supersedes it. A device that never edited the row stays blocked. | `PurgeRegistry.kt:88-99`, `PurgedRecord.kt:59` | confirmed |
| Tendril | 12 folder-wide array files plus one file per page. Undecodable records are quarantined and republished verbatim. `UnknownFieldMerge` carries undeclared keys. | `SnapshotSyncOrchestrator.kt:98, 430-442` (held only when the peer's copy would win on updatedAt); `UnknownFieldMerge.kt:12-44` | not stated |
| Chronicle | Identity is a ULID primary key. Stamps are `(updatedAt, deviceId)` in total order, with the device id breaking ties. | `Ids.kt:18`, `FieldStamp.kt:36-39`, `ReminderEntity.kt:38-41`, `SyncCodec.kt:93` | "scheduleUpdatedByDevice" (**partial**: that is the Room column, `ReminderEntity.kt:39`, and the JSON key is `scheduleUpdatedAtDevice`; either way it is a merge stamp, not the identity) |
| Chronicle | Reminders merge per field group: *schedule* (with `deletedAt` in it) and *status*. The other 10 entity types merge as a whole row. | `ReminderMerge.kt:8-21`, `EntityMerge.kt:25`, `RoomRepositoryBundle.kt:37-137` (the wiring that gives the count of 10) | not stated |
| Chronicle | Stamps more than 24 h ahead are clamped to "now" for the comparison. A fast device wins for up to its skew, then stops winning. | `FieldStamp.kt:86-101` | not stated |
| Chronicle | Tombstones are deleted after 90 days (garbage-collected). A device offline for longer brings the row back. | `Syncable.kt:22`, `RoomBackedRepository.kt:72` | not stated |
| Mnemo | UUID id plus `updatedAtEpochMillis`. There is one file per reminder, `reminders/<uuid>.json`. | `Reminder.kt:34,81`; `ReminderSyncManager.kt:38` | confirmed |
| Mnemo | `isArchived` is the sync tombstone. It also means done, or fired with nothing left. | `Reminder.kt:23-24` | **missed** |
| Mnemo | A conflict is any differing `updatedAt` on a file that moved. There is no both-sides-changed test, so an edit made only on the other device still goes to the conflict screen. Equal stamps count as "unchanged", so a same-millisecond divergence is never noticed. | `ReminderSyncManager.kt:144-160` | contradicts its own KDoc (`:18`) |
| Mnemo | Deleting a file from the folder does not delete the reminder; `pushMissingOrStale` rewrites the file. | `ReminderSyncManager.kt:197` | not stated |
| Equipoise | `Importer.merge` merges by device-local autoincrement id using REPLACE. Deletes are hard and no deletion travels through an import, so a deleted row returns from any older export. REPLACE on a clashing id does delete the local row first, and the CASCADE on `regulation_event.checkinId` (`Entities.kt:46`) deletes that check-in's events with it. Two devices that each create id=1 overwrite each other. | `Transfer.kt:57-69`, `Daos.kt:16` | "does not sync" (**partial**) |

**The map's claim that "tombstone-union and last-writer-wins give different answers to the same delete-then-edit" is refuted.** For trash plus a later edit on an entry or habit (Tendril) or any Chronicle entity, the two apps agree: the edit brings the row back. Tendril's reminders, check-ins and completions are the exception, where the delete wins (simulated, `sync_sim.py`). They differ on *permanent* purge. Tendril's registry holds forever, while Chronicle's 90-day garbage collection lets a stale device bring the row back.

## Cases and options

The cases (`cases/01-sync.jsonl`) are the properties each owner app guarantees, each with its source line. The options (`options/01-sync.json`) are the three existing models, two hybrids, and a control (Equipoise's REPLACE). Every option was run by `tools/sync_sim.py`, which rebuilds each model's merge rule from the verified lines above. Nothing is marked by hand. The `tendril` option models Tendril's entry and habit rule (whole-row, and a later edit beats a trash). Tendril's own reminders are delete-wins, which the fresh-eyes audit found afterwards. On `chronicle-delete-beats-status` that would move the tendril option from 0 to 1, which leaves it on the front and changes no pick.

## Scores

See `01-sync-scores.md`. Coverage per owner, where 1 means the guarantee holds, 0.5 means a person is asked, and 0 means it is lost silently:

| Option | Chronicle | Mnemo | Shared | Tendril | Growth |
|---|---|---|---|---|---|
| tendril | 0.00 | 0.00 | 0.50 | 1.00 | 3 |
| chronicle | 1.00 | 0.00 | 0.50 | 0.67 | 5 |
| mnemo | 0.50 | 1.00 | 0.50 | 0.50 | 3 |
| **hybrid** | 1.00 | 0.00 | 1.00 | 1.00 | 6 |
| **hybrid+** | 0.83 | 1.00 | 0.75 | 1.00 | 8 |
| replace (control) | 0.33 | 0.00 | 0.50 | 0.33 | 0 |

The control fails every case it was expected to fail, so the scorer can tell a loss from a win. All five real options are non-dominated. For some pairs growth is the only thing keeping them apart: hybrid beats tendril on coverage but costs 3 more columns, and hybrid+ beats mnemo on coverage but costs 5 more. On behaviour, **hybrid** and **hybrid+** are the only options that keep every Tendril guarantee and lose no Chronicle or shared guarantee silently. The chronicle option also keeps all its own guarantees, but it silently loses Tendril's purge. They differ in a single decision: whether a concurrent change to a reminder's schedule is merged silently (hybrid) or shown to a person (hybrid+).

## Decision

**hybrid+** was picked by the owner on 2026-09-30, after a walk-through of both hybrids.

The model:
- **Identity.** Every row has a ULID primary key.
- **Stamps.** Each field group carries an `(hlc, deviceId)` stamp. The whole row is one group by default.
- **Deletion.** `deletedAt` lives in the group that decides "does this exist".
- **Permanent delete.** A purge registry records purged rows. It never expires, and only a newer edit supersedes it.
- **When a person is asked.** The *schedule* group also keeps a per-row base stamp. If both sides changed it since that base, a person is asked: keep mine / take theirs / keep both. Everything else merges silently.

**Why:** hybrid+ is the only option that loses no owner's guarantee silently. Its cost is an occasional prompt when the same reminder's schedule really was changed on two devices between syncs. It also fixes Mnemo's current defect, which is asking about changes made on one side only.

## Consequences for later contests

Either hybrid fixes the identity columns every later table carries:
- a ULID primary key;
- one `(hlc, deviceId)` stamp per field group, with a whole-row group by default;
- `deletedAt` inside the group that decides "does this exist";
- one purge registry table.

Contest 02 (Task) and contest 03 (Reminder) must say which field groups their rows have.
