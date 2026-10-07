# 17. Screens T1: shared parts

Status: **questions answered 2026-10-07; screens being mocked one at a time.** Method: decision 15, "every screen, one at a time, before colour".

T1 holds the parts every later tier reuses:
- the header and the bar;
- item rows;
- the capture sheet;
- the Hub sheet;
- the date, time and repeat pickers;
- label chips;
- toasts and dialogs;
- empty and error states.

Mockups are in `docs/screens/t1/screens.html`.

## Owner's answers (2026-10-07)

| Question | Answer |
|---|---|
| What a row shows | **Title only** is the default for the screens. The three variants (title only; title plus one quiet line; title plus chips) are mocked side by side in a chapter of their own, to decide later. |
| Acting on a row | **No swipes at all.** |
| Capture | **Parsed chips under the line.** The text stays as typed, and tapping a chip fixes it or drops it. |
| Destructive actions | **An Undo toast, no dialog.** Dialogs only for what Trash cannot bring back: emptying Trash, discarding an unsaved page. |
| Date and time | **Presets first** (Today, Tomorrow, This weekend, Next week, No date), then a month grid and the time. Typing a date also works. |
| Repeat | **A plain-language builder with a live sentence**: common choices as a list, "Custom" for the fields, and the rule read back with its next three dates. |
| Empty states | **One plain sentence and one action.** No illustration, no cheer, no guilt. |
| Labels | **A dot and the text.** The dot takes the user's colour later. |

Already decided elsewhere: a done or skipped item folds into "Done today · n" (decision 15).

**To confirm on the first row screen:** with no swipes, a row is finished by tapping its circle, with Undo. The other actions (move, skip this one, edit, label, delete) are reached by opening the item. A long-press menu was offered and not chosen.

## Screens

| # | Screen | Status |
|---|---|---|
| T1.1 | Header and bar | in progress |
| T1.2 | Item rows (title only), plus the row-variants chapter | to do |
| T1.3 | Capture sheet | to do |
| T1.4 | Hub sheet (cards) | to do |
| T1.5 | Date and time picker | to do |
| T1.6 | Repeat builder | to do |
| T1.7 | Label chips and picker | to do |
| T1.8 | Toasts and dialogs | to do |
| T1.9 | Empty and error states | to do |
