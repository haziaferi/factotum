# ADR 09: Settings store, where each setting may travel

Status: **decided: scoped-live**. The owner chose this against the recommendation, which was local+backup. Date: 2026-09-30. Owners: Tendril, Chronicle, Mnemo and Equipoise.

The map listed this row as *duplicated*, "one model expresses the other without loss". Verification found the disagreement is not about storage format at all. It is about **what may leave a device**:
- No app syncs settings.
- Mnemo and Equipoise carry settings in a backup or export, and Tendril and Chronicle carry none.
- Each app keeps per-device state beside its preferences.

This ADR builds on ADR 01 (sync, per-group stamps, device identity).

## Verified facts

The facts were verified with `tools/verify.py`; the raw output is in `verify/09-settings/`.

| App | Fact | Source | Map said |
|---|---|---|---|
| Tendril | A string-only `KeyValueStore`: SharedPreferences `tendril_kv` on Android, a Properties file on desktop. It has 26 key constants in shared code, and the desktop sync folder is kept separately in `java.util.prefs`. Several Android preference classes sit outside it (app lock, calendar, sync folder). | `KeyValueStore.kt:19`; `AndroidKeyValueStore.kt:17`; `DesktopSyncFolderManager.kt:21`; `AppLockPreferences.kt:10` | "KeyValueStore" (partial) |
| Tendril | The AI key is a secret kept apart from settings: Keystore on Android, a DPAPI-wrapped file on desktop. | `AiKeyStore.kt:7`; `FileAiKeyStore.kt:36` | not stated |
| Tendril | No setting syncs, and none is in the backup (0 hits in sync code and in `PortableArchive`). The store also holds per-device layout: window frame, pane widths, pop-outs. | `data_extraction_rules.xml:4,7`; `PopOuts.kt:58` | not stated |
| Chronicle | **The map didn't open this.** Settings are one Preferences DataStore, `chronicle_settings`, with 33 keys across files. It also holds non-settings state: alarm codes, pending alerts, the folder-sync seen marks and **`device_id`**. | `CoreDataModule.kt:43-44`; `SettingsRepository.kt:117-128` (the settings keys); `AlarmCodes.kt:70`; `PendingAlerts.kt:100`; `DeviceIdRepository.kt:24` | "DataStore" (unverified before) |
| Chronicle | No setting syncs or travels in the backup. A corrupt file resets to empty, which **regenerates `device_id`**, and the old identity's file stays in the folder as a stale peer. The PIN is a salted PBKDF2 hash in the same store. | `FolderSync.kt:24-28`; `SyncPayload.kt:17`; `CoreDataModule.kt:41`; `SettingsRepository.kt:127-128,207` | not stated |
| Mnemo | Preferences DataStore `app_settings` (5 keys), plus a **second store**: SharedPreferences `sync_export`, holding the folder's SAF tree URI. | `AppSettingsStore.kt:18`; `SyncRootStore.kt:28,63-64` | "DataStore" (partial) |
| Mnemo | Settings are "deliberately not part of the sync path", because a phone and a tablet may want different defaults. The manual full backup carries them, and restoring **overwrites everything**, including a per-device first-run flag. The folder URI isn't in the backup. | `AppSettingsStore.kt:22,107-108`; `FullBackupManager.kt:32,58,184`; `SyncRootStore.kt:49` | not stated |
| Equipoise | Two single-row Room tables (id = 1): `settings` and `llm_settings`. There is no DataStore or SharedPreferences (0 hits). | `Entities.kt:94-114`; `Daos.kt:76,84` | confirmed |
| Equipoise | `settings` (burnout threshold, crisis contacts, check-in shape and so on) **travels in export/import**, where an import overwrites it. `llm_settings` (model URI, endpoint, encrypted key) never leaves the device. | `Transfer.kt:34,70,78`; `Snapshot.kt:9-10` | not stated |

## Scores (`09-settings-scores.md`, run by `tools/settings_sim.py`)

The simulator models phone A and tablet B sharing a folder, and phone C restored from A's backup. Each option is a per-key policy.

| Option | Chronicle | Equipoise | Mnemo | Shared | Tendril | Growth | Status |
|---|---|---|---|---|---|---|---|
| as-is | 1.00 | 1.00 | 1.00 | 0.00 | 1.00 | 7 | dominated (carries Mnemo's first-run flag to a new phone) |
| all-local | 1.00 | 0.50 | 0.67 | 1.00 | 1.00 | 2 | front (nothing restores) |
| local+backup | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 3 | **front, the recommendation** |
| scoped-live | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 4 | dominated by the metric; **the owner's pick** |
| synced-table (control) | 0.00 | 0.50 | 0.00 | 0.00 | 0.00 | 1 | failed 8 of 9, all expected (tablet B takes phone A's sync identity) |

Growth here is a hand count of storage places, taken from the verification. It isn't measured from a schema, and it only breaks ties.

scoped-live is "dominated" only because no owner app syncs settings live today, so no case can ask for it. That makes it a feature choice, which the owner made.

**Sensitivity (2026-10-01, `tools/sensitivity.py`):** local+backup and scoped-live both cover every case, and only the hand-counted growth separates them (3 against 4 storage places). Varied over ×0.5 to ×2, scoped-live is on the front in 36% of 1,296 combinations. The owner's pick rests on wanting live sync, not on growth, so this changes nothing.

## Decision

**scoped-live** was chosen by the owner on 2026-09-30, against the recommendation. Every setting key is declared once, in a registry in code, with one of four scopes:

| Scope | Examples | Stored in | Syncs live | In backup/export |
|---|---|---|---|---|
| PERSONAL | burnout threshold, crisis contacts | synced `setting` table (key, value, ADR 01 identity and stamps) | **yes** | yes |
| DEVICE_PREF | Mnemo's default mode, theme | device-local store | no | yes |
| DEVICE_STATE | window frame, pane widths, folder URI, first-run flags, LLM model URI and endpoint | device-local store | no | no |
| SECRET | AI API key, LLM endpoint key, PIN hash | Keystore / DPAPI | no | no |

**Device identity is not a setting.** ADR 01's device id lives in its own store, not in the settings file, so a corrupt settings file can't give a device a new sync identity (Chronicle's `CoreDataModule.kt:41`).

## Consequences: fixes, not questions

- **A PERSONAL conflict** follows ADR 01's rule for that group (hybrid+: a later stamp wins silently). Settings are not schedule changes, so no one is asked.
- **Restore writes only PERSONAL and DEVICE_PREF keys.** Mnemo's restore of its first-run flag is not carried over.
- **A corrupt local store** resets DEVICE_PREF and DEVICE_STATE to their defaults. PERSONAL keys come back from the synced table, and secrets and the device id are untouched.
- **Parked columns aren't carried over.** Equipoise's `greyDay` (`Entities.kt:99`) is never read and stays behind, which a fresh start allows.
- **Owner-facing wording.** The settings screen marks which settings follow you across devices. That wording will be decided with the owner when screens are designed.
