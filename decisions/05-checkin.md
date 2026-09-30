# ADR 05: Check-in, two scales for one gesture

Status: **decided: own-axis** (the owner chose against the recommendation; recorded as given). Date: 2026-09-30. Owners: Tendril and Equipoise.

## Verified facts

The facts were verified with `tools/verify.py`; the raw output is in `verify/05-checkin/`.

| App | Fact | Source | Map said |
|---|---|---|---|
| Tendril | `CheckIn(id, uid, date, at, mood: Int?, energy: Int?, deletedAt)`. A row carries **one** scale. There can be several rows a day, and the day's value is the latest live row of each scale, by `at`. The 1-5 range is only a doc comment and nothing enforces it. | `CheckIn.kt:14-38`; `CheckIns.kt:23,71` | partial (uid, deletedAt and one-scale missed) |
| Tendril | Mood levels are Awful, Bad, Okay, Good, Great, with hues slate to green-gold and no red by design. Energy has no colour. | `CheckIns.kt:16-23`; `CheckInRow.kt:130` | not stated |
| Tendril | **By design, no averages, counts or curves.** A check-in is never edited: a changed mind is a new row. There is no note, because the journal page is the words. Sync is insert-by-uid plus a tombstone that wins. | `CheckIns.kt:11`; `CheckIn.kt:16,19`; `SnapshotSyncOrchestrator.kt:2028` | not stated |
| Tendril | "Check-in" also names **habit completions** (`CheckInHabitUseCase`, and the review screen's count). That is a different table. | `CalendarViewModel.kt:121` | not stated (a naming collision; carried to contest 06) |
| Equipoise | `CheckInEntity(id, at, energy: Double, pleasantness: Double?, stability, note)`, with both axes in 0..1. `pleasantness = null` marks the widget's one-tap energy-only log. `Stability` is JUMPY, STEADY or FLAT, stored as a chip and read by no engine. | `Entities.kt:14-20`; `Types.kt:3-6`; `Repositories.kt:159` | partial |
| Equipoise | The DirectionModel splits at **0.5** on both axes. LowMoment scores `energy + w·pleasantness` against a floor, a 30-logged-day quartile and a 120-day quartile, and leaves energy-only rows out. BurnoutIndex reads energy only and is not wired into the app yet. | `DirectionModel.kt:25,34`; `LowMoment.kt:29-47`; `BurnoutIndex.kt:25-52` | "the direction engine reads it" (confirmed) |
| Equipoise | `CheckInShape` says **"even grids only"**, so no cell lands on the 0.5 midline. The screen itself hard-codes an odd `GRID = 5` and ignores the stored shape setting. | `CheckInShape.kt:25`; `CheckInScreen.kt:34` | not stated (a defect) |

## Scores (`05-checkin-scores.md`, run by `tools/checkin_sim.py`)

Each owner's real check-ins are stored in each option, then read back by a port of that owner's reader: Tendril's labels, and Equipoise's quadrant, LowMoment and even-grid rule.

| Option | Equipoise | Shared | Tendril | Columns | Status |
|---|---|---|---|---|---|
| onto | 0.67 | 1.00 | 1.00 | 3 | front (Tendril's "Okay" lands on the engine's 0.5 midline, unmarked) |
| **onto+levels** | 1.00 | 1.00 | 1.00 | 4 | **front, the only full coverage** |
| own-axis | 1.00 | 0.00 | 1.00 | 5 | dominated (Tendril check-ins never reach Equipoise's engines) |
| tendril-ints | 0.33 | 1.00 | 1.00 | 2 | front (loses continuous values and the midline rule) |
| two-tables | 1.00 | 0.00 | 1.00 | 7 | dominated |
| coalesce (control) | 0.33 | 1.00 | 0.67 | 3 | failed the 2 cases it was expected to fail, plus the midline |

## Recommendation

**onto+levels**: one `check_in` table.
- `energy` and `pleasantness` are REAL in 0..1, both nullable, with a CHECK that at least one is set.
- `source_levels` is 5 for a value written on a 5-step scale and NULL for a continuous one.
- `stability` and `note` are both nullable.
- Tendril's mood k is stored as pleasantness (k−0.5)/5, and its label and colour come back exactly.
- A 5-step value sitting on 0.5 (Tendril's "Okay") is sent to Equipoise's existing **Mixed** path rather than forced to one side of the quadrant.

**Fix, not a decision.** The check-in grid uses the even shape its own code demands, instead of the hard-coded odd 5.

## Open for the owner

1. **Is Tendril's mood the same axis as Equipoise's pleasantness?** Recommended: yes. Awful…Great is a pleasant/unpleasant (valence) scale, the axis the circumplex calls pleasantness. The measured alternative (`own-axis`) keeps it separate, and then Tendril-origin check-ins never inform the burnout or direction engines.
2. **Tendril's rule of no averages, counts or curves.** Should it carry over to the merged check-in screen, while Equipoise's engines still compute in the background as they do now?

## Decision

On 2026-09-30 the owner decided both open questions.

1. **Mood is its own axis** (`own-axis`). Mood is not pleasantness. The table is one `check_in` table:
   - `mood` is an INT 1-5 with a CHECK. Tendril never enforced that range; Factotum does, as a fix.
   - `energy` and `pleasantness` are REAL in 0..1 and nullable, with a CHECK that at least one of mood, energy or pleasantness is set.
   - `source_levels`, `stability` and `note` are all nullable.

   **What the owner accepts with this.** A quick mood tap never reaches Equipoise's direction engine or its LowMoment assessment, because both need pleasantness. That is the measured loss `shared-one-history`. A quick *energy* tap still lands on the shared energy axis, stored as (k−0.5)/5 with `source_levels = 5`. It is treated like Equipoise's own widget energy-only row: BurnoutIndex, which reads energy only, may use it, and LowMoment leaves it out, as it already does with widget rows.
2. **No numbers on the check-in screen.** Tendril's rule carries over: no averages, counts or trend curves are shown. Equipoise's engines keep computing in the background, and what they produce appears only as their own outputs, such as a suggested direction or a low-moment prompt, never as a chart of the check-ins.
