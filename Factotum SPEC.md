# Factotum — Product & Technical Spec

**Status:** draft v0.4, seeded from the decision register · **Scope:** the merged data model, sync and behaviour rules of Factotum. Screens are not decided and are marked open (§10.1).
**Related documents:** `decisions/`, the evidence behind §3: one ADR per decision with verified `file:line` facts, the scored options, the behaviour cases and the harness that measured them (`decisions/register.md` is the index). This spec states each decision once and points to its ADR for the evidence. It never restates the evidence.

---

## Revision Log

| Version | Summary | Sections touched |
|---|---|---|
| v0.4 | §10.2 and §10.3 decided: KMP split by layer (`:core`, `:data`, `:llm`, `:ui` later, `:android`, `:windows`); the data layer goes first, in ADR order, with no screens. Imports are hybrid and pass a review gate | §5.1, §7, §9, §10 |
| v0.3 | The post-scoring fixes in ADRs 06, 11 and 12 were re-scored and a growth sensitivity pass run: no decision changed | §3.6, §3.11, §3.12 |
| v0.2 | Spikes 9.2, 9.4 and 9.6 run: DTSTART aligned, RULE_SET for set times, HABIT gains block_id and duration_min, seed and generator fixed, llama.cpp MIT | §3.4, §3.6, §6, §9 |
| v0.1 | Seeded from ADRs 01–12, the sole-owner probe and the owner's standing answers, after the 11–12 audit | all |

---

## 0. Hard Constraints

### 0.1 Owner's standing answers

Everything else in this spec is filtered through these.

| # | Constraint | Given |
|---|---|---|
| 0.1.1 | **Fresh start.** No data is migrated from the four source apps, and migration cost is never a reason for a design. | 2026-09-30 |
| 0.1.2 | **Folder sync, no server.** One person, several devices, one folder they choose. No compatibility with the source apps' sync files. | 2026-09-30 |
| 0.1.3 | **Constraint 0.14 applies to Habits only.** Inside Habits, nothing stores or shows a streak or a missed-day count. Nothing outside Habits inherits the rule. | 2026-09-30 |
| 0.1.4 | **Platforms: Android and Windows**, as Tendril ships now. | 2026-10-01 |
| 0.1.5 | **Every sole-owner module moves across.** No single-app feature is dropped. | 2026-10-01 |
| 0.1.6 | **Every visible choice is the owner's.** Layout, wording, navigation and palette are settled with the owner before they are built (§10.1). | standing practice |

### 0.2 Source apps

| App | Path under `Downloads/Builds/` | Platform today | Brings |
|---|---|---|---|
| Tendril | `Tendril/` (`shared/`, `Tendril android/`, `Tendril windows/`) | Android + Windows, Kotlin Multiplatform | calendar items, habits, reminders, check-ins, time logs, labels, pages and canvas |
| Chronicle | `chronicle-native-pending/chronicle-native/` | Android | trackers, goals, charts, activities and sessions, categories, checklists, reminders with alarms |
| Mnemo | `mnemo_pass4/mnemo/` (not git) | Android | reminders: cron and stochastic schedules, nag, modes and skins |
| Equipoise | `Personal assistant project/` | Android | check-in circumplex, regulation, burnout index, on-device LLM, capacity-ranked tasks |

---

## 1. Purpose, Goals & Non-Goals

**Purpose.** One app that does what Tendril, Chronicle, Mnemo and Equipoise do today, over one data model and one sync folder, so the same idea is never stored twice.

**Goals.**
- Every owner app's verified behaviour survives, unless a decision in §3 records its loss and the owner accepted it.
- One home per concept: one item table, one recurrence encoding, one label vocabulary, one search index, one sync model.
- A defect found in a source app while settling the decisions is fixed, not carried over (the "fixes" in each ADR).

**Non-goals.**
- Moving existing data across (§0.1.1).
- Cloud or server sync (§0.1.2).
- Streaks or missed-day counts in Habits (§0.1.3).

