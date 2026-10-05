# 16. Databases in pages

Status: **decided 2026-10-05: O6, hybrid with items** (the owner's choice, the recommended option). The owner asked: "What would score as an improvement upon Notion's or other apps' current model?"

## Why it came up

The navigation mockups listed "Databases" as a destination of its own. The owner pointed out that databases belong inside pages, as in Notion.

The model as built (SPEC §3.12, slice 12b) has no such destination: a database is a page made into one, reached through the tree. But it also has **no way for a database to sit inside an ordinary page** among its text, as Notion's inline databases do. Nor can it show a database in more than one place.

## Survey

`16-databases-survey.json` answers 12 questions per app, each with a source URL. It covers Notion, Obsidian Bases, Anytype, Logseq and Capacities.

- **Notion is the only app where a database owns its rows.** A page belongs to one database, and reaches others only through relations.
- **The other four are queries over one pool of items.** A note or object can be in any number of views without being copied.
- **"A project page shows its tasks"** is, everywhere, a view embedded in the project page and filtered on *this page*:
  - Obsidian's `this`;
  - Capacities' "This object";
  - Notion's linked view on a relation;
  - Anytype's inline query on a relation.
- **Removing a view or query never deletes the items it showed** (Anytype, Obsidian).

Tendril, and so Factotum, already combine the two models. A database's rows are its sub-pages **and** every page carrying its doorway label (`PageDatabase.kt:45`, `LabelMembership.kt:80`).

## Options

`options/16-databases.json`, counted against the schema as built:

| Option | Model | Growth |
|---|---|---|
| O1. Full page | As built | 0 |
| O2. Inline owned | O1, plus a DATABASE block: a database made inside a page is that page's sub-page, shown in place (Notion inline) | 1 block kind |
| O3. Linked views | O2, plus a VIEW block: a view of any database with its own layout, sort and filter, including *this page* | 2 block kinds, +1 column |
| O4. Query only | A database is a saved query over every page (Obsidian, Logseq); no owned rows | +2 columns, 2 block kinds; rewrites slice 12b membership |
| O5. Hybrid | O3, plus a saved query on properties beside the doorway label (Anytype's types, sets and collections together) | +2 columns, 2 block kinds |
| O6. Hybrid with items | O5, plus views over Factotum's own items (tasks, events, habits) by label | +3 columns, 2 block kinds |
| C0. Control | a page shown in a database is copied into it | — |

There's a precedent for the new blocks. Factotum already has `CANVAS`, a canvas page shown inside a page ("not a second canvas model", Tendril §0.6.3). A DATABASE block works the same way: no second data model.

## Scores

`tools/dbview_sim.py` simulates every option against 17 behaviour cases (`cases/16-databases.jsonl`), two-device merges included. `tools/score_contest.py` then builds the front. In full: `16-databases-scores.md`.

| Option | Factotum | Owner | Reference | Tendril | All | Growth | Status |
|---|---|---|---|---|---|---|---|
| O1 | 0.75 | 0.17 | 0.00 | 1.00 | 0.47 | 0 | front |
| O2 | 1.00 | 0.67 | 0.00 | 1.00 | 0.71 | 1 | front |
| O3 | 1.00 | 1.00 | 0.33 | 1.00 | 0.88 | 3 | front |
| O4 | 1.00 | 0.83 | 0.67 | 0.50 | 0.76 | 4 | dominated by O5 |
| O5 | 1.00 | 1.00 | 0.67 | 1.00 | 0.94 | 4 | front |
| O6 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 5 | front |
| C0 | 0.25 | 0.17 | 0.00 | 0.25 | 0.18 | — | control: it fails the 4 cases it must (the scorer exits 0) |

**What each step up the front buys:**
- **O2** adds a database inside a page, which moves and trashes with its page.
- **O3** adds:
  - a project page showing its own tasks;
  - one database in many places, each with its own filter;
  - removing a view without touching the pages.
- **O5** adds rows by property, wherever the pages live.
- **O6** lets a page list real Factotum tasks, events and habits by label, without making them pages. No surveyed app can do this: each keeps its notes and its tasks in one pool of one kind.

**Why O4 is dominated.** It costs as much as O5 and loses Tendril's owned rows. It also loses "trashing a database trashes its rows", and the inline database's rows outlive their page.

## What the scores do not say

- The simulator models **membership and sync semantics**, not Room tables. The growth counts are by hand, against the built schema.
- The **owner** and **reference** cases state what is wanted, taken from the owner's words and the surveyed apps. Unlike contests 01–14, they are not behaviour an owner app already has.
- A **view over items** (O6) overlaps with Today and the agenda. Where such a view sits among the screens is a T5 question.
- The **"this page"** filter needs a field naming the project page. A relation column (`relation_link`, built) or a page mention would do. Which of the two counts is a T5 detail.

## Owner's choice (2026-10-05)

**O6, hybrid with items.** Factotum keeps what is built, a database page whose rows are its sub-pages plus the pages carrying its doorway label, and adds four things:
- **A DATABASE block:** a database made inside a page is that page's sub-page, shown in place. It moves and trashes with the page.
- **A VIEW block:** a view of any database, owning its own layout, sort and filter, including *this page*. Removing the block never touches the pages it showed.
- **A saved query on properties**, beside the doorway label. A page matching it is a row wherever it lives.
- **Views over items** (tasks, events, habits) by label, so a page can list its project's real tasks.

**Growth:** 2 block kinds and 3 columns (`page_view`'s owning block, its source as pages or items, and the database's query). Nothing built is reworked.

**When:** the data layer is built before T5 (pages and databases), as its own slice.
