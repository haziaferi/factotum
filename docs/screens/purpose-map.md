# Purpose map

Factotum's screens by purpose (owner, 2026-10-13): what each screen does, where it comes from (or that it is new), its tier and status, and what it overlaps with. It replaces grouping by source app, and it is what the Hub's groups are drawn from once it is settled. Rendered to purpose-map.md by tools/screens/purpose_map.py, which also checks that every screen in the navigation scoring (nav_score2.SCREENS) and every Hub entry (tier_t1.FEATURES) has a place here. A draft: it is refined as the tiers go.

Generated from `purpose-map.json` by `tools/screens/purpose_map.py`; edit the JSON, not this page.

## Purposes

| | Purpose | Its job | Screens |
|---|---|---|---|
| P1 | **Catch and find** | get something in, or get to anything, from anywhere | 5 |
| P2 | **What's next** | see and act on what is due: commitments, deadlines, reminders | 8 |
| P3 | **Daily basics** | the basic things that get a day done (make the bed, brush teeth, shower), as if-then cues, with no judgment; a clear reference on a low day | 3 |
| P4 | **Measuring** | record an amount (water, exercise, studying, knitting, time) and, if wanted, aim at one | 6 |
| P5 | **Looking back** | see how things went over time; a weekly review (owner, 2026-10-05) | 6 |
| P6 | **Noticing myself** | notice how I am, and what helps; event-driven (owner, 2026-10-05) | 6 |
| P7 | **Planning the week** | lay out the week: blocks, planned habits, outside calendars | 3 |
| P8 | **Writing and knowing** | write, keep and find what I know: pages, journal, databases, canvas, lists | 9 |
| P9 | **Looking after the app** | make the app work: settings, sync, trash, backup, lock, labels | 9 |

## P1 Catch and find

_get something in, or get to anything, from anywhere_

| Screen | Comes from | New in Factotum | Tier | Status | Overlaps |
|---|---|---|---|---|---|
| Capture line (one line, parsed chips) | Tendril QuickAddField (tokens); Chronicle QuickAdd card; Mnemo quick-add widget | the chips, corrected by a tap, and one line for every module | T1.3 | approved |  |
| Search and the quick switcher | Tendril (Ctrl+K) |  | T6 | pending |  |
| Hub sheet | **none** | Factotum's own navigation (decision 15); its groups will follow this map | T1.4 | approved (groups to redo from this map) |  |
| Home-screen widgets (Android) | Chronicle; Mnemo; Equipoise (one-tap energy) |  | none yet | pending (owner: they move across) |  |
| Windows global quick-add | Tendril QuickAddWindow |  | none yet | pending (owner: it moves across) |  |

## P2 What's next

_see and act on what is due: commitments, deadlines, reminders_

| Screen | Comes from | New in Factotum | Tier | Status | Overlaps |
|---|---|---|---|---|---|
| Today | Tendril (calendar and tasks for today); Mnemo Home |  | T1 | approved | Reminders list, Calendar: Week (planner) · Month · 3 days, Capacity-scaled day (a shorter list on a low day) |
| Calendar: Week (planner) · Month · 3 days | Tendril Calendar | Week as a paper-planner grid of day cells | T2 | approved | Habit planner (confirm the week into time blocks) |
| Day screen (opened from a day) | Tendril day view |  | T2 | approved |  |
| An item's page (in place) | Tendril item editor; Mnemo Edit |  | T2 | approved |  |
| This occurrence only (move, skip, edit one) | Tendril (ADR 11) |  | none yet | pending |  |
| Reminders list | Mnemo Home; Chronicle Remind |  | T2 | approved | Today |
| The alarm ringing, and Skip from upcoming | Chronicle AlarmActivity; Mnemo |  | T2 | approved |  |
| Missed alarm and 'alarms were stopped' notices | Mnemo; Chronicle |  | none yet | pending (they arrive) |  |

## P3 Daily basics

_the basic things that get a day done (make the bed, brush teeth, shower), as if-then cues, with no judgment; a clear reference on a low day_