---

## 2. Blast Radius

**Unified: one model replaces several (§3):** sync identity, tasks and events, reminders, recurrence, per-occurrence edits, check-ins, habits, timed intervals, labels, settings, search, and how pages merge.

**Moves across as-is (§0.1.5), with only the identity and sync columns of §3.1 added:**

| Module | Entities | Owner | Evidence |
|---|---|---|---|
| Pages & canvas | page, block, property, property_value, page_database, page_database_view, page_relation, page_canvas, canvas_node, canvas_edge, page_revision | Tendril | the page-merge rule changes (§3.12) |
| Trackers & goals | tracker, tracker_choice, tracker_reading (was `EntryEntity`), goal, saved_chart, checklist, checklist_item | Chronicle | `docs/sole-owner-probe-2026-10-01.md` |
| Regulation | sensory_log, masking_entry, regulation_event, pending_outcome, daily_index | Equipoise | the same probe |
| Time blocks, calendar links | habit_block, calendar_link (device-local) | Tendril | the same probe |

**Dropped as mechanisms, with their behaviour kept elsewhere:**
- Tendril's Entry exception columns and `HabitScheduleEdit` become §3.11.
- Tendril's stored streak columns go (§0.1.3).
- Tendril's `.tendril-lost` folder files become §3.12.
- The four settings stores become §3.9.
- Tendril's and Chronicle's separate FTS tables become §3.10.

---

## 3. Decisions

Every decision here was scored against its owners' behaviour cases, with a control option that failed as expected, and picked by the owner. Three fresh-eyes audits checked the records: `docs/fresh-eyes-2026-09-30.md`, `docs/fresh-eyes-2026-10-01.md` and `docs/fresh-eyes-2026-10-01b.md`.

**Acceptance for every subsection below:** the ADR's behaviour cases (`decisions/cases/<nn>-*.jsonl`) are rewritten as tests against the real implementation, and all of them pass.

### 3.1 Sync identity and conflict — ADR 01

**Finding [Verified]:** the three syncing apps disagree on identity, deletion and conflict. Tendril's purge registry never expires, Chronicle garbage-collects tombstones after 90 days, and Mnemo raises a conflict on any `updatedAt` difference.

**Decided:** **hybrid+.**
- Every row has a ULID primary key and one `(hlc, deviceId)` stamp per field group. The whole row is one group by default.
- `deleted_at` sits in the group that decides whether the row exists.
- A permanent purge registry never expires.
- A person is asked (keep mine / take theirs / keep both) only when an item's **schedule** group changed on both sides since its base stamp. Everything else merges silently.

**Acceptance:** the 10 cases in `cases/01-sync.jsonl` pass. `tools/sync_sim.py` is the reference model.

### 3.2 Items: tasks and events — ADR 02

**Decided:** one `item` table.
- The kinds are TASK, EVENT, REMINDER (§3.3), HABIT (§3.6) and ACTIVITY (§3.7). CHECK constraints keep each kind's columns on that kind.
- Occurrences go to a `completion` log (DONE or SKIPPED).
- The sync groups are **schedule** (dates, times, due date, recurrence, `deleted_at`) and **status** (status, importance, `capacity_rank`).

**Names:** `Item`, and `TrackerReading` for Chronicle's logged value. Nothing is called "Entry".

**Acceptance:** `cases/02-task.jsonl`, 9 cases.

### 3.3 Reminders — ADR 03

**Decided:** a standalone reminder is an item of kind REMINDER. Reminder rows hang off any item.
- A reminder row carries `alert_kind` (NOTIFICATION or ALARM), nag count and duration, sound, vibration, mode, skin and `exact`.
- Standalone reminders show on the day view only when a setting is on. It is **off by default**.
- **Snooze syncs.** It is stored as `snoozed_until` in the row's own status group, and never overwrites the next occurrence.
- A reminder on an item with no start date is refused.

