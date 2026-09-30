"""Contest 09 (settings store): simulate where each setting may travel. Devices A (phone) and B
(tablet) share a sync folder; C is a new phone restored from A's backup. Each option is a policy
that says, per key, whether the key syncs live, rides in the backup/export, or never leaves.

    python tools/settings_sim.py     # writes decisions/options/09-settings.sim.json + a table

Keys, with the owner app whose code sets the expectation (verify/09-settings/):
  ai_api_key        tendril    secret: Keystore / DPAPI, never in the KV store (AiKeyStore.kt:7)
  window_frame      tendril    per-device layout (PopOuts.kt:58)
  device_id         chronicle  sync identity, local, never restored (DeviceIdRepository.kt:16)
  sync_folder_uri   mnemo      SAF grant, device-local, not in the backup (SyncRootStore.kt:49)
  first_run_flag    mnemo      per-device flag; Mnemo's restore overwrites it (AppSettingsStore.kt:108)
  default_mode      mnemo      differs per device on purpose (AppSettingsStore.kt:22), restored from backup
  theme             mnemo      restored from backup (FullBackupManager.kt:58)
  burnout_threshold equipoise  travels in export/import (Transfer.kt:34,70)
  crisis_contacts   equipoise  travels in export/import (Entities.kt:100)
  llm_model_uri     equipoise  never leaves the device (Snapshot.kt:9-10)

Options (scope classes: PERSONAL, DEVICE_PREF, DEVICE_STATE, SECRET)
  as-is         each app's store unchanged (7 storage places)
  all-local     one local store + a secret store; nothing leaves a device
  local+backup  one local store with a declared scope per key + a secret store; PERSONAL and
                DEVICE_PREF ride in the backup/export; DEVICE_STATE and SECRET never leave
  scoped-live   local+backup, and PERSONAL keys also sync live through a synced settings table
  synced-table  CONTROL: every key in one synced table that also rides in the backup
Growth = storage places a setting can live in (stores, secret stores, backup sections, synced tables).
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SCOPE = {"ai_api_key": "SECRET", "window_frame": "DEVICE_STATE", "device_id": "DEVICE_STATE",
         "sync_folder_uri": "DEVICE_STATE", "first_run_flag": "DEVICE_STATE", "llm_model_uri": "DEVICE_STATE",
         "default_mode": "DEVICE_PREF", "theme": "DEVICE_PREF",
         "burnout_threshold": "PERSONAL", "crisis_contacts": "PERSONAL"}
# as-is: what each source app does today, from the verification
AS_IS = {"ai_api_key": (False, False), "window_frame": (False, False), "device_id": (False, False),
         "sync_folder_uri": (False, False), "first_run_flag": (False, True), "llm_model_uri": (False, False),
         "default_mode": (False, True), "theme": (False, True),
         "burnout_threshold": (False, True), "crisis_contacts": (False, True)}


def policy(opt, key):
    """(syncs live, rides in backup) for one key."""
    s = SCOPE[key]
    if opt == "as-is":
        return AS_IS[key]
    if opt == "all-local":
        return (False, False)
    if opt == "local+backup":
        return (False, s in ("PERSONAL", "DEVICE_PREF"))
    if opt == "scoped-live":
        return (s == "PERSONAL", s in ("PERSONAL", "DEVICE_PREF"))
    if opt == "synced-table":
        return (True, True)
    raise KeyError(opt)


GROWTH = {"as-is": 7, "all-local": 2, "local+backup": 3, "scoped-live": 4, "synced-table": 1}
OPTIONS = list(GROWTH)


class World:
    def __init__(self, opt):
        self.opt = opt
        self.dev = {d: {"device_id": "dev-" + d} for d in "AB"}
        self.folder = {}

    def set(self, d, key, value):
        self.dev[d][key] = value

    def sync(self):
        for d in "AB":
            for k, v in self.dev[d].items():
                if policy(self.opt, k)[0]:
                    self.folder[k] = v
        for d in "AB":
            for k, v in self.folder.items():
                self.dev[d][k] = v

    def backup(self, d):
        return {k: v for k, v in self.dev[d].items() if policy(self.opt, k)[1]}

    def restore(self, blob):
        c = {"device_id": "dev-C"}
        c.update(blob)
        self.dev["C"] = c
        return c

    def everywhere_but(self, d, key, value):
        """Where the value shows up outside device d: folder, backup, other devices."""
        seen = []
        if self.folder.get(key) == value:
            seen.append("folder")
        if self.backup(d).get(key) == value:
            seen.append("backup")
        seen += [o for o in self.dev if o != d and self.dev[o].get(key) == value]
        return seen


def world(opt):
    w = World(opt)
    w.set("A", "ai_api_key", "sk-A")
    w.set("A", "window_frame", "1200x800@0,0")
    w.set("A", "sync_folder_uri", "content://tree/A")
    w.set("A", "first_run_flag", "asked")
    w.set("A", "llm_model_uri", "file:///A/gemma.gguf")
    w.set("A", "default_mode", "EASE")
    w.set("B", "default_mode", "FOCUS")
    w.set("A", "theme", "Bark")
    w.set("A", "burnout_threshold", "0.4")
    w.set("A", "crisis_contacts", "sam: 555")
    w.sync()
    return w


def stays_on_a(key, value):
    def case(opt):
        w = world(opt)
        return 1 if w.everywhere_but("A", key, value) == [] else 0
    return case


def case_device_id(opt):
    """chronicle: every device keeps its own sync identity; B never takes A's, and a phone restored
    from A's backup is a new device."""
    w = world(opt)
    c = w.restore(w.backup("A"))
    return 1 if w.dev["B"]["device_id"] == "dev-B" and c["device_id"] == "dev-C" else 0


