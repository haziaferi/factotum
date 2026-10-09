# Actions inventory (T1.8 G workshop, draft 3, 2026-10-09)

Draft 3 takes in the owner's corrections of 2026-10-09:
- "Move" is split into When and Move;
- Snooze and Skip are named;
- the matrix is corrected kind by kind.

Where the owner's answers go beyond the data layer or the SPEC, the work is listed at the end.

## The vocabulary (one word, one meaning, everywhere)

| Word on screen | What it does | Where |
|---|---|---|
| **When** | Date, time and repeat, through the When sheet. Moving something to another day is a When change. | Anything that happens at a time. |
| **Move** | Where it sits: another parent, list or order, or a place on a canvas. Never a time. | Pages, rows, checklist lines, canvas cards, labels (order). |
| **Skip** | This occurrence does not happen; the next one stands. For a reminder or alarm it reads **Skip for today**. | Anything that repeats. |
| **Snooze** | While ringing only: rings again in a few minutes. Not a When change. | A ringing reminder or alarm (T2). |
| **Delete** | The element goes to Trash. An Undo toast shows for 7 s. | On the element, and on a selection. |
| **Restore** | It comes back from Trash, to where it was. | In Trash only. |
| **Delete forever** | It is gone for good, on every device. Held. | In Trash only. |
| **Empty Trash** | Delete forever for everything in Trash. Held. | Trash, fixed top right (owner). |
| **Archive** | It stays, out of the lists, and keeps its history. Not a deletion. | Activities (Chronicle's). |
| **Remove** | Takes one thing off another; nothing is deleted. | A label off an element, a reminder off a task, a line off a canvas. |
| **Undo** | Reverses the last action, from its toast only. | The toast. |

## a. A single element

Every element that can be deleted has all three of **Delete** (to Trash), **Restore** and **Delete forever** (owner, 2026-10-09). The matrix therefore lists what differs between kinds. **gap** = the screens need it and the data layer lacks it; see the end.

| Element | Done | When | Skip | Label | Reminder | Move | Archive | Its other actions |
|---|---|---|---|---|---|---|---|---|
| Task | ✓ Done | ✓ | ✓ if it repeats | ✓ **gap** | ✓ | ✓ order | — | rename; importance; an occurrence: change this day / week / from now on |
| Event | — | ✓ | ✓ if it repeats | ✓ **gap** | ✓ | — | — | rename; an occurrence as for a task |
| Reminder / alarm | — (no Done) | ✓ date, time, repeat | ✓ Skip for today, if it fires on several days | ✓ **gap** | — | — | — | alert: notification or alarm; Snooze while ringing |
| Habit | ✓ Log | ✓ (plan the week, time blocks) | — | ✓ | ✓ | — | — | pause / resume; undo the log |
| Tracker | ✓ Log | — | — | ✓ | — | — | — | goals; undo the last log |
| Activity (time) | — (start / stop) | — | — | ✓ | — | — | ✓ | goals; its time spans: edit, Delete |
| Checklist | — | — | — | ✓ **gap** | — | ✓ | — | rename; reset; its lines: Check, edit, Move, Delete |
| Page | — | — | — | ✓ (many) | — | ✓ parent | — | rename; icon; relate to a page; revisions; save as a template |
| Database (a page) | — | — | — | ✓ | — | ✓ parent | — | properties; options; views; rows as tasks |
| Database row (a page) | ✓ Done, if rows are tasks | ✓ date, due | ✓ if it repeats | ✓ (many) | ✓ if rows are tasks **gap** | ✓ | — | its cells |
| Canvas card / frame | — | — | — | — | — | ✓ place | — | text; colour; fold; to front; connect |
| Label | — | — | — | — | — | ✓ order | — | rename; colour; scope |
| Chart | — | — | — | — | — | ✓ | — | rename; range; sources |
| Check-in entry | — | — | — | — | — | — | — | mood; energy; note; undo only |

**Labels (owner, 2026-10-09):** tasks, events, reminders and checklists carry labels too. This amends ADR 08, which gave them to pages, habits, activities, trackers and databases only.

## b. A screen's own actions

**Every screen:**
- Search and Settings ⚙ in the header (T1.1).
- Add, through the capture line; what it adds follows the screen (T1.3).
- The label filter bar (T1.7).
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

A selection offers only what makes sense for many at once, and only what every selected element has:

| Selection | Actions |
|---|---|
| Tasks, events, reminders | When (one date for all); Skip (the repeating ones); Label; Delete; Done (tasks only **?**) |
| Habits, trackers | Log; Label; Delete |
| Pages, rows, checklists | Move; Label; Delete |
| Trash | Restore; Delete forever (held) |
| Labels, charts, canvas cards | Delete |
| Mixed kinds (Today) | Only what all of them have **?** |

**How a selection starts.** A long press already opens a row's other actions (decided 2026-10-07), and a long press is also the usual way to start selecting. Ways out:
1. **A long press selects.** The selection bar shows that element's actions, so one element selected *is* the old long-press menu, and more taps add rows. One model for one or many.
2. **A long press opens the menu,** with "Select" in it; then taps add rows.
3. **Select is a screen's own action**; circles turn into checkboxes.
4. **Drag down the left column** to select a run of rows.

**Growing and ending a selection:** tap to add or remove; select all; ✕ or Back ends it.

## The work these answers create (data layer and SPEC)

1. **Restore** for tasks, events, reminders, habits and trackers. Today they can be deleted, and deleted forever, but nothing brings them back.
2. **Trash, Restore and Delete forever** for activities, canvas cards, labels and charts.
   - Activities, canvas cards and labels have a delete with no Trash.
   - Charts have no Delete forever.
3. **Delete forever** for checklists.
4. **Delete forever on an activity:** this reverses the owner's 2026-10-02 rule that an activity is never deleted forever, so that no tracked time is lost. Deleting an activity forever takes its time spans with it, and its labels' time totals shrink. Its time spans keep a plain Delete **?**
5. **Labels on tasks, events, reminders and checklists:** an ADR 08 amendment. It needs a `label_id` on those rows, a schema bump, and scope values for them.
6. **A reminder on a database row,** when rows are tasks.
7. **Skip for today** on a reminder: a standalone reminder is an item, so `OccurrenceRepository.skip` should serve it. To check with a test.

**Still open:**
- Should a database's properties, options and views go through Trash? (ADR 12 deletes a property forever at once.)
- Sort on Reminders and on Pages.
- How a selection starts, and what a mixed selection offers.