**Acceptance:** `cases/03-reminder.jsonl`, 11 cases.

### 3.4 Recurrence — ADR 04

**Decided:** **rrule+ext** on `item`. `recurrence_kind` is RRULE, RULE_SET, RANDOM_DAYS, RANDOM_WINDOW or PLANNED.
- Month ends anchor to the original date.
- DTSTART is the first date the rule's own anchor allows, on or after the active start (**[Verified]** §9.2).
- Several set times a day are a RULE_SET.
- Random draws are seeded with FNV-1a 64 of `itemId|occurrenceDate|kind` and drawn with SplitMix64, so every device computes the same time. **[Verified]** §9.4.
- A drawn time in a DST gap moves forward by the gap.
- Raw cron is accepted as input, converted, and never stored.
- **Missed occurrences:**
  - An **ALARM** is held by the OS through `setAlarmClock` and rings even while the app is dead.
  - A **NOTIFICATION** fires once, late, then continues.

**[Verified]** The PLANNED kind round-trips to Tendril's plans on 500/500 random weeks (§9.2).

**Platform limits, not defects:**
- A powered-off phone can't be woken.
- A force-stopped app loses its alarms until it is next opened, and it says so when it starts.

**Acceptance:** `cases/04-recurrence.jsonl`, 11 real rules round-trip through `tools/recurrence_sim.py`'s expander.

### 3.5 Check-in — ADR 05

**Decided:** one `check_in` table with **mood as its own axis**. The owner chose this against the recommendation, and ADR 05 records the loss it accepted.
- `mood` is 1–5.
- `energy` and `pleasantness` are 0..1 and nullable.
- `source_levels`, `stability` and `note` are also stored.
- **No numbers on the check-in screen**: no averages, counts or curves. Equipoise's engines still compute on demand.

**Acceptance:** `cases/05-checkin.jsonl`, 7 cases.

### 3.6 Habits — ADR 06

**Decided:** a habit is an item of kind HABIT linked to a tracker (`tracker_id` is required).
- Logging it is a reading on that tracker.
- Presence is derived as in `HabitPresence`: days this month, the last date, and the usual time (withheld below 3). There is no streak (§0.1.3).
- Pause is `pause_from` and `pause_until`.
- **[Amended]** A HABIT also carries `block_id` (its default time block) and `duration_min`. The planner needs both (§9.2).
- **The verb is "Log".** "Check-in" is kept for §3.5.

**Acceptance:** `cases/06-habit.jsonl`, 8 cases.

### 3.7 Timed intervals — ADR 07

**Decided:** an activity is an item of kind ACTIVITY.
- All tracked time is in one `time_span` table on `item_id`. A trigger refuses to delete an activity that still has spans.
- **Several timers can run at once.**
- A span counts wholly for **the day it started**.
- A day's total is the union of the spans that started that day, and a week's total is the sum of its days.
- Manual entry and editing apply to every owner.

**Acceptance:** `cases/07-timelog.jsonl`, 9 cases.

### 3.8 Labels — ADR 08

**Decided:** one `label` vocabulary (name, colour, `applies_to`, `sort_order`). Each owner keeps its cardinality:
- a page carries many, through `page_label`;
- an item (ACTIVITY or HABIT), a tracker or a page database carries one.

Names are unique ignoring case. A new label takes a colour derived from its name, which can then be changed. Labels sync as rows.

**The word on screen is "Label".** "Tag" keeps Tendril's meaning: a Select property.

**Acceptance:** `cases/08-tagging.jsonl`, 10 cases.

### 3.9 Settings — ADR 09

**Decided:** **scoped-live.** The owner chose this against the recommendation. Every key is declared once with a scope:
- **PERSONAL** keys sync live through a `setting` table and ride in the backup.
- **DEVICE_PREF** keys stay local and ride in the backup.
- **DEVICE_STATE** keys stay local and never leave the device.
- **SECRET** keys go to the Keystore or DPAPI.

