# Spec migration, 2026-11-21

`Factotum SPEC.md` v0.40 is migrated to project-spec-writer's format. The scope was migration only: no meaning was changed and no rulings were added, except the jobs table the owner asked to fold in (R04). Nothing is committed yet; the owner reviews the diff first.

## Result

- 202 rules: 194 decided (D), 1 owner rule (O, R09), 1 inherited (I, R10), 2 assumed (A, R196 and R197), 4 open (Q).
- `speccheck "Factotum SPEC.md"`: 0 BLOCK, 0 ASK, 0 REPORT; `open questions: 4 (R107, R108, R191, R192)`.
- `speccheck --base HEAD` raises one ASK: R09 enters the owner-rule kind. The owner approved this on 2026-11-21 ("0.1.7 as O-").
- `Factotum SPEC-history.md`: 284 rule rows, plus one `migrated` row naming 541abf9, the commit that holds the old file.

## Questions for the owner

1. R107 · An activity's usual length: how is it computed, for the timer limit of R106? None proposed: decision 19 T3b.3 leaves it owed. Your answer becomes R106's formula, and the code then replaces its `long_run_hours` setting.
2. R108 · The limit before any session: what limit applies before an activity has sessions to take a usual length from? None proposed. The answer completes R106.
3. R191 · Navigation: pattern, destinations and icons. None proposed, as the old spec left it to scoring. `decisions/15-screens.md` records the bar and the Hub as decided on 2026-10-07; this migration did not fold that in. If you confirm it, R191 becomes a decided rule.
4. R192 · Palette, type, shapes and density. None proposed: decision 15 holds palette slates with no pick.

Optional: R05, R06, R07, R08, R20, R81, R198 and R199 are standing answers with no stated reason. They are `D-` rules with `Since … · owner`, so a change to any of them still stops for you. A reason given for one makes it an `O-` rule.

## Owner decisions applied (2026-11-21)

- Migrate only. The file keeps its name, and the history goes in `Factotum SPEC-history.md`.
- The code's and the two briefs' citations are rewritten to rule numbers.
- Open items are carried as `Q-` rules.
- 0.1.7 becomes `O-`; the other standing answers stay `D-`.
- Acceptance lines with no source or test were drafted by the builder (listed below for review).
- `docs/screens/t0/jobs.md` is folded in as R04.

## Contradictions in the old spec, and how each was resolved

In every case below, the newer ruling clearly supersedes the older one. The replaced ruling sits in the rule's Not field.

- **Timer limit.** The PERSONAL 12 h setting (2026-10-02) was replaced by 3x the activity's usual length (2026-10-16): R106. The code still reads `long_run_hours`, noted in R106's Evidence.
- **Deleting an activity.** "Never deleted forever" (2026-10-02) was replaced by Delete forever with its spans (2026-10-09): R104.
- **Label scope and time totals** (2026-10-02) were replaced by global labels with no time total (2026-10-10): R110, R117.
- **Label cardinality.** The ADR's one label on an activity, habit, tracker or database was widened to every item kind and a checklist (2026-10-09): R111.
- **Archiving.** "Archived elements stay findable" (2026-10-03) was dropped with Archive (2026-10-09): R29, R97.
- **Snapshot name.** ADR 13's `snapshot.json` was replaced by `snapshot-<seq>.jsonl`, as the old spec itself said: R35.
- **Habit fields in an edit.** The block was kept raw (slice 11), then read (slice 06b): R76, R95.
- **A confirmed week.** It cleared the week (slice 11), then was laid out before other edits (slice 06b): R91.
- **Relations.** They were add-only (ADR 12), then made removable (owner, 2026-10-03): R178, R179.
- **Recurrence kinds.** The first list was incomplete. ROLLING (v0.12), RANDOM_TIMES and RANDOM_GAPS (v0.38) are joined into one table: R62.
- **Triggers on Windows.** Assumed in the old risks section, but measured as holding on the desktop in its spikes section. Only the Android half stays assumed: R196.
- **Entity names.** The old section 2 table used older names (`page_database_view`, `page_revision` as a moved entity). The current names come from the old data-model section: R18, R19.

Two dangling references were dropped rather than carried. The old 10.1 said it "settles §3.9's marker", but the old 3.9 holds no marker. "Constraint 0.14" is another document's number; it survives only in R81's Evidence.

## Independent review

Two Opus 5.5 reviewers each read half of the old spec, lines 1–278 and 279–631, against the whole new spec. Between them they checked about 620 rulings and reported 19 problems. Each one was checked against the old text, and 18 were fixed:

- **Missing.** The standing answers filter every other rule (now in the header); the `COALESCE` rule (R49); modules move as they are (R06); the importer is the only writer of remote rows (R12); relation-column links are removable, with placeholders from either side (R179); the journal and an unheard purge (R177); new rows start empty (R182); "chains" (R81).
- **Changed.** The engines read the moment, not the day (R134); a label's deletion reaches labels merged into it (R116); the schema check guards files only (R14); settings read on every call means the day boundary (R122).
- **Wrong as current.** The reversed timer limit was used as an example (R119).
- **Added.** Gates between build steps (R193, now "not stated" where the old spec says nothing); NOTIFICATION behaviour on Windows (R60, now "not ruled on"); SECRET keys and the backup (R118, narrowed to the settings part).
- **Misattributed.** The v0.40 gap fixes are now the builder's (R31, R104, R105); the force-stop notice is now the owner's (R61); `EntryEntity` was Chronicle's (R47).

