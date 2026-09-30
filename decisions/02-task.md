# ADR 02: Task, a kind of calendar item or its own table

Status: **decided: shared**. Date: 2026-09-30. Owners: Tendril and Equipoise. This ADR also settles the "Entry" name collision with Chronicle.

Depends on ADR 01 (hybrid+). Every table below also carries a ULID key and per-group `(hlc, deviceId)` stamps. Those columns are the same in every option, so they are left out of the comparison.

## Verified facts

The facts were verified with `tools/verify.py`; the raw output is in `verify/02-task/`. The two starred rows were also spot-checked by hand with Read.

| App | Fact | Source | Map said |
|---|---|---|---|
| Tendril | `EntryKind { TASK, EVENT }`, one `entries` table | `Entry.kt:12,23` | confirmed |
| Tendril | Tasks use `startDate`/`startTime` as the *planned* When, with a separate `dueDate` deadline. The calendar draws tasks from these columns. There is no all-day column: all-day means `startTime == null`. | `Entry.kt:34-35,56-62` | partly stated |
| Tendril | `EntryStatus { PENDING, DONE, SKIPPED }`. A recurring task is one live row plus an append-only `EntryCompletion` log per occurrence. | `Entry.kt:15`, `EntryCompletion.kt:31` | not stated |
| Tendril | Subtasks go one level deep through `parentEntryId`. | `Entry.kt:67`, `TaskTree.kt:7` | not stated |
| Tendril | `originalEntryId` / `originalOccurrenceDate` / `isExceptionSkip` make an Entry row double as a per-occurrence exception. | `Entry.kt:48` | not stated (matters for contest 04) |
| Tendril ★ | **Elastic is not "a miss goes overdue".** Resolving a task steps it forward by whole periods until it is in the future, and missed occurrences are passed over. The KDoc says the name is a misnomer and was kept deliberately. | `RecurrenceRule.kt:27-35`, `ResolveEntryUseCase.kt:105-121` | "a miss goes overdue rather than sliding" (**refuted**; carried to contest 04) |
| Tendril | Nothing enforces that a TASK gets Elastic and an EVENT gets Fixed. | `RecurrenceRule.kt:11` | not stated |
| Equipoise | `task(id, date, title, doneAt, capacityRank, parentId)` is its own table. It has no time, recurrence, reminder or update stamp. `parentId` has no FK, so deleting a parent leaves orphaned subtasks. | `Entities.kt:72-80` | confirmed, but the orphans were missed |
| Equipoise ★ | **The capacity rule is not built.** `CapacityPlanner (G04)` is marked "not yet". `TaskDao` has only insert, replaceAll, all and wipe, and nothing outside export/import reads tasks. The design is N ∈ {1, 3, 5} from today's check-in, and at most one task on a lower-than-usual day. | `SPEC.md:161-163,263`; `Daos.kt:58-61` | "sized by the capacity-scaled day" (**partial**: a design, not code) |
| Equipoise | Equipoise has no calendar table at all, and its SPEC rules out a timeline planner. | `SPEC.md:246` | consistent |

## Cases and options

`tools/task_sql.py` builds every option in SQLite with foreign keys on. It loads one fixture: an event, a timed task, a date-only task, a recurring task, a subtask, and reminders on a task and on an event. It then runs each case as a query or as a write the database must refuse. The cases are in `cases/02-task.jsonl` and the options in `options/02-task.json`. Growth is counted from the built schema.

## Scores (`02-task-scores.md`)

| Option | Equipoise | Shared | Tendril | Growth | Status |
|---|---|---|---|---|---|
| **shared** | 1.00 | 1.00 | 1.00 | 22 | **front, the only member** |
| split | 1.00 | 0.50 | 1.00 | 28 | dominated (no single id space for reminders and sync) |
| split+view | 1.00 | 1.00 | 1.00 | 34 | dominated (same coverage, +2 tables/views, +10 columns) |
| shared+side | 1.00 | 0.50 | 0.80 | 24 | dominated (subtask FK orphans the item; an event can get task state) |
| bare (control) | 0.50 | 0.50 | 0.40 | 21 | failed all 4 cases it was expected to fail, plus one more |

The map called this "derivable in principle, contested in practice". Measured, it is not contested. With the index `(kind, start_date)`, SQLite plans Equipoise's capacity query as `SEARCH item USING INDEX item_kind_date (kind=? AND start_date=?)` and never scans event rows. CHECK constraints give Equipoise the one thing its own table gave it: task state can never appear on an event. Tendril leaves that unenforced today.

## Recommendation

**shared**: one `item` table with `kind IN ('TASK','EVENT')`.
- **From Tendril:** the planned date and time, `due_date`, `status` PENDING/DONE/SKIPPED, `importance`, `parent_id` with an FK and ON DELETE CASCADE, and the recurrence column.
- **From Equipoise:** `capacity_rank` as a nullable task-only column.
- **Integrity:** CHECKs keep task state off events and event end times off tasks.
- **Index:** `(kind, start_date)`.
- **Completions:** a `completion` log records each occurrence as DONE or SKIPPED.

**Name collision.** Tendril's `Entry` (a calendar item) and Chronicle's `EntryEntity` (a logged tracker value) both lose the name "Entry". Proposed names: `Item` here, and `TrackerReading` for Chronicle's. That rename belongs to the Trackers module, which Chronicle owns alone.

## Decision

**shared** was confirmed by the owner on 2026-09-30.

Names: `Item` for a calendar task or event, and `TrackerReading` for Chronicle's logged value. Nothing in Factotum is called Entry.

## Consequences for later contests

- **Contest 03 (Reminder).** A reminder can point at one `item.id` with a real FK, for tasks and events alike.
- **Contest 04 (Recurrence).** The recurrence column lives on `item`. (Amended 2026-10-01: this line first said Tendril's per-occurrence exception columns come with it; ADR 11 replaced them with the `occurrence_edit` log.)
- **Sync groups (ADR 01).** `item` has a *schedule* group (planned date and time, `due_date`, recurrence, `deletedAt`) and a *status* group (`status`, `importance`, `capacity_rank`). hybrid+ asks a person only about concurrent schedule changes.