The device id is not a setting.

**Acceptance:** `cases/09-settings.jsonl`, 9 cases.

### 3.10 Search — ADR 10

**Decided:** one FTS4 table, `search_fts(text, kind, row_key)`.
- It uses the `unicode61` tokenizer, which folds accents.
- Triggers on every source table keep it current, including on sync import.
- Queries AND prefix terms. Block hits get snippets.
- The index is local and rebuildable.

**Acceptance:** `cases/10-search.jsonl`, 7 cases.

### 3.11 Occurrence edits — ADR 11

**Decided:** one insert-once `occurrence_edit` log for every repeating item.
- Scopes: OCCURRENCE, DAY, WEEK, FROM and EXTRA.
- `changes` holds only the fields an edit sets. Edits apply in ADR 01 stamp order, field by field.
- A move is one edit with `moved_to`.
- **A clash on one occurrence asks the person**, like §3.1's schedule prompt.
- Renaming a series renames its moved occurrences.
- Tasks gain "this week" and "from now on".

**Acceptance:** `cases/11-occurrence-edits.jsonl`, 10 cases.

### 3.12 Page merge — ADR 12

**Decided:** **per-row+revive.**
- Blocks, property values, canvas nodes and edges, and database views are rows with §3.1 stamps and tombstones. Relations stay add-only, and the property schema stays upsert-by-uid.
- Block order is a fractional key.
- A later edit to any part restores a trashed page. **[Amended]** This is a deliberate exception to §3.1's group rule, and it applies to pages only.
- On a clash within the same paragraph, the later text wins. The losing part (block, cell or canvas node) goes to History, and a "replaced by a sync" notice appears.

**Acceptance:** `cases/12-page-merge.jsonl`, 8 cases.

---

## 4. Explicitly Out of Scope

- **Importing data from the four source apps.** It is ruled out by §0.1.1, and nothing is built to read their databases or sync files.
- **A sync server, accounts or cloud storage** (§0.1.2).
- **Streaks, chains and missed-day counts in Habits** (§0.1.3). Tendril's `show_habit_streaks` setting isn't carried over.
- **Tendril's `.tendril-lost` folder files** (§3.12), **Equipoise's parked `greyDay` column** (ADR 09), and **Tendril's Entry exception columns** (§3.11).
- **Waking a powered-off phone** (§3.4). No third-party app can do it.

---

## 5. Technical Architecture

### 5.1 Platforms and modules

**Decided:** Android and Windows (§0.1.4).

**Finding [Verified]:** Tendril is the only source app on both. It ships them from a Kotlin Multiplatform `shared/` module with Room declared in common code (`shared/src/commonMain/kotlin/com/tendril/app/data/TendrilDatabase.kt`), plus `Tendril android/` and `Tendril windows/`. The other three apps are Android-only Kotlin.

**Decided (2026-10-01, owner): KMP split by layer.** The owner asked which option scored best for the app's size and data, and picked from the front.

| Module | Holds | Depends on |
|---|---|---|
| `:core` | Pure Kotlin common code with no Room: ULID, HLC, field-group merge (§3.1), the recurrence expander and the seeded draw (§3.4), occurrence-edit application (§3.11), presence (§3.6), the page-part merge (§3.12) | nothing |
| `:data` | The one Room database with every entity and DAO, the triggers (§3.7, §3.10), the corruption guard on both drivers (§8), the repository and the sync importer. DAOs are `internal`, so only this module writes rows (§5.3) | `:core` |
| `:llm` | llama.cpp with the build switches of §6 | nothing |
| `:ui` | shared Compose, once §10.1 is settled | `:data`, `:core` |
| `:android`, `:windows` | the app shells | all of the above |

**Measured** (2026-10-01): the source apps hold 40.7k data and logic lines, 51.0k UI lines and 51 Room entities; Tendril's single `shared` module alone has 55.4k main lines. Four options were scored:

