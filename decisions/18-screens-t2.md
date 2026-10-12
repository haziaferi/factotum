# 18. Screens T2: items, calendar and alarms

Status: **in progress.**
- Approved: the alarm ringing and an item's page (owner, 2026-10-12).
- Still open: the Reminders list, what a calendar day holds, and Calendar.

The method is decision 15's: every screen, one at a time, before colour. The owner's T2 answers (2026-10-10) are at the end of `decisions/17-screens-t1.md`.

The scorer is `tools/screens/t2_opt.py`. Its files live in `docs/screens/t2/`:
- `t2-options.html`, every option drawn;
- `t2-scores.html`, the measures and the Pareto fronts;
- `t2-<part>.json`;
- the phone references, in `t2-references.json` and `t2-refs.json`.

Each part has a control that must lose, or the scores page fails.

## The owner's picks (2026-10-12)

| Part | Pick | Next |
|---|---|---|
| The alarm ringing | **full, slide, one, upcoming** | approved |
| An item's page | **inplace, all, auto** | approved |
| The Reminders list | **next, days**, and Skip in **the item page's in-place form**, for consistency | new option, scored below |
| What a calendar day holds, and its filter | "everything" looks too much like the control | rescore |
| Calendar | needs different axes | rescore |

## The alarm ringing: approved (owner, 2026-10-12)

**The pick:**
- **Full screen**, over the lock screen and over any app.
- **Slide to dismiss.**
- **One Snooze**, whose length is set in the reminder.
- **Skip for today from the upcoming notification**, a quiet notification an hour before.

The pick is on the front (`t2-alarm.json`):
- **Half-asleep:** of the full-screen options, only hold or slide with Skip off the ringing screen keep both risks at 0. A tap aimed at Snooze cannot land on a dismiss or Skip target (`aim_risk` 0), and a blind slap dismisses nothing (`slap_risk` 0). Snooze is missed 0.16% of the time.
- **Its costs against tap-to-dismiss:**
  - reach is 1.49 bits against 0.75 (the knob sits at the track's start);
  - dismissing takes about 0.5 s;
  - Dismiss holds 45% of the two targets' visual mass, against 35%.
- **Skip from upcoming:** 2.5 actions, against 2 on the ringing screen. The ringing screen keeps only two things on it.
- **Reference:** Fossify Clock over the locked phone (run 5) is the same form, a full screen with a slide knob.

**To keep when drawing it:**
- The knob stays plain, and Snooze stays the larger target.
- Dismiss's pull must not grow past the measured 0.452.

## An item's page: approved (owner, 2026-10-12)

**The pick:**
- **In place:** the row grows where it is, its fields under its title, and a tap on the title closes it.
- **All fields**, set or not. An unset field reads "Add a reminder".
- **Autosave**, with T1.8 H's Undo toast after a change.

It had the lowest sum of the twelve options (49.5):
- Today's rows stay in view while the item is open;
- an edit takes one action;
- nothing is lost on leaving.

On Windows, the row grows in Today's column.

## The Reminders list: in-place Skip scored (2026-10-12)

The owner's pick:
- **next, days**;
- and, for consistency, **Skip in the same in-place form as an item's page**.

That form was not in the space. Added as `skip: inplace`:
- the row grows in place as an item's page does;
- its fields are listed, with **Skip for today** under When;
- the skipped row folds into "Done today" (decision 15).
- That makes 2 actions: the row, then Skip.

Measured, for next and days (`t2-rem.json`):

| Skip | Actions | Reach (bits) | Hidden | Set off by a scroll |
|---|---|---|---|---|
| **inplace** | **2** | **3.276** | 0 | 0 |
| selection (T1.8 I) | 2 | 3.914 | 0 | 0 |
| page | 3 | 3.436 | 0 | 0 |
| swipe | 1 | 3.390 | 1 | 1 |

In place dominates selection and page on every measure. Only swipe is cheaper, and T1's answer is "no swipes at all".
