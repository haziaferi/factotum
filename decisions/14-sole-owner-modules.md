# 14. The sole-owner modules (§7 step 3)

Status: **owner answers recorded 2026-10-03.** Date: 2026-10-03. Owners: Chronicle (checklists, saved charts), Equipoise (regulation), Tendril (rows as tasks, formulas and rollups, images).

Three source surveys mapped what step 3 ports: Chronicle's checklists and saved charts, Equipoise's regulation module, and the three Tendril features owner answer 8 of ADR 12 deferred. They found these facts:

- **Chronicle:**
  - A checklist is standalone, with a manual reset and no history.
  - A saved chart stores its type, its sources as one delimited string, and a range.
  - Both merge whole-row, so a tick and a rename made apart lose one.
- **Equipoise:**
  - Only check-ins, the masking ledger and regulation outcomes are written in production.
  - The burnout index and the sensory log have no writer, and the "outcome at next open" machine is unwired.
  - The index's sleep, sensory and per-day energy inputs are undefined.
- **Tendril:**
  - A row and its task are two records that can disagree.
  - Formulas name properties by display name.
  - Images ride the folder as files that are never collected.

The owner answered:

**Order**
1. **Build the simplest first:**
   1. formulas and rollups;
   2. checklists and saved charts;
   3. regulation;
   4. database rows as tasks;
   5. images.

**Checklists and saved charts**
2. **A delete wins over an edit made apart** (checklist, item or chart), with restore from the Trash, as for labels, check-ins and time spans.
3. **A reset starts a new run**: a tick made before the reset is cleared even when it syncs after it, and a tick made after the reset stays.
4. **Checklists are found by search**: names first, then item text.
5. **Checklists and saved charts have a manual order** that syncs, newest first until moved.

**Regulation (SPEC open item 5)**
6. **The burnout index is computed on demand**, as the other check-in engines are. Each device may keep a cache it can rebuild; the index is never synced.
7. **Sleep comes from a tracker** the person chooses (a number in hours), named in a personal setting.
8. **A missing input reweighs the rest**: the weights are spread over the inputs present, so not tracking sleep does not make the threshold harder to reach.
9. **A sensory log's load is the mean of its channels, and a day's load is the mean of its logs.** How many levels a channel has waits for the screens.
10. **A day's energy is the mean of every energy value that day**, one-axis taps included.
11. **An outcome whose check-in was undone stops teaching** the direction engine.

**Formulas and rollups**
12. **A formula names a property by id and shows it by name**, so a rename never breaks it.
13. **A rollup counts live related rows only.**
14. **A formula does not reach into related rows yet**, as in Tendril; rollups cover related rows.

**Database rows as tasks**
15. **A row and its task have one title**: renaming either renames both.
16. **Every row is a task while "rows as tasks" is on**, later rows and labelled pages included.
17. **Deleting a row's task deletes the row**: it is one thing.
18. **A task edit made on a device that had not seen the row trashed brings the row back**, as a cell edit does (ADR 12).
19. **Turning "rows as tasks" off trashes the tasks**, and the columns keep the tasks' last values.
20. **Unbinding a column freezes the task's current value** in it.
21. **"Keep both" is not offered** on a row-task's date clash.
22. **A repeating row shows its next open occurrence**: ticking it resolves the current one.
23. **A Recurrence column is edited as "every n days, weeks or months"**; a richer rule from the task side is shown read-only.

**Database rows as tasks, second round (owner, 2026-10-04)**, after the Tendril survey:

26. **Editing a repeating row's Date cell asks every time** whether it moves the whole series or only the next open occurrence (an occurrence move, ADR 11). The data layer offers both; the question waits for the screens.
27. **Unbinding a Recurrence column while the task carries a richer rule leaves the cell empty**; the task keeps its rule.
28. **Setting an interval on a row with no Date starts the task today**, and the Date cell shows it.
29. **Keeping both for one occurrence of a repeating row-task is allowed**: it adds an occurrence to the same task, never a second row or task. Answer 21 covers only the task's own date clash.
30. **A page that stops being a row of any database with rows as tasks has its task trashed** (Tendril's rule; it follows from answers 16 and 17).

**Images**
24. **An inserted image is scaled to about 2048 px on its longest edge.**
25. **An image replaced on two devices keeps the later one**, and the earlier goes to History with a notice, as text does.

**Images, second round (owner, 2026-10-04)**, after the Tendril survey:

31. **A deleted block's picture stays in the sync folder for 30 days**, then is collected when nothing refers to it; a block revived within that time keeps its picture.
32. **Page History keeps its pictures**, so restoring an old version brings the picture back.
33. **Every inserted image is scaled and re-encoded**: longest edge at most 2048 px; photos as JPEG at about quality 85, images with transparency as PNG; an animated GIF or WebP keeps its first frame.
34. **Photo metadata is stripped on insert**: rotation is applied to the pixels, then camera details and location are removed before the picture syncs.

**Waiting for the screens:**
- automatic checklist resets;
- run history;
- linking a checklist to an item;
- how charts draw missing days, pies, several bars and choice trackers;
- chart types and ranges;
- the once-only burnout alert across devices;
- crisis contacts;
- where an owed outcome is asked;
- a partly answered ledger day;
- the "labelled pages become tasks" dialog;
- how `round` treats a half;
- a Gallery card's cover.

## Consequences: fixes, not questions

- **Chronicle:**
  - Every edit checks the row is live inside its write.
  - Items are never made under a deleted checklist.
  - The order is fractional.
  - A deleted chart no longer shows.
  - A chart's sources are rows, so two devices each adding one keep both.
- **Equipoise:**
  - The outcome-at-next-open machine is wired.
  - A tool is a stable key, not a sentence.
  - An untapped ledger scale stays empty.
  - The ledger day is the personal day.
  - The index's stored fields are reconciled with what it computes.
- **Tendril:**
  - Seeding a row's task is de-duplicated by a derived id.
  - A restored row brings its task back, and a purged row purges it.
  - Formulas and rollups read bound task columns, and sort and filter see computed values.
  - A deleted block's image is collected from the folder.
  - "Keep both" never copies a row-task's link.