- **A. One `shared` module, as Tendril has.** On the Pareto front with C: the fewest modules, but every engine edit recompiles everything and reruns Room's code generation.
- **B. Split by feature. Dominated by C.** §5.2's hub tables (sync stamps, search triggers, labels, habit→tracker) would all cross module lines.
- **C. Split by layer.** On the front with A, and the owner's pick.
- **D. Android first. Fails §0.1.4.**

### 5.2 Data model

**Every synced table** carries §3.1's columns: a ULID id, a stamp per field group, and `deleted_at` in the existence group. The purge registry is one table.

| Area | Tables | Home |
|---|---|---|
| Items | `item` (TASK, EVENT, REMINDER, HABIT, ACTIVITY), `completion`, `reminder`, `occurrence_edit`, `time_span` | §3.2, §3.3, §3.6, §3.7, §3.11 |
| Trackers | `tracker`, `tracker_choice`, `tracker_reading`, `goal`, `saved_chart` | §2, §3.6 |
| Check-in & regulation | `check_in`, `sensory_log`, `masking_entry`, `regulation_event`, `pending_outcome`, `daily_index` | §3.5, §2 |
| Pages | `page`, `block`, `property`, `property_value`, `page_database`, `page_database_view`, `page_relation`, `page_canvas`, `canvas_node`, `canvas_edge` | §2, §3.12 |
| Labels | `label`, `page_label` | §3.8 |
| Other | `checklist`, `checklist_item`, `habit_block`, `setting` (PERSONAL only), `purge_registry` | §2, §3.9, §3.1 |

**Local only, never synced:**
- `page_revision` (§3.12);
- `calendar_link` (§2);
- `search_fts` (§3.10);
- the device store for DEVICE_PREF and DEVICE_STATE keys;
- the secret store;
- the device id (§3.9).

### 5.3 Layering rules

- **Every write goes through one repository layer**, which stamps the row per §3.1. Search stays correct even on paths that bypass it, because of §3.10's triggers.
- **Recurrence expansion** is one engine for every item kind, and it reads `occurrence_edit` (§3.4, §3.11).
- **The sync importer** is the only code that writes remote rows. It applies §3.1's merge per field group, and §3.12's per-row rule for page parts.

---

## 6. Licensing

The four source apps are the owner's own. The only third-party code found so far is Equipoise's vendored `third_party/llama.cpp`. **[Verified]** Only the MIT-licensed `llama` and `ggml` are built. The vendored extras aren't linked, because `common` and `tools` are off. Factotum must show llama.cpp's MIT notice in the app, and the Windows build must keep the same build switches (§9.6).

---

## 7. Phasing

**Decided (2026-10-01, owner): the data layer goes first. No screens are built in this phase.**

1. **Skeleton.** The modules of §5.1, building on Android and Windows, and the corruption guard (§8). **Done 2026-10-01.**
   - `:core`, `:data`, `:android` and `:windows` build. `:llm` is created with Equipoise's module in step 3, where its first code lands.
   - The guard recovers only from SQLITE_CORRUPT and SQLITE_NOTADB. A locked or full database is rethrown, and its file is left in place.
   - It moves the `-journal`, `-wal` and `-shm` files with the database.
   - Tests cover both drivers, with a control showing that the stock Android driver deletes a corrupt file. Wiring the guard into the Room open path comes with slice 01.
2. **Schema slices in ADR dependency order:** 01 → 02 → 03 → 04 → 11 → 06 → 07 → 08 → 09 → 10 → 05 → 12. Each slice is done when its ADR cases pass as tests against the real implementation (§3). Spikes 1 and 3 run with slice 10, and spike 5 runs with slice 04.
3. **The sole-owner modules of §2.**
4. **Screens**, after §10.1.

