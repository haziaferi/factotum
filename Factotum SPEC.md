# Factotum — Product & Technical Spec

**Status:** draft v0.19, seeded from the decision register · **Scope:** the merged data model, sync and behaviour rules of Factotum. Screens are not decided and are marked open (§10.1).
**Related documents:** `decisions/`, the evidence behind §3: one ADR per decision with verified `file:line` facts, the scored options, the behaviour cases and the harness that measured them (`decisions/register.md` is the index). This spec states each decision once and points to its ADR for the evidence. It never restates the evidence.

---

## Revision Log

| Version | Summary | Sections touched |
|---|---|---|
| v0.19 | Slice 05 built: one `check_in` table on own-axis, Tendril's mood and energy taps, Equipoise's two axes and widget, past days, and Equipoise's LowMoment and StabilityTrend ported | §3.5, §7 |
| v0.18 | Slice 10 built: the search index over items, trackers, Logs and sessions, with the owner's answers; spikes 1 and 3 on the desktop | §3.10, §5.2, §7, §9 |
| v0.17 | Slice 09 built: settings by scope, the day boundary and the timer limit as PERSONAL settings every repository reads on each call, the settings part of a backup. A recovered database reads its own folder files again | §3.4, §3.7, §3.9, §3.13, §7 |
| v0.16 | Slice 08 built: labels on activities, habits and trackers, merged by name after a sync, read through what they were merged into; label time totals. Found on the way: an upgrade that rebuilt a table stopped on a trigger naming it, so the app's triggers are dropped before any upgrade | §3.7, §3.8, §7 |
| v0.15 | Slice 07 built: activities as items, one `time_span` table, several timers, day totals as unions by the start day, goals on tracked time, the owner's answers (long timers ask, finishing stops a timer, an activity is never deleted forever) | §3.6, §3.7, §7 |
| v0.14 | Owner answer: an "n a day" habit reminds at the start of each occurrence's block. Found on the way: a whole-day item reminded before its anchor missed the rest of a day once a firing had passed | §3.4, §3.6, §10 |
| v0.13 | Slice 06b built: time blocks with Tendril's five defaults, the PLANNED kind, and the week planner ported from Tendril. A 06a defect fixed: two habits sharing a tracker shared one pause | §3.4, §3.6, §7 |
| v0.12 | Slice 06a built: trackers (Chronicle's, as they are), habits tied to their trackers, Logs, presence with the owner's rule, rolling habits, pause. The item rules now sit in COALESCE: a task with no status had slipped through | §3.4, §3.6, §7 |
| v0.11 | Slice 11 built: the occurrence-edit log, its engine in `:core`, clash questions from base stamps, edits reaching reminders | §3.11, §7 |
| v0.10 | Slice 04 built: the RRULE expander (ported from Tendril, extended to times of day), rule sets, seeded random kinds, cron conversion, recurrence on items, reminders on repeating items | §3.2, §3.3, §3.4, §7 |
| v0.9 | Slice 03 built: reminders on any item, standalone reminders as REMINDER items, fire times, synced snooze, the day-view toggle | §3.2, §3.3, §7 |
| v0.8 | Slice 02 built: `item` (TASK, EVENT) and `completion`, the repository, CHECK rules and the export queue as triggers, deferred foreign keys with a waiting table for rows that arrive before their parent. ADR 01's merge fixed: a replayed old version moved the base and hid a later clash | §3.1, §3.2, §3.13, §7 |
| v0.7 | Slice 01's folder importer and exporter built (ADR 13): its 4 cases pass through them under a Syncthing double. Rows carry their table; group doubles must be finite; database version 2 | §3.1, §3.13, §7 |
| v0.6 | §10.9 decided as ADR 13: device-log+copies. Five folder requirements added (§3.13) | §3.1, §3.13, §7, §10 |
| v0.5 | Slice 01 built: the sync merge engine (§3.1), the database with its real open path and corruption guard, the purge registry, the clock and the device id. §10.9 opened: the sync folder's layout | §3.1, §7, §10 |
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

**Built (2026-10-01):** the merge engine in `:core` (`com.factotum.core.sync`), behind a `SyncStore` interface. The 10 cases pass against it on both targets, with hybrid+'s scored outcomes: 8 hold, and 2 ask a person. `tools/mutants.py 01` shows that each rule is needed: without it, named tests fail. Rules the implementation had to fix, none of which changes the decision:
- **A person's answer settles the clash everywhere.** The answered group carries `settles`, the other side's stamp that the answer saw, and it syncs. The device that was also asked takes the answer instead of asking again. This adds one synced `(hlc, device)` pair to every asking group.
- **Keep mine** re-stamps the local group. Its base becomes the stamp it settled, so a later edit on the other side is asked again. **Take theirs** adopts their group, stamp and all. **Keep both** keeps mine, and makes their version a new row with a new ULID.
- **Two devices that answer differently are asked again.** That is ADR 01's rule as written: both sides changed the schedule since their base. Nothing is lost.
- **Group values are String, Long, Boolean, Double or null.** Clashes compare values with `==`, so 5 and 5L would otherwise differ.
- **The clock resumes from its stored high-water mark** (table `clock`). A wall clock set backwards therefore cannot reissue an older stamp. Each write saves the clock in its own transaction (slice 02).
- **A pending question is not replaced by an older replay** of the other side's version (fixed with slice 02).
- **A version no newer than the base is ignored** (fixed with slice 02). A device log replays old versions, and merging one used to move the base up to this device's own newer stamp. The other side's next change then looked uncontested and replaced this device's change without asking. The in-memory cases never replayed an old version, so this was missed until the folder tests did.
- **The device id lives in its own file** (ADR 09), written atomically. An unreadable file is set aside and a new id made.
- **Purges:** an import re-checks only the registry entries it added or lowered.

**Importer built (2026-10-01):** see §3.13. Two changes to the rules above came with it: a `Row` names its table (ids stay unique across tables), and a Double value must be finite, since NaN never equals itself and JSON cannot carry it.

### 3.2 Items: tasks and events — ADR 02

**Decided:** one `item` table.
- The kinds are TASK, EVENT, REMINDER (§3.3), HABIT (§3.6) and ACTIVITY (§3.7). CHECK constraints keep each kind's columns on that kind.
- Occurrences go to a `completion` log (DONE or SKIPPED).
- The sync groups are **schedule** (dates, times, due date, recurrence, `deleted_at`) and **status** (status, importance, `capacity_rank`).

**Names:** `Item`, and `TrackerReading` for Chronicle's logged value. Nothing is called "Entry".

**Acceptance:** `cases/02-task.jsonl`, 9 cases.

**Built (2026-10-01):** `com.factotum.data.item`. All 9 cases pass as tests against the real database: eight in `ItemCasesTest`, and `tendril-reminder-fk` with the `reminder` table in `ReminderCasesTest` (slice 03). What the build settled, none of which changes the decision:
- **Three groups, not two.** The columns ADR 02 leaves unassigned (`kind`, `title`, `parent_id`) form a third group, `details`. It merges silently, like everything but the schedule (§3.1: the whole row is one group by default).
- **The CHECK constraints are triggers.** Room cannot declare a CHECK, so `SchemaTriggers` creates BEFORE INSERT and BEFORE UPDATE triggers that refuse a row breaking its kind's rules. They are dropped and created again on every open, so an upgrade never keeps an old body.
- **Deleting a parent deletes its subtasks** (`deleted_at` on each). Deleting forever (a purge) removes them through the foreign key, with the parent's completions.
- **Two devices resolving one occurrence leave two `completion` rows.** A unique key would make the second device's row fail to import, so reads take the later stamp per occurrence.
- **The capacity query uses `item_kind_date`** and never scans the table, checked from the query plan.
- **Each write is one transaction** through the same staged merge as an import. It stamps the groups it changes and saves the clock with them (§3.1). Answers to a pending question (keep mine, take theirs, keep both) go the same way.
- **The recurrence columns** came with slice 04 (§3.4).

### 3.3 Reminders — ADR 03

**Decided:** a standalone reminder is an item of kind REMINDER. Reminder rows hang off any item.
- A reminder row carries `alert_kind` (NOTIFICATION or ALARM), nag count and duration, sound, vibration, mode, skin and `exact`.
- Standalone reminders show on the day view only when a setting is on. It is **off by default**.
- **Snooze syncs.** It is stored as `snoozed_until` in the row's own status group, and never overwrites the next occurrence.
- A reminder on an item with no start date is refused.

**Acceptance:** `cases/03-reminder.jsonl`, 11 cases.

**Built (2026-10-02):** `com.factotum.data.reminder`. All 11 cases pass as tests against the real database: ten in `ReminderCasesTest`, and `chronicle-standalone-repeats` with the recurrence columns in `RecurringItemTest` (slice 04), where `shared-one-recurrence-home` is also checked across every synced table. ADR 02's `tendril-reminder-fk` passes here too. What the build settled, none of which changes the decision:
- **Two groups.** `alert` holds the offset, anchor, alert settings and `deleted_at`; `status` holds only the snooze (`snoozed_until`, `snoozed_from`). Neither asks a person; a retime of a standalone reminder is a change to its item's schedule, which does.
- **Fire time** is the item's start date, at its start time (else the reminder's anchor, else midnight), moved by the offset in wall-clock minutes: five minutes before 14:00 is 13:55 on any day, whatever the time zone does. A reminder is quiet once its item is done, skipped or deleted.
- **A snooze holds for the firing it snoozed.** The `status` group keeps the snoozed time and the time it replaced. Once the item is rescheduled or the reminder retimed, the reminder fires at its new time, as Mnemo's does when a reschedule replaces its next fire. Snoozing never changes the item's schedule.
- **Computing firings writes nothing** (§3.13 requirement 1). Which firings have rung is device state, built with the Android and Windows shells.
- **A reminder on an item with no start date is refused by the repository**, and so is taking the start date away from an item with live reminders, or adding one to a deleted item. A trigger would instead drop a synced reminder whose item lost its date on another device; such a reminder is kept, and does not fire.
- **Deleting a standalone reminder's last reminder deletes its item**, which would otherwise sit unseen, never firing. **"Keep both"** on a clash over a standalone reminder copies its reminders onto the new item, so both times fire.
- **The day-view setting** (off by default) is ADR 09's `show_reminders_on_day`, a DEVICE_PREF (§3.9); the day query takes it from its caller, with no default of its own.

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

