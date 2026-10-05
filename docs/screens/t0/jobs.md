# Jobs, screens and the cadence each one implies

This is the input to the navigation scoring (decision 15, Q2 and Q3). The owner asked for it on 2026-10-05: analyse use **by purpose**, screen by screen, starting from what each feature already implies. A journal is one page per day, so it is opened daily; a ringing alarm arrives and is never sought.

**How to read the columns**

- **Cadence by design** is what the data layer itself fixes, with the SPEC section that fixes it. **open** means nothing in the design sets a cadence, and the owner's use decides it.
- **Arrives / sought**:
  - **arrives** means it is pushed to the person (notification, alarm, dialog, a prompt at the next open), so navigation never carries it;
  - **sought** means the person goes looking, so navigation pays for it in taps and clicks.
- **Device lean** is only where the content makes one device clearly better (space for a canvas, a pocket for an alarm). It is marked **open** otherwise.

## J1 Catch something quickly

| Screen / feature | Cadence by design | Arrives / sought | Device lean |
|---|---|---|---|
| Quick add (a task, event or reminder from one line). Tendril's QuickAddField has tokens; Chronicle has a QuickAdd card; Mnemo has a quick-add widget | open, though all three apps put it a tap or less away | sought, ideally **from anywhere** | both. Tendril's Windows build has a QuickAddWindow |
| One-tap reading on a tracker with a default value (Chronicle's "Set a default value (1-tap logging)") | as often as the tracker is read | sought | phone |
| **Not in the SPEC yet: home-screen widgets.** Chronicle, Mnemo and Equipoise all ship Glance widgets (due soon, next up, pinned reminder, quick add, energy) | glanced several times a day where they exist | arrive on the home screen | phone only |

## J2 See what's next

| Screen / feature | Cadence by design | Arrives / sought | Device lean |
|---|---|---|---|
| Today / agenda: items due, reminders, habits due today, "n a day" occurrences by block | **daily**; items, habits and reminders are all laid out per personal day (§3.2–§3.6, the day boundary in §3.9) | sought | both |
| Calendar: day, week and month, with the day-view toggle for standalone reminders (off by default, §3.3) | **daily** at a glance, **weekly** to plan | sought | week and month lean to desktop |
| A whole-day item reminded before its anchor (§3.4) | per item | arrives | — |

## J3 Answer a prompt (all of these arrive)

| Screen / feature | Cadence by design | Device lean |
|---|---|---|
| Ringing ALARM: Android full screen via setAlarmClock; Windows tray toast that keeps ringing as its nag says (§3.4, §10.4) | per firing | both |
| NOTIFICATION reminder with snooze; the snooze syncs and holds for that one firing (§3.3) | per firing | both |
| Missed alarm: on Android one late notification; on Windows shown once at the next start (§3.4, §10.4) | when one is missed | both |
| "The system stopped this app's alarms" at the next start after a force-stop (§3.4) | rare | phone |
| Sync clash: keep mine, take theirs, or keep both, only when a schedule changed on two devices (§3.1, §3.11) | rare, after a sync | both |
| "Replaced by a sync" notice inside a page, with History (§3.12) | rare | both |
| Outcome at next open: "how did that tool go?", asked once and then lapsed (§7 step 3) | after each regulation tool | phone |
| Timer past its limit (12 h by default): keep, end at a picked time, or end at the limit (§3.7) | rare | both |
| Burnout notice: once-only, over 14 personal days (§7 step 3; the alert is not wired yet) | rare, **triggered** | both |
| App lock PIN (per device, §3.9) | **every open**, when switched on | both |

## J4 Do it and log it

| Screen / feature | Cadence by design | Arrives / sought | Device lean |
|---|---|---|---|
| Habits: Log (yes, a rating, or a number above 0), "n a day", rolling ("due again N days after the last Log"), pause; no streaks (§3.6, §0.1.3) | **daily**, and **several times a day** for "n a day" habits, each reminding at its block's start (§3.6b) | sought, or from the reminder | phone |
| Tick a task, or resolve an occurrence (done or skipped) (§3.2, §3.11) | **several times a day** | sought, or from the reminder | both |
| Timers: start and stop an activity, several at once; finishing a task stops its timer (§3.7) | **daily** for whatever is timed | sought | both |
| Tracker reading: a number, yes or no, a rating, or a choice; a number habit's daily amount is a DAY goal (§3.6) | **daily** per tracker | sought | phone |
| Checklist: tick an item, then reset (a resettable template, such as a morning routine) (§7 step 3) | **daily** by design | sought | phone |

## J5 Check in with myself

| Screen / feature | Cadence by design | Arrives / sought | Device lean |
|---|---|---|---|
| Check-in: mood and energy, optional pleasantness, no numbers shown; may be about a past day (§3.5) | **several times a day** is Equipoise's model; at least daily | sought (a reminder could push it) | phone |
| Regulate: which way to go, and the tools (§7 step 3) | after a low check-in | **arrives from the check-in** | phone |
| Ledger: three masking scales, one row per day (`masking:<day>`) (§7 step 3) | **once a day** by design | sought | phone |
| Sensory log: five channels, recorded when it happens (§7 step 3) | when it happens | sought | phone |

## J6 Plan ahead

| Screen / feature | Cadence by design | Arrives / sought | Device lean |
|---|---|---|---|
| Item editor: task, event or reminder; recurrence (RRULE, RULE_SET, random days or window, rolling, planned); reminders (offset, anchor, NOTIFICATION or ALARM, nag, sound, vibration, exact) (§3.2–§3.4) | per new or changed item | sought | both |
| This occurrence only: move, skip or edit one occurrence (§3.11) | occasional | sought | both |
| Week planner: PLANNED habits laid into time blocks, the week confirmed (§3.6b) | **weekly** by design (a confirmed week) | sought | desktop |
| Time blocks (Tendril's five defaults) (§3.6b) | rare (setup) | sought | both |
| Calendar links: external calendars, local to the device (§2) | rare (setup) | sought | phone |

## J7 Write and think

| Screen / feature | Cadence by design | Arrives / sought | Device lean |
|---|---|---|---|
| **Journal**: one page per personal day under one "Journal" page, dated until renamed, one page however many devices open it (§3.12) | **daily** by construction | sought | open |
| Page: blocks, images (at most 2048 px, stored by hash), labels (§3.12, §7) | open | sought | long writing leans to desktop |
| Canvas and mind map: cards, lines, frames, page cards (§3.12) | open | sought | desktop (space) |

## J8 Organise and look things up

| Screen / feature | Cadence by design | Arrives / sought | Device lean |
|---|---|---|---|
| **Search and the quick switcher**: from 2 letters, names first and then newest, finished items marked (§3.10) | **several times a day**, the way into everything | sought | both. Tendril has Ctrl+K |
| Page tree | whenever pages are open | sought | desktop (side pane) |
| Database: table, board and timeline views; formulas and rollups; relations; rows as tasks (§3.12, §7) | open | sought | desktop |
| Templates (structure-only copies) (§3.12) | occasional | sought | open |
| Road Map: links between pages (§3.12) | occasional | sought | desktop |
| Labels: one vocabulary, merges, scope (§3.8) | rare to manage, but labels are used everywhere | sought | both |

## J9 Look back over time

| Screen / feature | Cadence by design | Arrives / sought | Device lean |
|---|---|---|---|
| Tracker detail: charts by trend, hour, weekday, month day; day, week, month and quarter (Chronicle) | open | sought | both |
| Saved charts: activity minutes and tracker means per personal day; moving average and goal line (§7 step 3) | open | sought | desktop |
| Goals, including goals on tracked time (§3.6, §3.7) | open; a DAY goal shows inline daily | sought | both |
| Time totals per activity and per label (§3.7, §3.8) | open | sought | both |
| Stability trend, in words only (§3.5) | open | sought | phone |
| Page History: revisions and what a sync replaced (§3.12) | rare | sought, or from a notice | desktop |

## J10 Look after the app

| Screen / feature | Cadence by design | Arrives / sought | Device lean |
|---|---|---|---|
| Settings, in two sections, "On every device" and "On this device" (§3.9, decision 15). Examples: the day boundary, the timer limit, reminders on or off, app lock, theme | rare | sought | both |
| Sync folder: choose it, its status, sync now (§3.13) | rare, plus a glance when something looks stale | sought | both |
| Trash: pages, items, checklists, a database's rows (§3.12, §7) | rare | sought | both |
| Backup (settings only for now, §3.9) | rare | sought | both |
| Onboarding: Equipoise's "what helps when low" question, in Mixed mode, the sleep tracker (§7 step 3) | **once** | arrives | phone |
| About, with llama.cpp's MIT notice (§6) | rare | sought | both |

## Features no screen holds yet (the owner places them)

These are not decided, and are not decided here.
- **Home-screen widgets** (Android). Three source apps have them, and §0.1.5 keeps every sole-owner feature. None is in the SPEC yet.
- **The on-device LLM** (Equipoise's llama.cpp, in `:llm` with no code yet). It has no screen or entry point.
- **Tendril's opt-in Claude text verbs** (Settings → Claude, key on this device). Factotum's SPEC does not mention them, so it is open whether they move across.
- **A global quick-add on Windows** (Tendril's QuickAddWindow). Whether Factotum has a system-wide hotkey is open.

## Owner's answers (2026-10-05)

- **Pages, databases and canvas are daily, on both devices.** They are a working surface, not a reference shelf.
- **Looking back is a weekly review.** Charts, goals, time totals, tracker detail and the stability trend can sit deeper than the daily jobs.
- **A check-in happens when something is noticed.** It is event-driven: rare, but it must be quick to reach when it is wanted. It is not Equipoise's several-a-day model.
- **Features that move across:**
  - Android widgets;
  - the on-device LLM;
  - a Windows global quick-add;
  - and, added by the owner, **natural-language input where appropriate** (Tendril's quick-add tokens are one such input today).
- **Dropped: Tendril's opt-in Claude text verbs.** This is an owner-accepted exception to §0.1.5 ("no single-app feature is dropped"), recorded in decision 15 and the SPEC.