| Screen | Comes from | New in Factotum | Tier | Status | Overlaps |
|---|---|---|---|---|---|
| Habits: today's basics as if-then cues | Tendril habits (the data: blocks, Log, rolling, pause); Equipoise (the no-shame rules G05/G06, the low-capacity path) | the owner's definition (2026-10-13): basic daily actions, cues, no history in the list | T3a | scored on the old axes; to rescore | Routine checklists (resettable, e.g. Morning routine), Capacity-scaled day (a shorter list on a low day) |
| Routine checklists (resettable, e.g. Morning routine) | Chronicle checklists |  | T3a | pending (owner: routine checklists join Daily basics) | Habits: today's basics as if-then cues |
| Capacity-scaled day (a shorter list on a low day) | Equipoise G04 |  | T3a or T4 | pending; whether it moves across is to check in the SPEC | Today, Habits: today's basics as if-then cues |

## P4 Measuring

_record an amount (water, exercise, studying, knitting, time) and, if wanted, aim at one_

| Screen | Comes from | New in Factotum | Tier | Status | Overlaps |
|---|---|---|---|---|---|
| Trackers (water, exercise, studying, knitting) | Chronicle Track |  | T3b | pending | Activities and timers (several at once), Goals, inside their tracker or activity |
| Log sheet (a number, a rating, yes or no, a choice) | Chronicle; Loop's picker (reference) |  | T3b | pending |  |
| Activities and timers (several at once) | Chronicle activities and sessions; Tendril time logs |  | T3b | pending | Trackers (water, exercise, studying, knitting) |
| A timer past its limit (keep, end at a time, end at the limit) | Factotum §3.7 (owner, 2026-10-02) | the question itself | T3b | pending (it arrives) |  |
| Editing a session | Chronicle |  | T3b | pending |  |
| Goals, inside their tracker or activity | Chronicle goals |  | T3b | pending | Trackers (water, exercise, studying, knitting), Activities and timers (several at once) |

## P5 Looking back

_see how things went over time; a weekly review (owner, 2026-10-05)_

| Screen | Comes from | New in Factotum | Tier | Status | Overlaps |
|---|---|---|---|---|---|
| This week (the weekly review) | Tendril Review |  | T3c | pending | Saved charts, Time totals, Stability trend (in words), Ledger and sensory history |
| Saved charts | Chronicle Charts |  | T3c | pending | A tracker's detail and charts, Time totals |
| A tracker's detail and charts | Chronicle Data |  | T3c | pending | Saved charts |
| Time totals | Tendril time logs; Chronicle |  | T3c | pending | Saved charts |
| Stability trend (in words) | Equipoise |  | T3c or T4 | pending | This week (the weekly review) |
| Ledger and sensory history | Equipoise |  | T3c or T4 | pending | This week (the weekly review) |

## P6 Noticing myself

_notice how I am, and what helps; event-driven (owner, 2026-10-05)_

| Screen | Comes from | New in Factotum | Tier | Status | Overlaps |
|---|---|---|---|---|---|
| Check-in | Equipoise (the grid); Tendril check-ins |  | T4 | pending |  |
| Regulate sheet, and the outcome at the next open | Equipoise |  | T4 | pending (it arrives from the check-in) |  |
| Ledger (three masking scales, once a day) | Equipoise |  | T4 | pending | Journal (one page a day) |
| Sensory log | Equipoise |  | T4 | pending | Journal (one page a day) |
| Burnout notice (a triggered state) | Equipoise |  | T4 | pending (it arrives) |  |
| Onboarding question (what helps when low) | Equipoise |  | T6 | pending (once) |  |

## P7 Planning the week

_lay out the week: blocks, planned habits, outside calendars_

| Screen | Comes from | New in Factotum | Tier | Status | Overlaps |
|---|---|---|---|---|---|
| Habit planner (confirm the week into time blocks) | Tendril PlanView |  | none yet | pending; could be a mode of Calendar's Week | Calendar: Week (planner) · Month · 3 days |
| Time blocks (setup) | Tendril |  | T6 | pending |  |
| Outside calendars (links, on this device) | Tendril |  | T6 | pending |  |

## P8 Writing and knowing

_write, keep and find what I know: pages, journal, databases, canvas, lists_