**Imports from the source apps are hybrid.**
- Self-contained units are ported, then cleaned. Examples: `KeepFileOnCorruptionDriver`, `HabitPresence`, the seeded draw, the RRULE expander.
- Code that is bound to the old schemas is rewritten against this spec, and the source is read only for behaviour.
- Every import passes a review gate before it is committed: `code-verification-core`, then `/code-review`, then `/simplify`, plus a check that removes AI slop (comments that restate the code, dead branches, speculative generality, invented APIs).

---

## 8. Risks

- **Windows parity for alerts.** §3.4's ALARM relies on Android's `setAlarmClock`, and Windows has no equivalent held by the OS. What an ALARM does on Windows is open (§10.4).
- **The on-device LLM on Windows.** Equipoise runs llama.cpp on Android only, and today only in the foreground.
- **Database corruption recovery.** Room's corruption handler deletes the database file before any recovery code runs. **[Verified]** All three syncing apps guard against this: Tendril with `shared/src/androidMain/.../KeepFileOnCorruptionDriver.kt`, and Chronicle and Mnemo each with a `DatabaseRecovery.kt`. Factotum must carry one of these guards onto both its drivers. Tendril's is the natural starting point, because it is already KMP.
- **Room triggers in common code.** §3.10 and §3.7 install triggers from a database callback, as Chronicle does on Android. **[Assumed]** The same callback works on the Windows (JVM) driver. See §9.3.

---

## 9. Pre-Implementation Validation / Spikes

Status: 2, 4 and 6 are done (`docs/spikes-2026-10-01.md`). With §10.2 decided, 1 and 3 run with schema slice 10, and 5 runs with slice 04 (§7).

1. **FTS5 on target devices.** It could replace FTS4 (§3.10) if every target SQLite build has it. Room's annotations don't generate it.
2. **PLANNED recurrence. Done.** All 8 RRULE-form rules match once DTSTART is aligned and set times use a RULE_SET. PLANNED matches on 500/500 random weeks once HABIT has `block_id` and `duration_min`.
3. **Triggers on both drivers.** §3.10's search triggers and §3.7's spans trigger install and fire on Android and on Windows.
4. **Seeded random draws. Done.** The draws are identical across 18 Kotlin versions and 4 time zones. Chronicle's current seed made two items draw in lockstep 1000/1000 times; the item-keyed seed doesn't. Both generators pass a uniformity test.
5. **Force-stop detection.** On the next start, the app detects that the OS cancelled its alarms and says so (§3.4).
6. **llama.cpp licence. Done:** MIT only (§6).

---

## 10. Open Items

1. **Screens, navigation and wording.** None are decided (§0.1.6). The only fixed words are "Label" (§3.8), "Log" for a habit (§3.6) and "check-in" for mood, energy and pleasantness (§3.5). The settings screen's marker for "follows you across devices" is also open (§3.9).
2. **Module layout. Decided 2026-10-01:** KMP split by layer (§5.1).
3. **Phasing. Decided 2026-10-01:** the data layer first, with no screens (§7).
4. **What an ALARM does on Windows** (§8).
5. **Equipoise's burnout index isn't computed in production.** `BurnoutIndex.compute` is called only from a test, and `sleepHours` has no source table. The work is to decide where the score is computed and where sleep comes from; a tracker is the obvious source.
6. **Occurrence-edit log growth.** A storage policy for edits on occurrences more than a year in the past (§3.11).
7. **Checklists in search.** Checklist text isn't indexed today (§3.10). Adding it is a feature choice.
8. **The map's copies. Done 2026-10-01.**
   - The `.md` table and its count line now read 10 contested, 0 duplicated and 1 name collision.
   - The `.html` carries both correction sections, and its exporters emit them.
   - The `.json` and `.csv` were rebuilt from the `.md` table, and all 14 rows were checked equal.
   - The pre-edit copies are in `../_map-before-2026-10-01/`.

---

## 11. Next Steps

1. The owner reviews this spec, especially §10.
2. Settle §10.1 to §10.4 with the owner.
3. Run the spikes in §9 before the feature code that depends on them.
4. Turn each ADR's cases into the first tests of the real schema (§3).
