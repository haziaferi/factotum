# Actions inventory (T1.8 G workshop, draft 2, 2026-10-09)

Draft 1 used the data layer's words as they stand, and those disagree between kinds: "delete" meant three different things, and some kinds had restore while others had none. This draft fixes one vocabulary for the screens first, then checks every kind against it. Where the data layer falls short of the vocabulary, the gap is listed at the end.

## The vocabulary (one word, one meaning, everywhere)

| Word on screen | What it does | Where |
|---|---|---|
| **Delete** | The element goes to Trash. An Undo toast shows for 7 s. | On the element, and on a selection. |
| **Restore** | It comes back from Trash, to where it was. | In Trash only. |
| **Delete forever** | It is gone for good, on every device. Held. | In Trash only. |
| **Empty Trash** | Delete forever for everything in Trash. Held. | Trash, fixed top right (owner). |
| **Archive** | It stays, out of the lists, and keeps its history. Unarchive brings it back. Not a deletion. | Activities (Chronicle's). |
| **Remove** | Takes one thing off another; nothing is deleted. | A label off an element, a line off a canvas, a reminder off a task. |
| **Undo** | Reverses the last action, from its toast only. | The toast. |

Nothing else is called delete. "Move to Trash", "Trash", "Purge", "Eliminate" and the like are not used.

## a. A single element: the matrix

Columns: **Done** (Done / Log / Check); **When** (date, time, repeat: the When sheet); **Label** (put on or remove); **Reminder** (add or remove); **Move** (to another day, list, parent or place); **Delete** (to Trash, then Restore or Delete forever there); **Archive**.

✓ = the kind has it. — = the kind does not have it. **gap** = the screens need it, but the data layer lacks part of it (see the end).

| Element | Done | When | Label | Reminder | Move | Delete | Archive | Its other actions |
|---|---|---|---|---|---|---|---|---|
| Task | ✓ Done | ✓ | — | ✓ | ✓ day | ✓ **gap** (no Restore) | — | rename; importance; an occurrence: skip, move this one, change this day / week / from now on |
| Event | — | ✓ | — | ✓ | ✓ day | ✓ **gap** (no Restore) | — | rename; an occurrence as for a task |
| Reminder (on its own) | **?** | ✓ | — | — | ✓ time | ✓ **gap** (no Trash) | — | alert: notification or alarm |
| Alarm (ringing) | — | — | — | — | — | — | — | snooze; dismiss (T2) |
| Habit | ✓ Log | ✓ (plan the week, time blocks) | ✓ | ✓ | — | ✓ **gap** (no Restore) | — | pause / resume; undo the log |
| Tracker | ✓ Log | — | ✓ | — | — | ✓ **gap** (no Restore) | — | goals; undo the last log |
| Activity (time) | — (start / stop) | — | ✓ | — | — | ✓ **gap** (no Trash; never deleted forever, owner 2026-10-02) | ✓ | goals; its time spans: edit, Delete **gap** |
| Checklist | — | — | — | — | ✓ | ✓ **gap** (no Delete forever) | — | rename; reset; its lines: Check, edit, Move, Delete |
| Page | — | — | ✓ (many) | — | ✓ parent | ✓ | — | rename; icon; relate to a page; revisions; save as a template |
| Database (a page) | — | — | ✓ | — | ✓ parent | ✓ | — | properties; options; views; rows as tasks |
| Database row (a page) | ✓ Done, if rows are tasks | ✓ date, due | ✓ (many) | — | ✓ | ✓ | — | its cells |
| Canvas card / frame | — | — | — | — | ✓ place | ✓ **gap** (no Trash; a later edit brings it back) | — | text; colour; fold; to front; connect |
| Label | — | — | — | — | ✓ order | ✓ **gap** (no Trash) | — | rename; colour; scope |
| Chart | — | — | — | — | ✓ | ✓ **gap** (no Delete forever) | — | rename; range; sources |
| Check-in entry | — | — | — | — | — | — (Undo only) | — | mood; energy; note |

**Labels:** per SPEC §3.8, only pages (many), habits, activities, trackers and databases (one each) carry labels. Tasks, events, reminders, checklists, charts and canvas cards carry none.

## b. A screen's own actions

**Every screen:**
- Search and Settings ⚙ in the header (T1.1).
- Add, through the capture line; what it adds follows the screen (T1.3).
- The label filter bar (T1.7), on screens whose elements carry labels.
- The Hub, in the bar.

| Screen | Its own actions, besides those |
|---|---|
| Today | Edit home (re-pin slot 5); the "Done today · n" fold |
| Calendar | Day / week / month; go to today |
| Reminders | Sort **?** |
| Pages | New page or database (from a template too); sort **?** |
| Check-in | History |
| Trash | Empty Trash (held, fixed top right) |
| Settings › Labels | Edit (reorder) |
| Habits, trackers, time, charts | T3 decides |

## c. A selection

A selection offers only what makes sense for many at once, and only what every selected element has (the matrix's columns):

| Selection | Actions |
|---|---|
| Tasks and events | Done (tasks); When (one date for all); Delete |
| Habits | Log; Label; Delete |
| Pages, rows | Move; Label; Delete |
| Trash | Restore; Delete forever (held) |
| Labels | Delete |
| Mixed kinds (Today) | Only what all of them have: Delete, and When if all are tasks or events **?** |

**How a selection starts.** A long press already opens a row's other actions (decided 2026-10-07), and a long press is also the usual way to start selecting. Ways out:
1. **A long press selects.** The selection bar shows that element's actions, so one element selected *is* the old long-press menu, and more taps add rows. One model for one or many.
2. **A long press opens the menu,** with "Select" in it; then taps add rows.
3. **Select is a screen's own action**; circles turn into checkboxes.
4. **Drag down the left column** to select a run of rows.

**Growing and ending a selection:** tap to add or remove; select all; ✕ or Back ends it.

## Gaps between the vocabulary and the data layer

These are data-layer work the screens depend on. The fixes, unless the owner rules otherwise:

1. **No Restore:** tasks, events, habits, trackers. Their delete exists, and so does their delete forever, but nothing brings them back from Trash. Add Restore.
2. **No Delete forever:** checklists, charts. They would sit in Trash for good. Add it.

**Owner questions** (behaviour choices, not gaps):

3. **No Trash at all:** reminders, labels, activities, time spans, canvas cards, and a database's options and views. Should Trash hold them, or is the 7-second Undo their only way back?
4. **A database property** is deleted forever at once (ADR 12). Through Trash, or kept as it is?
5. **An activity is never deleted forever** (owner, 2026-10-02). In Trash it has Restore but no Delete forever, and Empty Trash leaves it. Or should Delete on an activity simply archive it?
6. **A reminder has no Done.** Add one, as Mnemo had?