One was kept: "Android widgets" and "natural-language input where appropriate" (R06) are the owner's own words in `decisions/15-screens.md:73` and `jobs.md`, which R06's Evidence now names.

Noted by a reviewer, not changed: two case files still hold givens that were later reversed: `decisions/cases/07-timelog.jsonl` (`chronicle-activity-delete-refused`) and `08-tagging.jsonl` (`chronicle-applies-to-scope`). Their tests were rewritten (`TimeCasesTest.kt:130`, `LabelCasesTest.kt:150`), but R98's and R109's "every case passes" reads them literally. The old spec had the same lines.

## Inconsistencies outside the old spec (not folded in)

- Decision 19's item page draws labels as a comma list, while R111 allows at most one label on a tracker or activity.
- `TrackerDao.kt:25` lists tracker units including `HOURS`. R102 (2026-10-16) says units are typed and never time.
- `Settings.kt` declares 8 keys no rule covers: `long_run_hours`, `burnout_threshold`, `crisis_contacts`, `default_alert_mode`, `first_run_done`, `sync_folder`, `window_frame`, `llm_model` (listed in R120's Evidence).
- Decisions 15, 17, 18 and 19 hold screen picks approved after v0.40 (T0's bar and Hub, T1 to T3, Review's 2026-10-28 rulings). Some change data rules (goal-line setting, ranges per tracker, a glyph per option). By the owner's choice they wait for a separate update.
- `ParamLogistic.kt:14` cites "SPEC v0.2 §3.2", a historical version, and was left as is.

## Dates and attribution

- Each version's date is its first commit, from `git log --follow` (`build/runlogs/spec-migration/versions.tsv`). v0.33 shares 1913622 with v0.34. Two edits after v0.40 (b2e8278, d044548) carry 2026-10-16.
- Four standing answers carry 2026-09-30, the date the old table gives, with 3f5fb8f, the first version holding them.
- A rule's Since names the owner when any of its history rows does, otherwise the builder, otherwise `unrecorded`. As a result, a change to any owner-decided rule raises an ASK.
- No ruling was dated by a range or left undated.

## Wording to review

All 202 rules carry `Since … · migrated`: the wording is carried over, and the owner has not reviewed it. That includes R04's condensed jobs table. Marking a rule `agreed rewording` or `own words` once reviewed is one edit plus one history row.

## Size

| File | Lines | Bytes |
|---|---|---|
| old `Factotum SPEC.md` (v0.40) | 631 | 102,454 |
| new `Factotum SPEC.md` | 2,873 | 171,370 |
| new `Factotum SPEC-history.md` | 289 | 27,908 |

Of the new spec, the derived rule index takes 10.6 KB and the acceptance list 24.9 KB. The rest is mostly field labels and the blank lines between fields. What left the spec:

- the revision-log table, now history rows;
- the old 10's closed items (2, 3, 7, 8, 9, 12) and 11's next steps, left to git;
- "Built (date)" status prose, now history rows and Evidence.

## Readers of the spec, updated

- **Code.** 27 citations in 20 Kotlin files are now `SPEC:Rnn`, so `speccheck --base` blocks a rule change that leaves its code behind. Only comment lines changed (checked against `git diff`). `:core` and `:data` compile for the desktop target.
- **Briefs.** `docs/workflow-prompt.md` and `docs/screens-workflow-prompt.md` cite plain rule numbers rather than `SPEC:Rnn`, so a rule change does not block on a brief. Their measured copies (`tools/workflow-brief/prompts*.json`, `screens_prompts.py`) keep the measured text. The briefs' checkers do not parse `§`.
- **Left as dated records.** `decisions/`, `docs/screens/**` (`jobs.md` included), `tools/task_sql.py:139`, which cites Equipoise's SPEC.md, and every other document's `§` in code: Equipoise SPEC, Tendril, `docs/spikes-2026-10-01.md`.

## Not checked

- The full test suite was not run; only comments changed, and the compile guard passed.
- The briefs were not re-measured with `tools/workflow-brief/`.
- 35 of the 107 drafted Acceptance lines name no test, so they were not checked against the tests; the 72 that name one were (see the second pass below).

Working files, gitignored: `build/runlogs/spec-migration/`, holding the section drafts, `assemble.py`, `keys.json` and the logs.

## Gap check, second pass (2026-11-21)

- **Python tools.** 11 old section citations in 6 live tools now cite plain rule numbers ("SPEC Rnn"): `tools/screens/form_opt.py`, `module_personality.py`, `nav_score2.py`, `picker_opt.py`, `t3_opt.py` and `tools/spikes/planner_check.py`. All 6 still byte-compile. Two of the strings in `module_personality.py` render into a T0 page, which shows the new numbers at its next rebuild. `tools/workflow-brief/screens_prompts.py` keeps its measured prompt text.
- **Reversed cases.** `chronicle-activity-delete-refused`, the category half of `chronicle-activity-and-category-totals`, and `chronicle-applies-to-scope` still state the old givens in `decisions/cases/`. R98 and R109 now say how the later rulings read them. The case files are left as dated records.
- **Names in the spec.** Every path, class and member the spec names exists in this repository or in the source apps. Eight hits of the automated check were false positives (source-app paths, file names), each confirmed by hand.
- **Acceptance lines against the tests.** Two Opus 5.5 reviewers read the test bodies behind the 72 drafted lines that name a test. 29 were true as written; 31 were partly true, 10 named a test that does not check them, and 2 named the wrong class. Five more lines, written by the builder but not marked as drafted, named the wrong or a partial class (R13, R24, R110, R116, R134). In all, 49 rules were updated: each cites the tests that really check it, and each untested clause is a `Not checked:` note in its Evidence.

### Clauses no test checks (33 rules)

These are missing tests, not spec errors. The spec keeps each clause as its criterion.

| Rule | Name | Untested |
|---|---|---|
| R18 | Synced tables | no test round-trips every synced table (`FolderSyncTest` covers `item`, `reminder` and purges), and no test reads the export triggers back. |
| R22 | Group values | no test feeds a NaN or infinite Double through the codec; decoding goes through `Group` (`Row.kt:17`). |
| R27 | A permanent purge registry | no test counts registry reads; the lookup by id is `StagedStore.kt:151`. |
| R34 | Recovery re-reads its own files | no test checks the rows after a recovery; `DatabaseRecoveryTest` checks only the recovery order. |
| R36 | Folder requirements | no test reads the outbox after a firing (no firing path writes: `firings()` only reads); `exportAfterQuiet` has no production caller (R38); the Auto Backup exclusion is not built. |
| R40 | Read positions | no test shrinks a file (`FolderSync.kt:103`). |
| R48 | Item field groups | no test changes the details and status groups on two devices and asserts no question. |
| R50 | The completion log | no test resolves one occurrence on two devices; reads take the later stamp in `ItemRepository.kt:216`. |
| R66 | Times are floating | no test parses one; `RRule.kt:57` takes the optional `Z`. |
| R77 | Edits reach reminders | no test retimes an occurrence without moving it, or gives an added occurrence a time. |
| R79 | Trackers move across as they are | only one value per reading is refused in a test; a rating outside 1 to 5, a unit on a non-number tracker and a CHOICE default are not (`SchemaTriggers.kt:134`). |
| R83 | Habit types and Logs | a yes/no habit Logged with an explicit value. |
| R85 | Habit columns | no test changes habit columns on two devices. |
| R88 | Logged occurrences are quiet | the test asserts the next firing, not the third dose. |
| R94 | Timed and whole-day occurrences | no test moves a timed occurrence to the day before (`OccurrenceEdits.kt:211`). |
| R95 | An occurrence's block and order | no test does it; `block` is outside an edit's schedule fields (`OccurrenceEdits.kt:34`). |
| R97 | Activities | no test reorders an ordered activity. |
| R99 | Span field groups | the keep and start-time groups' survival is not asserted. |
| R100 | A span's end is checked where it is written | no test counts such a span (`TimeTotals.kt:36`). |
| R103 | Goals on tracked time | only the week window goes through the repository, and no test reaches a goal. |
| R111 | How many labels each element carries | no test labels a standalone reminder. |
| R117 | What a label counts | no test leaves a template out (`LabelRepository.kt:150`). |
| R120 | Setting keys | no test reads the defaults of `app_lock_grace_seconds`, `llm_endpoint_key`, `onboarding_answer`, `mixed_mode` and `sleep_tracker`, and only `day_start` is synced in one. |
| R121 | Where each scope lives | no test reads the folder for a DEVICE_PREF value. |
| R141 | Page and block field groups | no test edits two groups of one block on two devices; `setType` and `setAttrs` have no test. |
| R143 | Later text wins, earlier is kept | a three-device clash on the real database, read from History. |
| R145 | Revive | revive by a place, a label or a sub-page made under the page; no test reads a revival's stamp. |
| R155 | Renames take the later name | no test renames on two devices (`renameOption` and `renameView` have no test call), and the visible columns' sync is untested. |
| R157 | Views | a Select sorted by its options' order (`DatabaseRepository.kt:972`), a text sort and a date filter. |
| R165 | Bound columns read the task | unbinding, or turning the switch off, with a row trashed elsewhere. |
| R169 | Inserting a picture | No test inserts a GIF, a BMP or an animation, refuses WebP, HEIC or CMYK, or checks quality 85. |
| R173 | Moving cards | a frame and a card in it moved apart on two devices. |
| R181 | Templates | templates kept out of database rows (`DatabaseRepository.kt:114`) and pickers (`CanvasRepository.kt:74`). |

### Behaviour absent from the code

The spec already records each of these as owed:
- the device-id file's Auto Backup exclusion (R32, R36);
- a new device id after a conflict copy in its own folder (R37);
- the SAF folder on Android (R45);
- a production caller for the export debounce, `exportAfterQuiet` (R38, R36).

### Clauses tested afterwards (2026-11-21)

Each row's test was written for the clause above, and each mutant, in `tools/mutants.py` (slices `gapA`, `gapB`, `gapC`), breaks the behaviour and is killed by that test. The rule's `Not checked:` note and Acceptance were rewritten to match, with one history row each.

| Rule | Test | Mutant killed |
|---|---|---|
| R18 | `FolderSyncTest.everySyncedTableIsQueuedForExportAndRoundTrips` | `a synced table with no export trigger` |
| R22 | `RecordCodecTest.aLineCarryingANaNOrAnInfiniteDoubleIsRefused` | `a group takes an infinite Double` |
| R27 | `FolderSyncTest.anImportTouchingOnePurgedIdReadsOneRegistryRow` | `the registry loaded whole` |
| R34 | `SettingsCasesTest.aRecoveredDeviceGetsItsRowsBackFromItsOwnFilesAndItsDeviceSettingsStartAtTheirDefaults` | `a recovery reads only peers` |
| R36 | `FolderSyncTest.aReminderFiringLeavesTheOutboxEmpty` | `a firing writes its reminder` |
| R40 | `FolderSyncTest.aFileThatShrankIsReadAgainFromTheStart` | `a shrunk file read from the old position` |
| R48 | `FolderSyncTest.theDetailsAndStatusGroupsChangedOnTwoDevicesMergeWithNoQuestion` | `details and status ask` |
| R50 | `FolderSyncTest.oneOccurrenceResolvedOnTwoDevicesReadsOneResultTheLater` | `the earlier completion read` |
| R66 | `RecurrenceCasesTest.anUntilEndingInZIsReadAsLocal_SPEC_R66` | `an UNTIL ending in Z is refused` |
| R77 | `OccurrenceEditSyncTest.aRetimedOccurrenceFiresAtItsNewTimeWithoutBeingMoved`, `anAddedOccurrenceGivenATimeOnAWholeDayItemFiresAtThatTime` | `a retimed occurrence fires at the series' time`, `an added occurrence's own time is ignored` |
| R79 | `HabitCasesTest.trackerAndReadingRulesHold` | `a rating outside 1 to 5 is taken`, `a unit is taken on any tracker`, `a CHOICE tracker takes a default` |
| R83 | `HabitCasesTest.aYesNoHabitLoggedWithAnExplicitValueKeepsIt` | `an explicit no is Logged as a yes` |
| R85 | `HabitCasesTest.habitColumnsChangedOnTwoDevicesAskOnlyForTheSchedule` | `a habit's details ask` |
| R88 | `HabitCasesTest.aLogNamingNoOccurrenceQuietsOnlyOneOfTheDays` | `one Log quiets its whole day` |
| R94 | `PlannerCasesTest.aTimedOccurrenceBeforeTheDayStartBelongsToTheDayBefore` | `a timed occurrence's day is its date` |
| R95 | `OccurrenceEditSyncTest.anOccurrencesBlockMovedOnTwoDevicesMergesWithoutAQuestion` | `a block is a schedule field` |
| R97 | `TimeCasesTest.reorderingAnActivityMovesItBetweenItsNewNeighbours` | `a fractional order is truncated` |
| R99 | `TimeCasesTest.eachOfASpansFiveGroupsWrittenOnADifferentDeviceSurvives` | `a span edit writes every part` |
| R100 | `TimeCasesTest.aMergedSpanEndingBeforeItStartsCountsAsNothing` | `a span ending before it starts counts` |
| R103 | `TimeCasesTest.aGoalIsReachedInEachWindowThroughTheRepository` | `every goal counts its week`, `a milestone counts only its period` |
| R111 | `LabelCasesTest.aStandaloneReminderCarriesOneLabelAndASecondReplacesTheFirst_SPEC_R111` | `a standalone reminder takes no label` |
| R117 | `VocabularyTest.aTemplateCarryingALabelIsNotCounted_SPEC_R117` | `a template carrying a label is counted` |
| R120 | `SettingsCasesTest.eachSettingKeyHasItsScopeAndDefaultAndThePersonalOnesSync` | `Mixed mode kept per device`, `the app lock grace defaults to 5 s` |
| R121 | `SettingsCasesTest.aDevicePreferenceNeverReachesTheFolder` | `a device preference written to the synced table` |
| R141 | `PageCasesTest.twoGroupsOfOneBlockEditedOnTwoDevicesBothStand_SPEC_R141` | `a block's attributes take its type's stamp` |
| R143 | `PageCasesTest.withThreeDevicesEveryReplacedTextIsKeptInAHistoryAndNoticedEverywhere_SPEC_R143` | `a winning local text looks agreed, on the database` |
| R145 | `PageCasesTest.aMoveALabelOrASubPageMadeUnderItAfterTheTrashBringsAPageBackStampedJustAboveTheTrash_SPEC_R145` | `a move leaves a trashed page in the Trash`, `a label leaves a trashed page in the Trash`, `a sub-page made under a trashed page leaves it in the Trash`, `a revival takes a fresh stamp, read back` |
| R155 | `DatabaseCasesTest.aPropertyOptionAndViewRenamedOnTwoDevicesTakeTheLaterNameSilentlyAndShownColumnsSync_SPEC_R155` | `a rename clash is asked`, `a view's shown columns do not sync` |
| R157 | `DatabaseCasesTest.aSelectSortsByItsOptionsOrderTextIgnoresCaseAndADateFilterReadsDates_SPEC_R157` | `a Select sorts by its options' names`, `a text sort leaves the rows as they are`, `a date cell is empty by its text` |
| R165 | `RowTasksTest.unbindingOrTurningTasksOffOnADeviceThatHadNotSeenATrashDoesNotBringTheRowBack_SPEC_R165` | `unbinding writes the cells as a person's`, `turning tasks off writes the cells as a person's` |
| R169 | `ImagesTest.aGifABmpAndAnAnimationAreReadWebpHeicAndCmykRefusedAndAJpegIsWrittenAtQuality85_SPEC_R169` | `a JPEG at quality 75`, `an animation keeps its last frame`, `only JPEG and PNG are read`, `a picture the JDK cannot read is not refused as one`, `a CMYK JPEG is read`, `the frame header is looked for in the first segment only`, `every JPEG but an RGB one is refused` |
| R173 | `CanvasCasesTest.aFrameAndACardInItMovedApartEachKeepTheirOwnLaterPosition_SPEC_R173` | `a frame drags what lies in it` |
| R181 | `JournalLinksTemplatesTest.aTemplateIsNoDatabaseRowAndNoBoardOffersIt_SPEC_R181` | `a template made under a database is a row`, `a template carrying the doorway is a row`, `a board offers a template` |

Found while testing:
- No repository writes a `tracker_choice` row, so a CHOICE tracker has no way to get its choices (R18's test writes one through `LocalWrites`).
- The desktop refused no CMYK JPEG, though R169's Values and `DesktopImageScaler`'s doc comment said it did: JDK 21's ImageIO reads a four-channel JPEG, with or without an Adobe marker, and the scaler stored it. In a JDK probe the image drawn onto an RGB canvas came out black. Built 2026-11-22 at the owner's word: the scaler refuses a JPEG whose frame header names four channels (CMYK, or YCCK with an Adobe marker), and the R169 test refuses all three.

## Drafted Acceptance lines (107)

Written by the builder from each rule's wording where neither the old spec nor a test named the check. The 72 that name a test were then checked against the test bodies (above).

| Rule | Name | Drafted Acceptance |
|---|---|---|
| R02 | One home per concept | The data model (R18) holds one table family per concept, and no second table stores items, rules, labels, search text or sync state. |
| R03 | Source defects fixed | The ADR cases that encode a fix pass as tests (R194). |
| R04 | Jobs and how often | The navigation and screens decisions in `decisions/15-screens.md` and later tiers cite this table for every cadence they rely on, and no screen puts a weekly job above a daily one. |
| R06 | Every sole-owner module moves across | Each module in the table has its rules built and their tests passing; the features in the second sentence each have a screen or entry point once their tier is settled. |
| R08 | App id and packages | `applicationId` is `com.hazia.factotum` with no suffix, and every Kotlin package starts with `com.hazia.factotum`. |
| R09 | Personal use, one signing key | The installed APK's signing certificate has SHA-256 starting `20:FB:3E:76`, and every build type uses `signingConfigs.debug`. |
| R11 | Modules split by layer | `:core` has no Room dependency, `:data` depends only on `:core`, and the build passes (`./gradlew --offline`). |
| R12 | One write path | Every DAO in `:data` is `internal`, and the two-device tests through the composition root (R33) pass. |
| R17 | Licensing | The `:llm` build links only `llama` and `ggml` on both platforms, and the About screen shows llama.cpp's MIT notice. |
| R18 | Synced tables | `FactotumDatabase.kt:220` checks at open that every synced table has its `RowTable`, `SchemaTriggers` makes an export trigger for each, and every synced table round-trips through export and import. |
| R19 | Local stores, never synced | No export trigger names a store in this table, and a peer that imports a device's folder never receives one of them. |
| R20 | Folder sync for one person | `FolderSyncTest` syncs two devices through a shared folder and nothing else. |
| R22 | Group values | `RecordCodecTest.aLineThatIsNotARecordIsRefused` refuses a value of another type and `ClockAndIdTest.aGroupRefusesADoubleThatNeverEqualsItself` a NaN; a NaN or infinite Double in an imported line is refused. |
| R26 | Old versions do not move the base | Replaying an older version of the other side through the folder leaves the base and any pending question as they were, and the next change on the other side is still asked. |
| R27 | A permanent purge registry | The purge case of `decisions/cases/01-sync.jsonl` passes (`SyncCasesTest.tendrilPurgeHolds`), and an import touching one purged id reads one registry row. |
| R28 | A purge undone by a later edit | After a purge is undone by a peer's later edit, both devices hold the same rows under the revived one. |
| R32 | The device id | `SyncStorageTest.anUnreadableDeviceIdIsSetAsideAndReplaced` sets an unreadable id file aside and makes a new id; the Android manifest's backup rules exclude the file. |
| R34 | Recovery re-reads its own files | `SettingsCasesTest.aDeviceWhoseDatabaseWasRecoveredGetsItsSettingsBackFromItsOwnFiles` recovers a device alone and finds its PERSONAL settings again, and its rows come back too. |
| R36 | Folder requirements | `ExportTimingTest.aBurstOfWritesExportsOnceThirtySecondsAfterTheLast` (debounce), `DirectorySyncFolderTest.aReplaceLandsWholeAndLeavesNoTemporaryFile` (atomic replace) and `RecordCodecTest.aRecordIsOneCompactLine` (compact JSON) pass; a reminder firing leaves the outbox empty; the Auto Backup exclusion is checked with the Android shell. |
| R37 | Conflict copies | `FolderSyncTest.aClonedDeviceIdsClashIsMergedAndTheCopyRemoved` merges and deletes a conflict copy; after one in its own folder the device re-reads its own files and holds a new id. |
| R38 | A local outbox decides what to export | A write through any repository, and an import that changes a row, each leave the row queued for export. |
| R39 | Imports in chunks | `FolderSyncTest` imports a snapshot larger than one chunk and stops and resumes it at a chunk boundary. |
| R40 | Read positions | `FolderSyncTest.aPeerFileIsReadOnlyWhenItHasGrown` and `aLineStillBeingWrittenWaitsForItsNewline` pass, and a file that shrank is read again from the start. |
| R41 | Lines this version cannot read | `FolderSyncTest` skips an unreadable line, applies it after the table set changes, and drops a line that breaks its table's rules. |
| R42 | A row whose parent has not arrived waits | A completion imported before its item waits, then applies once the item arrives; one whose item was purged is dropped. |
| R43 | A deleted row takes its merge state | Purging a row with a pending question leaves no base or question behind. |
| R44 | Tables reach the importer through RowTable | Every synced table of R18 has its `RowTable`, and a snapshot of a large table is written with bounded memory. |
| R45 | Folder implementations | `DirectorySyncFolderTest` passes; the SAF folder passes the same tests on a device. |
| R47 | Names in code | No class, table or column in `core/` or `data/` is named Entry. |
| R48 | Item field groups | `FolderSyncTest.anAnswerSettlesTheQuestionOnBothDevices` asks for a schedule clash, and the details and status groups changed on two devices merge with no question. |
| R49 | Kind rules are triggers | `ItemCasesTest.sharedEventHasNoTaskState_theDatabaseRefusesIt` and `theKindRulesHoldAfterAReopen` (updates), `PlannerCasesTest.plannedAndBlockRulesHold` (inserts), `HabitCasesTest.aTaskWithoutAStatusIsRefused`, `ReminderCasesTest.aStandaloneReminderNeedsATime` and `TimeCasesTest.activitiesKeepTheirOrderAndTheirColumnsStayTheirs` pass. |
| R50 | The completion log | One occurrence resolved on two devices reads one result, the later. |
| R52 | The capacity query | The query plan of the capacity query names `item_kind_date` and no table scan. |
| R54 | Reminder field groups | `FolderSyncTest.aSnoozeOnOneDeviceAndAnAlertChangeOnAnotherBothStayWithoutAQuestion` passes. |
| R60 | Alarms and missed occurrences | On each platform an alarm set before the app is closed rings (Android) or is shown at the next start (Windows), and a missed NOTIFICATION fires once. |
| R61 | A force-stopped app says so | On a device, force-stopping the app and opening it again shows the notice, and the alarms are set again. |
| R65 | DTSTART and set times | `RecurrenceCasesTest.theNineFixedRulesGiveTheOwnerAppsOccurrences` and `aStartTheRuleDoesNotMatchIsNotAnOccurrence` cover an unaligned start, a cron rule from midnight and a month end, and `CronTest.severalLinesAreOneRuleTheirUnion` a rule set. |
| R66 | Times are floating | An `UNTIL` ending in `Z` is read as local. |
| R67 | The expander | `RecurrenceCasesTest` and the expander's ported tests refuse each row's rule and pass the fixed rules. |
| R69 | One recurrence engine | Tasks, events, reminders and habits all expand through `com.hazia.factotum.core.recurrence`, with no second expander in `core/` or `data/`. |
| R75 | Series edits | `OccurrenceEditsTest` renames a series with a moved occurrence. |
| R76 | Habit fields in an edit | An edit carrying `sort_order`, `rule_patch` and `pause` round-trips through the folder unchanged. |
| R77 | Edits reach reminders | `OccurrenceEditSyncTest.aSkippedOccurrenceDoesNotFireAndAMovedOneFiresAtItsNewTime` and `anAddedOccurrenceOnAWholeDayItemFiresAtTheAnchor` pass, and a retimed occurrence and an added one given a time fire at their times. |
| R79 | Trackers move across as they are | `HabitCasesTest.trackerAndReadingRulesHold` refuses a reading breaking each rule. |
| R81 | No streaks in Habits | No table or column stores a streak or missed-day count, and presence (R82) returns none. |
| R83 | Habit types and Logs | `HabitCasesTest` Logs a number habit with and without a value, a rating habit (refused without one) and a yes/no habit without one. |
| R85 | Habit columns | `HabitCasesTest` changes a details column and a schedule column on two devices and gets a question only for the schedule. |
| R86 | Pause | `PlannerCasesTest.twoHabitsOnOneTrackerPauseOnTheirOwn` passes. |
| R88 | Logged occurrences are quiet | `HabitCasesTest.aLogNamingNoOccurrenceQuietsOnlyOneOfTheDays` Logs one dose of three, and the other two stay due. |
| R89 | Time blocks | `PlannerCasesTest` makes a database on two devices and finds the same five blocks. |
| R93 | Placing an occurrence | `PlannerCasesTest` (a set time in a block, an edit's block, a slot's block) and `PlannerTest` (a set time outside every block, the habit's block, `overlappingBlocksAreReportedOncePerOverlappingPair`) pass. |
| R94 | Timed and whole-day occurrences | `PlannerCasesTest.aWholeDayOccurrenceIsPausedOnItsOwnDateWhenTheDayStartsLater` passes, and a timed occurrence before the day boundary belongs to the day before. |
| R95 | An occurrence's block and order | An occurrence's block moved on one device while the other retimes the series gives no question. |
| R96 | Reminders on an "n a day" habit | `PlannerCasesTest` fires each occurrence at its block's start and an unblocked one at the anchor. |
| R97 | Activities | `TimeCasesTest.activitiesKeepTheirOrderAndTheirColumnsStayTheirs` makes and orders activities, and reordering one moves it. |
| R99 | Span field groups | `TimeCasesTest.aCommentWrittenOnOneDeviceDoesNotReopenATimerStoppedOnAnother` and the stale keep or start test pass, and each of the five groups written on a different device survives. |
| R100 | A span's end is checked where it is written | `TimeCasesTest` refuses an end before the start locally, and a merged span ending before its start counts as nothing. |
| R102 | Time is an activity's: spans and amounts | An amount added on a picked day syncs to a peer and counts in that day's total, and no tracker accepts a time unit. |
| R103 | Goals on tracked time | `TimeTotalsTest` checks each window's bounds, and a goal is reached in each window through `ActivityRepository`. |
| R111 | How many labels each element carries | `LabelCasesTest` (one label on a habit, activity, task, event, tracker and checklist, a second replacing the first), `PageCasesTest` (many on a page) and `DatabaseCasesTest` (the doorway) pass. |
| R112 | Label names are unique | `LabelCasesTest` refuses a second label differing only in case or form. |
| R114 | Label field groups | `LabelCasesTest` renames and recolours on two devices and both stand. |
| R115 | No foreign key on a label | `PageCasesTest` deletes a label carried by a trashed page, and the page stays trashed. |
| R117 | What a label counts | `VocabularyTest.aLabelCountsTheLiveElementsCarryingItEachOnce` counts each kind once, `LabelCasesTest` reads a merged label's elements, and templates are left out. |
| R119 | A typed registry | `SettingsCasesTest` reads an unreadable value as the default and clears a value set to its default. |
| R120 | Setting keys | `SettingsCasesTest` reads each key's default and syncs the PERSONAL ones. |
| R121 | Where each scope lives | `SettingsCasesTest` sets one key on two devices and reads one row, and a DEVICE_PREF value never reaches the folder. |
| R122 | Repositories read settings on every call | `SettingsCasesTest.theDayStartSetOnOneDeviceDecidesTheDayOnAnotherAtOnce` passes, and every repository that reads the day boundary takes it through a required parameter. |
| R126 | Kept current by triggers | `SearchCasesTest` finds a row written by an import, and an index emptied by hand is rebuilt at the next open. |
| R130 | No numbers on the check-in screen | The check-in screen's mockup and build show no number, average, count or curve. |
| R131 | A check-in about a past day | `CheckInCasesTest` makes a check-in about yesterday and finds it on yesterday, and refuses one about tomorrow. |
| R132 | Check-in field groups | `CheckInCasesTest` edits a note on one device while the other undoes the check-in, and it stays undone. |
| R138 | Sensory logs | `RegulationLedgerTest` writes and undoes a sensory log. |
| R141 | Page and block field groups | `PageCasesTest` edits two groups of one block on two devices and both stand. |
| R142 | Block order | `PageCasesTest.blocksNestAndKeepTheirOrderAfterTheKeysRunOutOfRoom`, `placingBlocksNeverWritesOverAMoveOrADeletionMadeElsewhere` and `OutlineTest` pass. |
| R143 | Later text wins, earlier is kept | `PageCasesTest.theLaterTextWinsAndTheEarlierIsKeptInHistoryWithOneNoticeDismissedEverywhere` (two devices) and `KeepLoserMergeTest.withThreeDevicesEveryReplacedTextIsLostSomewhereWhateverTheOrder` (three, in memory) pass. |
| R144 | The replaced-by-a-sync notice | `PageCasesTest` makes a clash on two devices, dismisses the notice on one, and it stays dismissed on both. |
| R145 | Revive | `PageCasesTest.aLaterEditBringsATrashedPageBackAndAnEarlierOneDoesNot`, `aLaterEditToASubPageBringsBackItsTrashedParents` and `aLaterEditBringsADeletedBlockBack` pass. |
| R146 | The app's own writes are marked | `CanvasCasesTest` deletes a card and its parent on two devices and neither comes back. |
| R148 | What a merge can leave | `PageCasesTest` makes a cycle on two devices and reads both pages at the top. |
| R149 | Page History | `PageCasesTest` writes, merges and restores versions and keeps fifty. |
| R151 | Cell values and type changes | `DatabaseCasesTest` changes a column's type both ways and reads the same stored values. |
| R154 | Select options | `DatabaseCasesTest` deletes, picks again, merges and restores options. |
| R155 | Renames take the later name | A rename on two devices reads the later name with no notice, and `DatabaseCasesTest.aSortAndAFilterChangedApartBothStand` passes. |
| R156 | A database's rows | `DatabaseCasesTest` and `PageCasesTest` read the members, trash and revive a database. |
| R157 | Views | `DatabaseCasesTest.aViewSortsByTypeWithEmptyLastAndFiltersByType` and `aDatabaseKeepsOneViewAndATrashedOnesSchemaIsNotEdited` pass. |
| R161 | Where formulas differ from Tendril | `FormulaColumnsTest` covers each row. |
| R165 | Bound columns read the task | `RowTasksTest.bindingOnADeviceThatHadNotSeenATrashDoesNotBringTheRowBack` passes, and unbinding does the same. |
| R167 | Rows changed | A write that adds a page to a database through the screens is followed by `rowsChanged()`, and the new row has its task. |
| R169 | Inserting a picture | `ImagesTest` inserts each format on the desktop; the device check passes on Android. |
| R170 | Pictures through the folder | `ImagesTest` syncs a picture to a peer, damages a copy, and reads a waiting placeholder. |
| R171 | Collecting pictures | `ImagesTest` collects the folder copy after 30 days unnamed and keeps the device copy History names. |
| R173 | Moving cards | `CanvasCasesTest` moves a card and its frame on two devices. |
| R175 | Page cards | `CanvasCasesTest` reads a page card in each of the four states. |
| R176 | Canvas History | `CanvasCasesTest` replaces a card's text on two devices and restores it from History. |
| R180 | Blocked-by | `JournalLinksTemplatesTest` blocks a row and unblocks it by trashing the blocker. |
| R181 | Templates | `JournalLinksTemplatesTest` makes a template and finds it only in `templates()` and the Trash. |
| R185 | Checklist order and text | `ChecklistChartTest` adds lists, charts and items and refuses a blank name. |
| R187 | Screens are settled tier by tier | Every screen built in `:ui` has its approval recorded in `decisions/` and a mockup under `docs/screens/`, and a screenshot of the running app matches it. |
| R188 | Dark mode | The settings offer the four choices on the phone and three on Windows. |
| R189 | Settings in two sections | Every PERSONAL setting appears under "On every device" and every DEVICE_PREF setting under "On this device". |
| R190 | Fixed words | The screens' wording uses each word only in its meaning. |
| R193 | Build order | No `:ui` screen code exists before step 4 begins, and every slice of step 2 has its cases passing (R194). |
| R198 | Importing data from the source apps | No code in `core/`, `data/`, `android/` or `windows/` reads a source app's database or sync files. |
| R199 | A sync server, accounts or cloud storage | No code opens a network connection for sync. |
| R200 | Source mechanisms not carried over | No table or column of those names exists in `data/schemas/`. |
| R202 | Tendril's Claude text verbs | ? |

## Identifier map

Old section numbers of `Factotum SPEC.md` v0.40 mapped to new rules. R04 has no old source: it comes from `docs/screens/t0/jobs.md`.

| Old | New |
|---|---|
| 0.1.1 | R198 |
| 0.1.2 | R20, R199 |
| 0.1.3 | R81 |
| 0.1.4 | R05 |
| 0.1.5 | R06, R202 |
| 0.1.6 | R07, R08 |
| 0.1.7 | R09 |
| 0.2 | R10 |
| 1 | R01, R02, R03 |
| 2 | R06, R200 |
| 3 (acceptance for every subsection) | R194 |
| 3.1 | R21, R22, R23, R24, R25, R26, R27, R32, R29, R30, R31 |
| 3.2 | R46, R47, R48, R49, R50, R51, R52, R12 |
| 3.3 | R53, R54, R55, R56, R57, R58, R59 |
| 3.4 | R62, R63, R64, R65, R66, R67, R68, R70, R60, R61 |
| 3.5 | R129, R130, R131, R132, R133, R134 |
| 3.6 | R80, R82, R83, R79, R84, R85, R86, R87, R88, R89, R90, R91, R92, R93, R94, R95, R96, R190 |
| 3.7 | R97, R98, R99, R100, R101, R102, R103, R104, R105, R106, R107, R108 |
| 3.8 | R109, R110, R111, R112, R113, R114, R115, R116, R117, R15, R190 |
| 3.9 | R118, R119, R120, R121, R122, R123, R34 |
| 3.10 | R124, R125, R126, R127, R128 |
| 3.11 | R71, R72, R73, R74, R75, R76, R77, R50 |
| 3.12 | R140, R141, R142, R143, R144, R145, R146, R147, R148, R149, R150, R151, R152, R153, R154, R155, R156, R157, R158, R172, R173, R174, R175, R176, R177, R178, R179, R180, R181, R182 |
| 3.13 | R35, R36, R37, R38, R39, R40, R41, R42, R43, R44, R45 |
| 4 | R198, R199, R81, R200, R201 |
| 5.1 | R05, R11 |
| 5.2 | R18, R19 |
| 5.3 | R12, R69 |
| 6 | R17 |
| 7 step 1 | R193, R13 |
| 7 step 2 | R194 |
| 7 step 3 | R195, R159, R160, R161, R168, R169, R170, R171, R14, R162, R163, R164, R165, R166, R167, R135, R136, R137, R138, R139, R120, R183, R184, R185, R186 |
| 7 step 4 | R193, R33 |
| 7 imports | R16 |
| 8 | R60, R13, R196 (the LLM risk is a background paragraph in section 18) |
| 9.1 | R197, R124 |
| 9.2 | R65, R92, R85 |
| 9.3 | R196 |
| 9.4 | R64 |
| 9.5 | R61 |
| 9.6 | R17 |
| 10.1 | R187, R188, R189, R190, R191, R192 |
| 10.2 | R11 |
| 10.3 | R193 |
| 10.4 | R60 |
| 10.5 | R139 |
| 10.6 | R78 |
| 10.7 | R125 |
| 10.8 | closed: the map's copies; left to git |
| 10.9 | R35 |
| 10.10 | R84 |
| 10.11 | R96 |
| 10.12 | R28 |
| 10.13 | R158 |
| 11 | next steps, all done; left to git |