def case_mode_per_device(opt):
    """mnemo: the phone keeps EASE and the tablet keeps FOCUS after a sync (AppSettingsStore.kt:22)."""
    w = world(opt)
    return 1 if (w.dev["A"]["default_mode"], w.dev["B"]["default_mode"]) == ("EASE", "FOCUS") else 0


def case_backup_restores_prefs(opt):
    """mnemo: a new phone restored from A's backup gets A's default mode and theme (FullBackupManager.kt:184)."""
    w = world(opt)
    c = w.restore(w.backup("A"))
    return 1 if (c.get("default_mode"), c.get("theme")) == ("EASE", "Bark") else 0


def case_folder_not_restored(opt):
    """mnemo: the restored phone does not inherit A's folder grant (SyncRootStore.kt:49)."""
    w = world(opt)
    return 1 if "sync_folder_uri" not in w.restore(w.backup("A")) else 0


def case_personal_travels(opt):
    """equipoise: the burnout threshold and crisis contacts arrive on the restored phone (Transfer.kt:34,70)."""
    w = world(opt)
    c = w.restore(w.backup("A"))
    return 1 if (c.get("burnout_threshold"), c.get("crisis_contacts")) == ("0.4", "sam: 555") else 0


def case_first_run_not_restored(opt):
    """shared (fix): a per-device first-run flag is not carried to a new phone; Mnemo's restore
    carries it today (AppSettingsStore.kt:108)."""
    w = world(opt)
    return 1 if "first_run_flag" not in w.restore(w.backup("A")) else 0


CASES = {
    "tendril-secret-never-leaves": ("tendril", stays_on_a("ai_api_key", "sk-A")),
    "tendril-layout-per-device": ("tendril", stays_on_a("window_frame", "1200x800@0,0")),
    "chronicle-device-id-own": ("chronicle", case_device_id),
    "mnemo-mode-per-device": ("mnemo", case_mode_per_device),
    "mnemo-backup-restores-prefs": ("mnemo", case_backup_restores_prefs),
    "mnemo-folder-not-restored": ("mnemo", case_folder_not_restored),
    "equipoise-personal-travels": ("equipoise", case_personal_travels),
    "equipoise-llm-stays": ("equipoise", stays_on_a("llm_model_uri", "file:///A/gemma.gguf")),
    "shared-first-run-not-restored": ("shared", case_first_run_not_restored),
}


def main():
    sim = {o: {cid: fn(o) for cid, (_, fn) in CASES.items()} for o in OPTIONS}
    with open(os.path.join(ROOT, "decisions", "options", "09-settings.sim.json"), "w",
              encoding="utf-8", newline="") as fh:
        json.dump(sim, fh, indent=1)
    print("%-32s" % "case" + "".join("%-14s" % o for o in OPTIONS))
    for cid in CASES:
        print("%-32s" % cid + "".join("%-14s" % sim[o][cid] for o in OPTIONS))
    print("%-32s" % "growth (storage places)" + "".join("%-14s" % GROWTH[o] for o in OPTIONS))


if __name__ == "__main__":
    main()