**Built (2026-10-02):** `com.factotum.core.recurrence`, with the columns on `item`. All 11 cases pass as tests (`RecurrenceCasesTest`). The 9 fixed rules are compared, occurrence by occurrence, with the truth `tools/recurrence_sim.py` computes from the owner apps' rules (`tools/recurrence_fixtures.py` writes it as a fixture); Mnemo's three go through the cron converter. The two random kinds are checked for their properties, and the draw against the spike's own SplitMix64 in both Python and its Java. What the build settled, none of which changes the decision:
- **The expander is Tendril's `RecurrenceSpec`, ported and extended**: to local date-times, `MINUTELY`, `HOURLY`, `BYHOUR`, `BYMINUTE`, `BYSETPOS`, and `UNTIL` to the second. It stays strict: a rule with a part it lacks (or YEARLY day selection without `BYMONTH`) is refused, never half-read. Porting found a bug in the original: a YEARLY period began at the start's month, so a `BYMONTH` earlier in the year was missed in the last year of a window.
- **DTSTART is an occurrence only when it matches the rule**, unlike RFC 5545. DTSTART is aligned to the rule anyway, and a converted cron rule starts at midnight, which must not ring.
- **Times are floating.** `UNTIL` with a `Z` is read as local, like every other time. Turning a time into an instant, with the DST-gap rule above, belongs to the shells' alarm code.
- **The seeded draw** is the spike's FNV-1a 64 + SplitMix64, cut at the same bound, so its draws equal the spike's.
- **Recurrence lives in the item's schedule group**, so a clashing rule change asks a person (ADR 04). Triggers tie each kind to its columns and require a start date.
- **Reminders on a repeating item** fire at its next occurrence after a given moment that is not resolved in the completion log. The search for it starts at the beginning of the day before that moment (earlier by a positive offset), since a whole-day occurrence sits at midnight and fires hours later: starting at the moment itself missed the rest of a day for a reminder set before its anchor (fixed 2026-10-02). A whole-day item's fire at the reminder's anchor, unless its rule sets times (BYHOUR, a random window, cron). A snooze names the firing it snoozes, which only the shell knows, and holds for that one firing. A rule this version cannot read (from a newer peer) silences only its own item's reminders.
- **Rules that would mislead are refused**, as well as unsupported parts: BYMONTHDAY under WEEKLY, a day no listed month has, an INTERVAL over 10,000. A minutely or hourly rule skips the days its limits exclude, so a rare one costs no more than a frequent one.
- **PLANNED** (habits' planner) was built with slice 06 (§3.6, part b).
- **Spike 5 (force-stop detection)** needs the Android shell and a device; it runs with the shell, not here.

### 3.5 Check-in — ADR 05

**Decided:** one `check_in` table with **mood as its own axis**. The owner chose this against the recommendation, and ADR 05 records the loss it accepted.
- `mood` is 1–5.
- `energy` and `pleasantness` are 0..1 and nullable.
- `source_levels`, `stability` and `note` are also stored.
- **No numbers on the check-in screen**: no averages, counts or curves. Equipoise's engines still compute on demand.

**Owner answers, 2026-10-03:** a check-in may be about a past day (it keeps the moment it was made and, optionally, the day it is about); Equipoise's stability trend is kept, said in words only; check-in notes stay out of search.

**Acceptance:** `cases/05-checkin.jsonl`, 7 cases.

**Built (2026-10-03):** `com.factotum.core.checkin` and `com.factotum.data.checkin`. All 7 cases pass as tests (`CheckInCasesTest`). What the build settled, none of which changes the decision:
- **A check-in has three ADR 01 groups**: what it says (its moment, the day it is about, its values), written once; its note; its deletion, so a note edited on another device never brings back one undone (Tendril: delete wins). It is undone, not changed; several a day are kept.
- **Scales:** a Tendril energy tap is (k − 0.5) / 5 with `source_levels = 5`; Equipoise's widget keeps the values it has always stored, 0.15, 0.5 and 0.85, with `source_levels = 3`. The rules (a whole mood 1–5, axes 0–1, a whole step count on an axis, a well-formed moment and day) sit on the group written once.
- **Days:** a check-in counts for the day it is about, else the personal day it was made on; the day it is about is no later than that personal day. The engines read the moment: their history is every two-axis check-in made before the one judged, by its personal day.
- **Ported unchanged:** Equipoise's LowMoment and StabilityTrend (said in words only, owner 2026-10-03), with their tests. Not ported yet: the check-in shapes (with the screens), BurnoutIndex (§10 item 5) and the direction engines (with regulation, §7 step 3).

### 3.6 Habits — ADR 06

**Decided:** a habit is an item of kind HABIT linked to a tracker (`tracker_id` is required).
- Logging it is a reading on that tracker.
- Presence is derived as in `HabitPresence`: days this month, the last date, and the usual time (withheld below 3). There is no streak (§0.1.3).
- Pause is `pause_from` and `pause_until`.
- **[Amended]** A HABIT also carries `block_id` (its default time block) and `duration_min`. The planner needs both (§9.2).
- **The verb is "Log".** "Check-in" is kept for §3.5.
- **Owner answers, 2026-10-02:** a rolling habit ("due again N days after the last Log", Tendril's default) stays rolling, as a recurrence kind ROLLING; presence counts a "yes", any rating and a number above 0, and number habits show today's and this month's amounts; the day boundary is a personal setting, default midnight. The tracker stays required and is created with its habit in one write (a habit may also use an existing tracker); deleting a tracker deletes its habits, deleting a habit leaves the tracker and its Logs.

**Acceptance:** `cases/06-habit.jsonl`, 8 cases.

**Built (2026-10-02), part a:** trackers in `com.factotum.data.tracker`, habits in `com.factotum.data.item` (`HabitRepository`), presence and the rolling kind in `:core`. All 8 cases pass as tests (`HabitCasesTest`), with the owner's answers. What the build settled, none of which changes the decision:
- **Chronicle's trackers move as they are** (`tracker`, `tracker_choice`, `tracker_reading`, `goal`), one ADR 01 group per row, as Chronicle stamps whole rows; their domain rules (one value per reading, a rating from 1 to 5, a unit only on a number tracker, a CHOICE tracker with no default) are triggers. A reading's time is a floating local date-time, as every Factotum time is, so the day boundary compares the wall clock directly. A tracker's category is ADR 08's label (§3.8).
- **A habit and its tracker are one write**; a number habit's amount per Log is the tracker's default value, and its daily amount is Chronicle's recurring, automatic DAY goal (one per tracker). A habit's Log with no value is a "yes", or its amount per Log, and a Log must be of its tracker's kind. A habit is a yes/no, rating or number habit: a choice tracker has no presence. A habit that uses an existing tracker shares its Logs, which belong to the tracker.
- **A deleted tracker** takes its habits and goals; a purge takes its goals too, which name it without a foreign key. A habit another device made on it meanwhile reads as deleted. Undo takes the Log made last.
- **Columns:** `tracker_id` and `block_id` in the item's details group (a block merges silently, ADR 11); `pause_from`, `pause_until` (none means until resumed, as in Tendril), `duration_min`, `roll_every` and `roll_unit` in its schedule group.
- **A rolling habit** falls due a period after the day of its last Log that counts as presence, or at its start before any, and stays due every day until a Log, as Tendril's does; a month is a calendar month (Tendril counted 30 days).
- **Logged occurrences are quiet:** a Log naming an occurrence silences that one; a Log naming none silences the first other occurrence of its personal day, so one dose of three leaves two. Pause and Logs both go by the personal day.

**Built (2026-10-02), part b:** time blocks and the week planner in `com.factotum.core.plan`, ported from Tendril's `CalendarSchedule.kt`; the blocks in `habit_block`, the PLANNED columns on `item`. Tendril's planner tests that still apply pass as tests (`PlannerTest`), with the database cases in `PlannerCasesTest`. What the build settled, none of which changes the decision:
- **Expanding and editing moved out of the planner.** Each habit's occurrences come from ADR 04's expander with ADR 11's edits applied, less its paused days; the planner only places them and suggests. So the load a suggestion balances is the week after its edits, where Tendril counted the week before them. Each day follows the rule in force on it, the item's own or one a FROM edit set, as Tendril's planner reads the habit day by day.
- **A confirmed week** is laid out before the other edits, so every DAY, WEEK and FROM edit reaches its days whenever it was written (a skip, a block, a time), and a moved or added entry in that week stays, as in Tendril. Confirmed days count only from the habit's start and on its own days. This replaces slice 11's rule that a confirmation cleared whatever was in the week. The days suggested leave out paused and skipped ones.
- **PLANNED** is `plan_n`, `plan_per` (DAY or WEEK), `plan_days` and `plan_blocks`, on a HABIT only. "n a day" has no set time: the i-th occurrence of a day is at i seconds past midnight, an ordinal no real time uses, which ADR 11's edits and a Log name. It sits in the block it names, or is spread evenly over the blocks in their order. "n a week" places nothing until a WEEK edit confirms the week's days; until then the planner suggests them as Tendril does (evenly spaced, rotated to keep the busiest day lightest, then the load even), each habit on the load the earlier ones left.
- **Blocks** are Tendril's rows, one group each, with its weekday times in its own text (`SAT,SUN@480-630`). The five defaults are written when a database is made (or upgraded to blocks), under fixed ids and one fixed stamp, so two devices hold the same five and any real edit is newer. A habit names its block without a foreign key: a deleted block leaves its habits at any time of day.
- **Placing:** a set time goes in the block holding it (start in, end out), else outside every block, kept and shown; otherwise in the block an edit gave the occurrence (or none), else its slot's block, else the habit's. Blocks that overlap on a day are reported. With every block deleted, "n a day" occurrences are at any time, where Tendril placed none: they still exist to be Logged.
- **The personal day** of a whole-day occurrence is its own date; only a timed one moves to the day before when the day starts after midnight (§3.6, part a). Pause and Logs both follow it. Whether an occurrence is timed is one rule for the planner, pause, Logs and reminders: the item's set time, a time its day's rule sets, or one an edit gave it.
- **An occurrence's block** is ADR 11's `block` field, now read; it merges silently. `sort_order`, `rule_patch` and `pause` stay as written: an occurrence keeps its habit's manual order (`sort_order` on the item, from slice 07, then the item), and Factotum edits a rule with a FROM edit and pauses on the item.
- **Reminders** on an "n a day" habit fire once per unlogged occurrence, at the start of its block that day (weekday times included), moved by the reminder's offset (owner, 2026-10-02). An occurrence with no block left fires at the reminder's anchor. The next firing is the earliest due, not the next occurrence's, as blocks need not follow the occurrences' order.
- **Found on the way:** habits sharing a tracker shared one pause, as their state was keyed by tracker. It is keyed by habit now.

### 3.7 Timed intervals — ADR 07

**Decided:** an activity is an item of kind ACTIVITY.
- All tracked time is in one `time_span` table on `item_id`. A trigger refuses to delete an activity that still has spans.
- **Several timers can run at once.**
- A span counts wholly for **the day it started**.
- A day's total is the union of the spans that started that day, and a week's total is the sum of its days.
- Manual entry and editing apply to every owner.
- **Owner answers, 2026-10-02:** a span running past a limit (12 hours to start with) asks the person to keep it, end it at a time they pick, or end it at the limit, and counts as running until answered; marking a task done or skipped, or deleting a task or habit, ends its running spans, while a habit's Log does not; an activity is never deleted forever, so no tracked time is lost to a purge.

**Acceptance:** `cases/07-timelog.jsonl`, 9 cases.

**Built (2026-10-02):** totals in `com.factotum.core.time`; spans and activities in `com.factotum.data.time`. The cases pass as tests (`TimeCasesTest`); the category half of `chronicle-activity-and-category-totals` passes with §3.8's labels (`LabelCasesTest`). What the build settled, none of which changes the decision:
- **An activity** is an item with no dates, an `archived` flag, and optionally an icon and a colour; an activity or a habit has a manual `sort_order`, fractional as Tendril's, which the planner now follows inside a block.
- **A span has five ADR 01 groups**, one per thing written apart: its start (with its owner and planned run), its end, its deletion, when a long run was last kept, and its comment. Each write touches only what it changes, so a stop, a deletion, a "keep", a start time and a comment made on different devices all survive the merge, and nothing reopens or revives a span. Times are kept to the second. A span stays on its owner and is timed only on a task, habit or activity. That it ends no earlier than it starts is checked where it is written, not in the database: start and end merge apart, and a row the database refused would stop every later import; totals count such a span as nothing. A deleted span, or one on a deleted owner, is not edited again (Chronicle); deleting twice changes nothing.
- **Totals** add each personal day's union of the spans started on it; a running span counts up to now; a span whose owner is deleted, or a habit whose tracker is deleted, does not count. Seconds are kept and minutes shown rounded down, as both apps round once at the end.
- **Goals on an activity** name the activity item. Their windows are Chronicle's (the day, the week from Monday, the month from the 1st, a milestone the last 400 days), built from day totals.
- **Deleting an activity** deletes its live spans and goals in the same write (Chronicle). An activity is never deleted forever (owner, 2026-10-02): the repository refuses, and a trigger refuses the row's delete. A purge on one device could otherwise take time another device logged before they synced.
- **The owner's answers:** a timer running past the limit (12 hours by default, a PERSONAL setting since slice 09, §3.9) since it started, or since the person last said to keep it, is listed to ask about (`runningLong`); "end it at the limit" ends it that long after. Marking a task done or skipped, resolving an occurrence, deleting a task or habit, or deleting a habit's tracker ends its running timers in the same write; resolving a past occurrence of a repeating task leaves a timer started after it running. A device that learns of a finished task or a deleted owner from a peer ends its timers when it imports it (`endFinished`, run after each import). A habit's Log does not stop a timer.

### 3.8 Labels — ADR 08

**Decided:** one `label` vocabulary (name, colour, `applies_to`, `sort_order`). Each owner keeps its cardinality:
- a page carries many, through `page_label`;
- an item (ACTIVITY or HABIT), a tracker or a page database carries one.

Names are unique ignoring case. A new label takes a colour derived from its name, which can then be changed. Labels sync as rows.

**The word on screen is "Label".** "Tag" keeps Tendril's meaning: a Select property.

**Owner answers, 2026-10-02:** two labels with the same name (ignoring case), made or renamed on devices that then sync, merge into the one made first, which keeps its colour and scope; a label's scope (everything, activities, trackers) is chosen and can change, and narrowing it only hides it from the other pickers; a label's time total counts every activity and habit carrying it, overlapping time once.

**Acceptance:** `cases/08-tagging.jsonl`, 10 cases.

**Built (2026-10-02):** `com.factotum.core.label` and `com.factotum.data.label`. Six of the ten cases pass as tests (`LabelCasesTest`), with the owner's answers and ADR 07's category total; the four that need a page (`tendril-page-many-labels`, `tendril-database-doorway`, `tendril-page-delete-no-orphans`, and the page half of the vocabulary) come with §3.12's pages. What the build settled, none of which changes the decision:
- **A label has five ADR 01 groups** (name, colour, scope, order, deletion), and an item's or a tracker's `label_id` is a group of its own, so a rename and a recolour made apart both stand, and a label deleted on one device never brings back a tracker deleted on another.
- **Names are unique by the repository, not by an index**: two devices make the same name apart, and a database rule a merged row broke would stop every later import. Names are compared trimmed, in one Unicode form (NFC), ignoring case; a new label's colour is Tendril's for its name.
- **The merge** (owner, 2026-10-02) runs after every import: of the live labels with one name, all but the one with the lowest id (ULIDs begin with the time, so the one made first) are deleted with `merged_into` naming it. Nothing that carried them is rewritten: readers take a merged label as the label it went into, so a merge never overwrites a label a person chose meanwhile on another device. Deleting a label clears what carried it or any label merged into it.
- **No foreign key on `label_id`**: a label is never deleted for good, and a key would only add a table rebuild; readers take a missing or deleted label as none (Tendril's habit label had no key either).
- **Scope** is where a label is offered: activities get labels for everything and for activities, trackers for everything and for trackers, habits for everything (ADR 08). A label outside the scope is refused when set; narrowing the scope leaves what carries it alone.
- **Upgrades drop the app's triggers first.** Adding the label columns made Room rebuild `item`, and SQLite checks every trigger when the rebuilt copy is renamed into place: the span rule, which names `item`, stopped the upgrade. Before Room upgrades an older file, the app now drops its own triggers, which it makes again on every open; a test upgrades a version 9 file holding them.
- **A label's time total** is the union of the spans on every activity and habit carrying it, or a label merged into it (owner, 2026-10-02); Chronicle's pie summed overlapping activities twice.

### 3.9 Settings — ADR 09

**Decided:** **scoped-live.** The owner chose this against the recommendation. Every key is declared once with a scope:
- **PERSONAL** keys sync live through a `setting` table and ride in the backup.
- **DEVICE_PREF** keys stay local and ride in the backup.
- **DEVICE_STATE** keys stay local and never leave the device.
- **SECRET** keys go to the Keystore or DPAPI.

The device id is not a setting.

**Owner answers, 2026-10-02:** the day view's standalone-reminders switch is DEVICE_PREF; the long-timer limit (§3.7) is PERSONAL, default 12 hours; app lock is per device (its PIN a SECRET, its on/off and grace DEVICE_PREF); the personal day boundary (§3.6) is PERSONAL, default midnight. This slice builds the settings part of the backup only (export PERSONAL and DEVICE_PREF; restore writes only those); a full backup comes with the shells.

**Acceptance:** `cases/09-settings.jsonl`, 9 cases.

**Built (2026-10-02):** `com.factotum.core.settings` and `com.factotum.data.settings`. All 9 cases pass as tests (`SettingsCasesTest`): A and B share a folder, and C is a phone restored from A's backup. What the build settled, none of which changes the decision:
- **A typed registry** names each setting's key, scope, default and the values it takes; a value that does not read (unreadable, or one no version could mean, such as a timer limit under an hour) reads as the default. No upper bounds were invented. Setting a value to its default clears it, so a later default reaches it.
- **PERSONAL settings** are rows of a synced `setting` table, one ADR 01 group each, later stamp first. A row's id is `setting:` and its key, so two devices that set one key apart write one row; a key this version does not know travels as it came. DEVICE_PREF and DEVICE_STATE live in a local `device_setting` table no export reads. SECRET goes to a `SecretStore`; the Keystore and DPAPI ones come with the shells (Tendril's `SecretStore` and `FileAiKeyStore` are the code to port). Tendril's AI key and Equipoise's endpoint key are two secrets.
- **Repositories read the day boundary and the timer limit on every call** through a required `PersonalSettings`, so a change imported from another device applies at once and no repository can be built that ignores them.
- **The backup's settings part** carries the PERSONAL rows with their stamps, so restoring an old backup never outranks a newer value here or on a peer, and the DEVICE_PREF values; a restore writes only settings this version knows, of those two scopes, with values they take. App lock is never turned on by a restore, nor at all before this device has its PIN.
- **Recovery:** a database made anew after a corrupt one was set aside reads this device's own folder files on its first import, so its settings and data come back with no peer; its DEVICE settings go back to defaults (ADR 09).

### 3.10 Search — ADR 10

**Decided:** one FTS4 table, `search_fts(text, kind, row_key)`.
- It uses the `unicode61` tokenizer, which folds accents.
- Triggers on every source table keep it current, including on sync import.
- Queries AND prefix terms. Block hits get snippets.
- The index is local and rebuildable.

**Owner answers, 2026-10-03:** what was written under an archived activity or tracker stays findable; nothing deleted, or under something deleted, shows; finished tasks, events and reminders show with a mark; names come first, then text inside by its own time, newest first; search starts at two letters.

**Acceptance:** `cases/10-search.jsonl`, 7 cases.

**Built (2026-10-03):** `com.factotum.data.search`. The cases that need no page pass as tests (`SearchCasesTest`): `chronicle-all-kinds`, `chronicle-tombstone-leaves`, the Log half of `chronicle-any-write-path`, `chronicle-accents-folded` (on an item's title) and the item half of `shared-one-search`; the page and block halves come with §3.12. What the build settled, none of which changes the decision:
- **The index is `search_fts(text)` and a plain `search_key(doc, kind, row_key)`**, whose `doc` is each entry's FTS document id: a trigger removes an entry by its key in about 0.04 ms, where finding it by a column FTS4 does not index scanned the index (13 ms at 50,000 entries). `unicode61` with `remove_diacritics=2` folds case and accents.
- **Sources:** every item's title, a tracker's name, a Log's label and note, a session's comment. A deleted row, a blank text, and an archived activity's or tracker's own name leave the index by trigger; whether what a hit belongs to is deleted (a deleted tracker's Logs, a deleted task's sessions, a subtask under a deleted parent, a habit whose tracker is deleted) is read when searching.
- **Kept current by triggers** made again on every open, which import writes fire like any other; **rebuilt on open** when the index holds a different number of entries than rows belong in it: an upgrade (whose triggers were dropped for it), a restore or a recovery.
- **Queries:** words of letters and digits (with any accent written apart), each a prefix, all required, from two letters on; hits are read in chunks under SQLite's 999 variables. Names come first, then text inside, newest first by its own time; a name's time is its item's date. Done or skipped tasks and reminders and one-off events that have ended are marked finished.

### 3.11 Occurrence edits — ADR 11

**Decided:** one insert-once `occurrence_edit` log for every repeating item.
- Scopes: OCCURRENCE, DAY, WEEK, FROM and EXTRA.
- `changes` holds only the fields an edit sets. Edits apply in ADR 01 stamp order, field by field.
- A move is one edit with `moved_to`.
- **A clash on one occurrence asks the person**, like §3.1's schedule prompt.
- Renaming a series renames its moved occurrences.
- Tasks gain "this week" and "from now on".

**Acceptance:** `cases/11-occurrence-edits.jsonl`, 10 cases.

**Built (2026-10-02):** the engine in `com.factotum.core.recurrence` (`OccurrenceEdits.kt`), the log in `com.factotum.data.item`. All 10 cases pass as tests: on the engine (`OccurrenceEditsTest`, with `tools/occurrence_sim.py`'s fixture) and across two syncing devices (`OccurrenceEditSyncTest`). Habits come with slice 06, so the cases' habit stands in as a repeating event, and the field that merges silently beside a retime is `title` rather than `block`; both are non-schedule fields under ADR 11. What the build settled, none of which changes the decision:
- **An OCCURRENCE edit names the series' own date-time**; DAY, WEEK and FROM reach occurrences where they are at that point, moved and added ones too, as `tools/occurrence_sim.py` applies them. Only one occurrence moves: `moved_to` is an OCCURRENCE field, and a new pattern for a day or week is a FROM edit with `week_days` (Tendril's "weekly" move) or a rule.
- **An added occurrence is keyed by its edit**, so it never replaces the series' occurrence at the same time.
- **A FROM edit with a rule or `week_days`** repeats the item differently from its date, starting afresh there (as Tendril's split series did). Each day follows the latest-created pattern dated on or before it.
- **A clash is computed, not stored.** Each edit lists the ids of the edits on the same place its author had seen, live or undone; ADR 11 said a base stamp, but one stamp cannot tell that a third device never saw an edit. Two live OCCURRENCE or FROM edits on one place, from two devices, neither having seen the other, that set a same schedule field to different values, make a question, until an edit that has seen both settles it.
- **An answer is a new edit that has seen both.** Keeping one re-sets its schedule fields, and the other's title still merges. Keeping both (one occurrence only) also adds an occurrence where the earlier edit had put it, under an id made from that edit, so two devices keeping both make one. Two devices answering differently make two corrections that clash in turn, as ADR 01's answers do. Edits are insert-once: a trigger refuses any change but the one undo.
- **The completion log names an occurrence by its date-time** (the series' own, or an added one's), so two occurrences on one day are resolved apart.
- **Habit fields this version does not apply** (block, sort_order, rule_patch, pause) are kept as raw JSON in `changes`, so nothing a newer peer wrote is lost on a round trip.
- **Reminders fire on the edited occurrences**: a skipped one is quiet, a moved or retimed one fires at its new time; an added occurrence on a whole-day item fires at the anchor unless it was given a time.

### 3.12 Page merge — ADR 12

**Decided:** **per-row+revive.**
- Blocks, property values, canvas nodes and edges, and database views are rows with §3.1 stamps and tombstones. Relations stay add-only, and the property schema stays upsert-by-uid.
- Block order is a fractional key.
- A later edit to any part restores a trashed page. **[Amended]** This is a deliberate exception to §3.1's group rule, and it applies to pages only.
- On a clash within the same paragraph, the later text wins. The losing part (block, cell or canvas node) goes to History, and a "replaced by a sync" notice appears.

**Owner answers, 2026-10-03:** a later edit brings back a deleted block; trashing a page trashes its sub-pages, "delete forever" purges them, and revive brings back trashed parents; the "replaced by a sync" notice syncs, shows everywhere until dismissed once, and counts a title clash; journal days follow the personal day boundary; Select options are rows; the slice is built as 12a (pages, blocks, page labels, search, History, revive, notice), 12b (databases), 12c (canvas), 12d (journal, relations, templates), with images, formulas and rollups, and rows as tasks in §7 step 3.

**Acceptance:** `cases/12-page-merge.jsonl`, 8 cases.

### 3.13 Sync folder layout — ADR 13

**Finding [Measured]:** with ADR 01's merge, every layout that delivers every version is lossless, so the layouts differ in cost and risk. At one year of data:
- **Rewriting each device's whole state** costs hundreds of MB of writes a day (Chronicle's snapshot: 900 MB/day; Tendril's per-area files: 411 MB/day).
- **Shared files** produce conflict copies, and lose a wiped device's losing edit.
- **One file per row** passes Android's 10,000-file slowdown within a year.
`decisions/13-folder.md` has the evidence, the simulator, a reviewed model and the scores.

**Decided:** **device-log+copies** (owner, 2026-10-01).
- Each device writes only under `devices/<device-id>/`, so ordinary use makes no conflict copies.
- Exports append the versions written since the last export, including versions imported from peers, to `log-<seq>.jsonl` segments of up to 16 KiB. Every write replaces the whole segment atomically.
- Every 64 segments the device writes `snapshot.json` (compact JSON) and deletes its older segments.
- Exports follow the last local write by 30 s. Readers keep a device-local read position per file, and merge, then delete, any `.sync-conflict-` copy.

**Requirements, whatever is synced** (`decisions/verify/13-folder/workload.md`):
1. Firing a reminder writes nothing that syncs. Fire bookkeeping is device state, and occurrences come from the rule (§3.4).
2. Folder exports are debounced, although the database may be written on every keystroke.
3. Every folder write is an atomic replace (temp file, then rename). Where Android's SAF cannot do that, the reader tolerates a torn file.
4. Synced files are compact JSON, never pretty-printed.
5. The device-id file is excluded from Android Auto Backup and device transfer, so two devices never share an identity.

**Acceptance:** the 4 cases in `cases/13-folder.jsonl` pass through the real importer and exporter, under a Syncthing double in the tests.

**Built (2026-10-01):** `FolderSync` in `:data` (`com.factotum.data.sync`). The 4 cases pass as tests (`FolderSyncTest`), with a Syncthing double that follows the simulator's rules. Nine more folder tests, and tests of the line format and the export timing, cover what the cases do not reach. `tools/mutants.py 13` shows that each rule is needed: without it, named tests fail. What the build settled, none of which changes the decision:
- **Snapshots are `snapshot-<seq>.jsonl`**, one record per line like the segments, where the ADR said `snapshot.json`. The sequence number in the name tells a reader a snapshot is new without opening it.
- **A local outbox decides what to export.** Every local write and every import that changes a row queues it. A stamp cursor would not work: a version imported from a peer can carry an older stamp than anything this device has exported.
- **An import commits in chunks of at most 2,000 lines.** Each chunk is one transaction, holding the merge, the read position it reached and the clock. A peer's 16 MB snapshot therefore neither fills memory nor holds the write lock for long, and a crash only means the rest is read again. The merge in `:core` stays synchronous: what a chunk can touch is loaded first, merged in memory, and written back.
- **The purge registry is looked up by id** (`SyncStore.purge(id)`), never loaded whole, because it never shrinks. Only a snapshot reads all of it.
- **Read positions are per file, in bytes.** A peer file is read only once it has grown. A last line with no newline is left for a later read, and a file that shrank (a torn SAF write) is read again from the start.
- **Lines this version cannot read are skipped.** When the set of synced tables changes (an upgrade), the read positions are dropped and every peer file is read once more, so a record for a table this version lacked is applied after the upgrade. Peers' snapshots and segments hold their whole state, so nothing skipped is lost.
- **A cloned device id:** copies are merged, then deleted. A conflict copy in a device's own folder also makes it re-read its own files, because the side that won the clash is not its own writing. Only a new id for one of the two devices ends the clashes; requirement 5 keeps that from arising. Owed: on finding such a copy, the device also takes a new id (ADR 09's file), which needs the app's identity wiring.
- **Tables reach the importer through `RowTable`**, one per synced table. Slice 02 brings the first real one; the tests use tables held in memory.
- **The folder** is `DirectorySyncFolder` on Windows and in app storage. A SAF folder on Android's shared storage comes with the Android shell.
- **Exports are queued by triggers** on every synced table and on the purge registry (slice 02), so no write path can forget the outbox.
- **A row whose parent has not arrived waits.** Sync gives no order between files, so a subtask or a completion can arrive before its parent. Each table names the parents a row needs (`RowTable.parents`), and before each chunk is applied, a line whose parent is neither here nor in the chunk is kept in `sync_waiting` (once per line). After every import, the waiting lines whose parents have arrived are applied. A line whose parent was purged is dropped, because the purge already meant the cascade. Foreign keys are deferred, and a snapshot lists parents first.
- **A line the database still refuses** is applied again one line at a time, as a backstop. One refused with its parents present breaks its table's rules, and is dropped and counted as skipped, never kept waiting.
- **A deleted row takes its local merge state with it**: a trigger clears its base and pending questions, whether the merge removed it or a foreign key's cascade did.
- **A row that does not fit its table** (missing groups, wrong value types) is skipped like an unreadable line.
- **Owed:**
  - starting the export from the queue writes through `exportAfterQuiet`, which needs the app's process wiring;
  - paging `RowTable.all()`, so a snapshot is written without holding every row at once.

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
- `search_fts` and `search_key` (§3.10);
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
2. **Schema slices in ADR dependency order:** 01 → 02 → 03 → 04 → 11 → 06 → 07 → 08 → 09 → 10 → 05 → 12. Each slice is done when its ADR cases pass as tests against the real implementation (§3). Spikes 1 and 3 run with slice 10. Spike 5 needs the Android shell and a device, so it runs with the shell (step 4). **Slice 01: done 2026-10-01** (§3.1), with its folder importer and exporter (§3.13). **Slice 02: done 2026-10-01** (§3.2). **Slice 03: done 2026-10-02** (§3.3). **Slice 04: done 2026-10-02** (§3.4), except spike 5, which needs the Android shell. **Slice 11: done 2026-10-02** (§3.11). **Slice 06: done 2026-10-02** (§3.6), with PLANNED. **Slice 07: done 2026-10-02** (§3.7). **Slice 08: done 2026-10-02** (§3.8), but for its page cases, which come with slice 12. **Slice 09: done 2026-10-02** (§3.9). **Slice 10: done 2026-10-03** (§3.10), but for its page cases, which come with slice 12, and the device halves of spikes 1 and 3, which come with the Android shell. **Slice 05: done 2026-10-03** (§3.5).
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

Status: 2, 4 and 6 are done (`docs/spikes-2026-10-01.md`). 1 and 3 ran on the desktop with slice 10; their device halves, and 5, run with the Android shell (§7).

1. **FTS5 on target devices.** It could replace FTS4 (§3.10) if every target SQLite build has it. Room's annotations don't generate it. **Desktop measured 2026-10-03:** the bundled SQLite is 3.50.1 with FTS5 compiled in, and makes the FTS4 index with `remove_diacritics=2` (`SearchCasesTest`). The phones use Android's own SQLite (3.28 on Android 11, the minimum, which has `remove_diacritics=2`); their FTS5 is measured with the Android shell.
2. **PLANNED recurrence. Done.** All 8 RRULE-form rules match once DTSTART is aligned and set times use a RULE_SET. PLANNED matches on 500/500 random weeks once HABIT has `block_id` and `duration_min`.
3. **Triggers on both drivers.** §3.10's search triggers and §3.7's spans trigger install and fire on Android and on Windows. **Desktop: holds** (every trigger test runs on the bundled driver). The device half runs with the Android shell, which has no code yet.
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
9. **The sync folder's layout. Decided 2026-10-01:** ADR 13, device-log+copies (§3.13).
10. **A habit whose tracker is deleted. Decided 2026-10-02:** the habit goes with it; the tracker is created with the habit (§3.6).
11. **Reminders on an "n a day" habit. Decided 2026-10-02:** each occurrence reminds at the start of its block (§3.6, part b). Tendril gave such habits no reminder at all.

## 11. Next Steps

1. The owner reviews this spec, especially §10.
2. Settle §10.1 to §10.4 with the owner.
3. Run the spikes in §9 before the feature code that depends on them.
4. Turn each ADR's cases into the first tests of the real schema (§3).
