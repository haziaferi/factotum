"""Contest 01 (sync): replay multi-device scenarios against each sync model and score the
properties the owner apps guarantee. Each model is rebuilt from the verified source
(decisions/verify/01-sync/*.json); the file:line each rule comes from is next to it.

    python tools/sync_sim.py            # writes decisions/options/01-sync.sim.json + prints a table

Models
  tendril    whole-row LWW on updatedAt, strict isAfter, tie keeps local
             (SnapshotSyncOrchestrator.kt:1571); trash = deletedAt field of the row;
             purge = PurgedRecord, never expires, superseded by a newer record (PurgeRegistry.kt:94)
  chronicle  per field-group stamps (updatedAt, deviceId) total order (FieldStamp.kt:36);
             deletedAt in the schedule group (ReminderMerge.kt:13); stamps >24h ahead clamped to
             now for comparison (FieldStamp.kt:91); tombstones GC'd after 90 days (Syncable.kt:22)
  mnemo      whole row; differing updatedAt on a moved file = conflict for a person, equal =
             unchanged (ReminderSyncManager.kt:155-160); isArchived tombstone never purged
  replace    control: Equipoise's Importer.merge, incoming row REPLACEs by id, hard delete,
             no stamps (Transfer.kt:57, Daos.kt:16)
  hybrid     chronicle's field groups + a hybrid logical clock stamp (HLC, deviceId) +
             tendril's permanent purge registry
  hybrid+    hybrid, plus: a concurrent change to the SCHEDULE group on both sides since the last
             agreed stamp (per-row base) is shown to a person instead of resolved (mnemo's rule,
             narrowed to the one group where a silent change is dangerous)
"""
import copy
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAY = 24 * 3600
GROUPS = {"schedule": ("due", "deleted"), "status": ("done",)}
MODELS = ["tendril", "chronicle", "mnemo", "replace", "hybrid", "hybrid+"]


class Device:
    def __init__(self, name, model, skew=0):
        self.name, self.model, self.skew = name, model, skew
        self.rows, self.purged, self.conflicts, self.base = {}, {}, set(), {}
        self.hlc = 0

    # -- stamps ------------------------------------------------------------
    def stamp(self, now):
        wall = now + self.skew
        if self.model.startswith("hybrid"):
            self.hlc = max(self.hlc + 1, wall)
            return (self.hlc, self.name)
        return (wall, self.name)

    def observe(self, st):
        if self.model.startswith("hybrid"):
            self.hlc = max(self.hlc, st[0])

    # -- local writes --------------------------------------------------------
    def create(self, uid, now, due="d0"):
        st = self.stamp(now)
        self.rows[uid] = {"uid": uid, "due": due, "deleted": None, "done": False,
                          "st": {"schedule": st, "status": st}, "updatedAt": st}
        self.base[uid] = {"schedule": st, "status": st}

    def edit(self, uid, now, **changes):
        row = self.rows[uid]
        st = self.stamp(now)
        if self.model == "replace" and changes.get("deleted"):
            del self.rows[uid]                      # hard delete, nothing travels
            return
        for k, v in changes.items():
            row[k] = v
            for g, fields in GROUPS.items():
                if k in fields:
                    row["st"][g] = st
        row["updatedAt"] = st

    def purge(self, uid, now):
        """Permanent delete ('empty trash'). Chronicle has no user purge: its GC does it."""
        if self.model in ("tendril", "hybrid", "hybrid+"):
            self.purged[uid] = self.stamp(now)
            self.rows.pop(uid, None)
        elif self.model == "chronicle":
            self.gc(now)

    def gc(self, now):
        if self.model == "chronicle":
            for uid in [u for u, r in self.rows.items()
                        if r["deleted"] is not None and now - r["deleted"] > 90 * DAY]:
                del self.rows[uid]

    # -- merge -----------------------------------------------------------------
    def clamp(self, st, now):
        if self.model == "chronicle" and st[0] > now + self.skew + DAY:
            return (now + self.skew, st[1])
        return st

    def import_(self, rows, purged, now):
        m = self.model
        if m in ("tendril", "hybrid", "hybrid+"):
            for uid, pst in purged.items():         # earliest purgedAt wins (PurgeRegistry.kt:169)
                self.purged[uid] = min(pst, self.purged.get(uid, pst))
            for uid, pst in list(self.purged.items()):
                r = self.rows.get(uid)
                if r and not max(r["st"].values()) > pst:
                    del self.rows[uid]
                elif r:
                    del self.purged[uid]
        for inc in rows.values():
            inc = copy.deepcopy(inc)
            uid = inc["uid"]
            for st in inc["st"].values():
                self.observe(st)
            local = self.rows.get(uid)
            if m in ("tendril", "hybrid", "hybrid+") and uid in self.purged:
                if max(inc["st"].values()) > self.purged[uid]:
                    del self.purged[uid]
                else:
                    continue
            if local is None:
                self.rows[uid] = inc
                self.base[uid] = dict(inc["st"])
                continue
            if m == "replace":
                self.rows[uid] = inc
            elif m == "tendril":
                if inc["updatedAt"][0] > local["updatedAt"][0]:   # strict, time only
                    self.rows[uid] = inc
            elif m == "mnemo":
                if inc["updatedAt"] != local["updatedAt"]:
                    self.conflicts.add(uid)
            else:                                   # chronicle / hybrid / hybrid+
                for g, fields in GROUPS.items():
                    ls, is_ = self.clamp(local["st"][g], now), self.clamp(inc["st"][g], now)
                    if m == "hybrid+" and g == "schedule":
                        b = self.base.get(uid, {}).get(g)
                        both = local["st"][g] != b and inc["st"][g] != b
                        differ = any(local[f] != inc[f] for f in fields)
                        if both and differ:
                            self.conflicts.add(uid)
                            continue
                    if is_ > ls:
                        for f in fields:
                            local[f] = inc[f]
                        # chronicle persists the clamped stamp as the winner's effective stamp
                        local["st"][g] = is_ if m == "chronicle" else inc["st"][g]
                    self.base.setdefault(uid, {})[g] = local["st"][g]
        self.gc(now)

    def export(self):
        return copy.deepcopy(self.rows), dict(self.purged)