| Screen | Comes from | New in Factotum | Tier | Status | Overlaps |
|---|---|---|---|---|---|
| Journal (one page a day) | Tendril Journal |  | T5 | pending | Ledger (three masking scales, once a day), Sensory log |
| Page tree | Tendril Pages |  | T5 | pending |  |
| A page (blocks, images, labels) | Tendril Pages |  | T5 | pending |  |
| Databases in pages (table, board, timeline views) | **none** | decision 16 (O6): inline databases with views, to improve on Notion; the source apps had plain pages only | T5 | pending |  |
| Canvas and mind map | Tendril Canvas |  | T5 | pending |  |
| Templates | Tendril |  | T5 | pending |  |
| Road Map (links between pages) | Tendril Road Map |  | T5 | pending |  |
| Page History (revisions, what a sync replaced) | Factotum §3.12 | the sync-replaced notice and its History | T5 | pending |  |
| One-off lists (packing, shopping) | Chronicle checklists |  | T5 | pending (owner: they stay lists; where they live is open) |  |

## P9 Looking after the app

_make the app work: settings, sync, trash, backup, lock, labels_

| Screen | Comes from | New in Factotum | Tier | Status | Overlaps |
|---|---|---|---|---|---|
| Settings ('On every device', 'On this device') | all four apps | the two sections (decision 15) | T6 | pending |  |
| Sync folder and its status | **none** | ADR 13's folder layout | T6 | pending |  |
| The sync clash question | **none** | ADR 01/11 | T1 (dialog) | approved as a dialog form |  |
| Trash (Delete, Restore, Delete forever for every kind) | **none** | one vocabulary for every kind (2026-10-09) | T6 | pending |  |
| Backup | Factotum §3.9 |  | T6 | pending |  |
| App lock | Chronicle (PIN) |  | T6 | pending |  |
| Labels (one vocabulary, any element) | Tendril areas; Chronicle categories | merged into one global vocabulary (2026-10-10) | T1.7 (chips), T6 (manager) | chips approved; manager pending |  |
| About (llama.cpp's MIT notice) | all four apps |  | T6 | pending |  |
| On-device language model | Equipoise (llama.cpp, no screen there) | no app gave it a screen; where it sits is open | none yet | pending (owner: it moves across) |  |

## Screens with no parent app

- **Hub sheet** (P1): Factotum's own navigation (decision 15); its groups will follow this map
- **Databases in pages (table, board, timeline views)** (P8): decision 16 (O6): inline databases with views, to improve on Notion; the source apps had plain pages only
- **Sync folder and its status** (P9): ADR 13's folder layout
- **The sync clash question** (P9): ADR 01/11
- **Trash (Delete, Restore, Delete forever for every kind)** (P9): one vocabulary for every kind (2026-10-09)

## Screens whose purposes overlap

| | Strength | Screens | Why |
|---|---|---|---|
| O1 | strong | Habits: today's basics as if-then cues, Routine checklists (resettable, e.g. Morning routine), Capacity-scaled day (a shorter list on a low day) | the basic things to get through today, with no judgment: a routine checklist is the owner's definition of habits; Equipoise's no-shame rules are the rules set for Habits |
| O2 | strong | Trackers (water, exercise, studying, knitting), Activities and timers (several at once), Goals, inside their tracker or activity | record an amount and aim at one: a timer is a way to enter a time amount; a goal always belongs to one tracker or one activity |
| O3 | strong | This week (the weekly review), Saved charts, A tracker's detail and charts, Time totals, Stability trend (in words), Ledger and sensory history | see how things went over time; time totals is a chart of activities, tracker detail a chart of one tracker |
| O4 | medium | Calendar: Week (planner) · Month · 3 days, Habit planner (confirm the week into time blocks), Time blocks (setup) | lay out the week; two things are now called a planner |
| O5 | medium | Check-in, Ledger (three masking scales, once a day), Sensory log, Journal (one page a day) | note how I am; the journal is free writing, the rest structured and quick |
| O6 | weak (settled) | Today, Reminders list, Calendar: Week (planner) · Month · 3 days | what is next; Reminders keeps managing repeating reminders as its own job |

## The owner's answers

- 2026-10-13: re-cut T3 and T4 by purpose (T3a Daily basics, T3b Measuring, T3c Looking back); it is refined as we go.
- 2026-10-13: Checklists split: routine checklists join Daily basics, one-off lists stay lists.
- 2026-10-13: the purpose map, once settled, decides how the Hub's elements are grouped.

_55 screens; 5 with no parent app; 9 approved._