def sync(devs, now, rounds=3):
    for _ in range(rounds):
        for a in devs:
            for b in devs:
                if a is not b:
                    a.import_(*b.export(), now)


def view(d, uid):
    r = d.rows.get(uid)
    if r is None:
        return "gone"
    return (r["due"], r["deleted"] is not None, r["done"])


def same(devs, uid):
    return len({str(view(d, uid)) for d in devs}) == 1


def surfaced(devs, uid):
    return any(uid in d.conflicts for d in devs)


# -- scenarios: each returns 1 (property holds), 0.5 (shown to a person, not guaranteed), 0 --
def s_group_merge(m):
    """chronicle: due edited on A, done on B concurrently -> both survive everywhere."""
    a, b = Device("A", m), Device("B", m)
    a.create("x", 0); sync([a, b], 1)
    a.edit("x", 10, due="d1"); b.edit("x", 11, done=True); sync([a, b], 12)
    ok = all(view(d, "x") == ("d1", False, True) for d in (a, b))
    return 1 if ok else 0.5 if surfaced([a, b], "x") else 0


def s_tie_converge(m):
    """chronicle: same-millisecond edits to the same field converge on every device."""
    a, b = Device("A", m), Device("B", m)
    a.create("x", 0); sync([a, b], 1)
    a.edit("x", 10, due="dA"); b.edit("x", 10, due="dB"); sync([a, b], 11)
    return 1 if same([a, b], "x") else 0.5 if surfaced([a, b], "x") else 0


def s_skew(m):
    """chronicle: a device 48 h ahead cannot out-rank an edit made after its own was seen."""
    a, b = Device("A", m), Device("B", m, skew=2 * DAY)
    a.create("x", 0); sync([a, b], 1)
    b.edit("x", 10, due="dB"); sync([a, b], 11)
    a.edit("x", 20, due="dA"); sync([a, b], 21)
    ok = all(view(d, "x")[0] == "dA" for d in (a, b))
    return 1 if ok else 0.5 if surfaced([a, b], "x") else 0


def s_delete_vs_status(m):
    """chronicle: delete on A, a later done-flip on B does not bring the row back."""
    a, b = Device("A", m), Device("B", m)
    a.create("x", 0); sync([a, b], 1)
    a.edit("x", 10, deleted=10); b.edit("x", 11, done=True); sync([a, b], 12)
    ok = all(view(d, "x") in ("gone",) or view(d, "x")[1] for d in (a, b))
    return 1 if ok else 0.5 if surfaced([a, b], "x") else 0


def s_purge_stale(m):
    """tendril: a purged row stays purged when a device that never edited it returns 100 days later."""
    a, b = Device("A", m), Device("B", m)
    a.create("x", 0); sync([a, b], 1)
    a.edit("x", 10, deleted=10); a.purge("x", 10 + 100 * DAY)
    sync([a, b], 11 + 100 * DAY)
    ok = all(view(d, "x") == "gone" or view(d, "x")[1] for d in (a, b))
    return 1 if ok else 0.5 if surfaced([a, b], "x") else 0


def s_late_join(m):
    """tendril: a new empty device adopts every live row and every deletion."""
    a, b = Device("A", m), Device("B", m)
    a.create("x", 0); a.create("y", 0); a.edit("y", 5, deleted=5)
    sync([a], 6)
    c = Device("C", m); sync([a, c], 7)
    ok = view(c, "x") == ("d0", False, False) and view(c, "y") in ("gone",) or \
        (view(c, "x") == ("d0", False, False) and view(c, "y")[1])
    return 1 if ok else 0


def s_remote_only(m):
    """tendril/chronicle: an edit made on one device only is adopted with no one asked."""
    a, b = Device("A", m), Device("B", m)
    a.create("x", 0); sync([a, b], 1)
    a.edit("x", 10, due="d1"); sync([a, b], 11)
    ok = all(view(d, "x")[0] == "d1" for d in (a, b)) and not surfaced([a, b], "x")
    return 1 if ok else 0


def s_same_field_shown(m):
    """mnemo: two devices change the same reminder's time -> a person sees it, nothing silent."""
    a, b = Device("A", m), Device("B", m)
    a.create("x", 0); sync([a, b], 1)
    a.edit("x", 10, due="dA"); b.edit("x", 11, due="dB"); sync([a, b], 12)
    return 1 if surfaced([a, b], "x") else 0


def s_delete_vs_edit_shown(m):
    """mnemo: delete on A and a later time change on B -> a person decides."""
    a, b = Device("A", m), Device("B", m)
    a.create("x", 0); sync([a, b], 1)
    a.edit("x", 10, deleted=10); b.edit("x", 11, due="dB"); sync([a, b], 12)
    return 1 if surfaced([a, b], "x") else 0


def s_converges(m):
    """shared: after a busy exchange every device holds the same rows (or a person is asked)."""
    a, b, c = Device("A", m), Device("B", m, skew=3), Device("C", m)
    a.create("x", 0); b.create("y", 0); sync([a, b, c], 1)
    a.edit("x", 10, done=True); b.edit("x", 10, due="dB"); c.edit("y", 10, deleted=10)
    b.edit("y", 12, due="dy"); sync([a, b, c], 13)
    ok = same([a, b, c], "x") and same([a, b, c], "y")
    return 1 if ok else 0.5 if surfaced([a, b, c], "x") or surfaced([a, b, c], "y") else 0


SCENARIOS = {
    "chronicle-group-merge": s_group_merge,
    "chronicle-tie-converges": s_tie_converge,
    "shared-later-edit-beats-fast-clock": s_skew,
    "chronicle-delete-beats-status": s_delete_vs_status,
    "tendril-purge-holds": s_purge_stale,
    "tendril-late-join": s_late_join,
    "tendril-remote-edit-silent": s_remote_only,
    "mnemo-same-time-shown": s_same_field_shown,
    "mnemo-delete-vs-edit-shown": s_delete_vs_edit_shown,
    "shared-converges": s_converges,
}

# map's claim to test: delete on A, later edit on B -> tombstone-union and LWW disagree?
def delete_then_edit(m):
    a, b = Device("A", m), Device("B", m)
    a.create("x", 0); sync([a, b], 1)
    a.edit("x", 10, deleted=10); b.edit("x", 11, due="dB"); sync([a, b], 12)
    return "shown to a person" if surfaced([a, b], "x") else \
        "stays deleted" if view(a, "x") == "gone" or view(a, "x")[1] else "edit resurrects it"


def main():
    sim = {m: {cid: fn(m) for cid, fn in SCENARIOS.items()} for m in MODELS}
    path = os.path.join(ROOT, "decisions", "options", "01-sync.sim.json")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        json.dump(sim, fh, indent=1)
    print("%-32s" % "scenario" + "".join("%-10s" % m for m in MODELS))
    for cid in SCENARIOS:
        print("%-32s" % cid + "".join("%-10s" % sim[m][cid] for m in MODELS))
    print("\ndelete on A, then a later edit on B (the map's claim):")
    for m in MODELS:
        print("  %-10s %s" % (m, delete_then_edit(m)))


if __name__ == "__main__":
    main()
