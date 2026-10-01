"""Contest 13 (sync folder layout): replay a workload through each folder layout over a model of
Syncthing, with ADR 01's state-based merge on every device, and measure what each layout costs.

    python tools/folder_sim.py                 # all layouts, default workload, writes 13-folder.sim.json
    python tools/folder_sim.py --days 14 --seeds 5

The merge is ADR 01's: per (row, group) the higher stamp wins, and it is idempotent and order-free,
so a layout loses data only when some version never reaches a device that should hold it. Every run
ends with all devices online until nothing changes; any device whose state differs from the join of
every version ever written has lost something. That count is the hard objective.

Syncthing, as modelled (each rule carries the source the research brief confirmed, in
decisions/verify/13-folder/):
  - a file is replaced atomically (temp file, then rename); there is no order between files
  - a sync session may end part-way, after any whole file
  - two versions of a file changed concurrently: the one with the newer mtime keeps the name, the
    other becomes  name.sync-conflict-<...>  and that copy syncs like any file
  - transfer is per block: an append sends the tail, a rewrite sends from the first changed byte
    (no rolling-hash reuse is assumed; that is the pessimistic case)

App, as modelled:
  - after a local write the app exports after a debounce; before writing a SHARED file it reads and
    merges it, and the write lands `write_ms` later; a peer version arriving in between is overwritten
    (the lost-update race of shared files). A device-owned file has no such race: only its owner writes it.
  - the app imports the folder before each export and every `import_every` minutes while online
  - layouts flagged `reads_conflicts` merge  .sync-conflict-  copies, then delete them
"""
import argparse
import heapq
import json
import math
import os
import random
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOCK = 128 * 1024
FILE_OVERHEAD = 300          # bytes of index/metadata Syncthing exchanges per changed file

# ---------------------------------------------------------------------------- layouts
# owner: "shared" (any device writes the file) or "device" (only its owner writes it)
# unit:  how rows map to files: "all" | "area" | "row" | "log"
LAYOUTS = {
    "one-file":            dict(owner="shared", unit="all"),
    "one-file+copies":     dict(owner="shared", unit="all", reads_conflicts=True),
    "per-area":            dict(owner="shared", unit="area"),
    "per-area+copies":     dict(owner="shared", unit="area", reads_conflicts=True),
    "per-row":             dict(owner="shared", unit="row"),
    "per-row+copies":      dict(owner="shared", unit="row", reads_conflicts=True),
    "device-snapshot":     dict(owner="device", unit="all"),
    "device-area":         dict(owner="device", unit="area"),
    "device-row":          dict(owner="device", unit="row"),
    "device-log":          dict(owner="device", unit="log"),
    "device-log+copies":   dict(owner="device", unit="log", reads_conflicts=True),
    "device-chunks":       dict(owner="device", unit="chunk"),
    "device-chunks-own":   dict(owner="device", unit="chunk", relay=False),
    "device-chunks-area":  dict(owner="device", unit="chunk", snapshot="area"),
}
CONTROL = "one-file"


# ---------------------------------------------------------------------------- workload
def load_workload(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


class Row:
    __slots__ = ("id", "area", "size", "order")

    def __init__(self, rid, area, size, order):
        self.id, self.area, self.size, self.order = rid, area, size, order


# ---------------------------------------------------------------------------- the folder
class FileCopy:
    """One device's copy of one file: its entries, a version vector, an mtime and a size."""
    __slots__ = ("entries", "vv", "mtime", "size")

    def __init__(self, entries, vv, mtime, size):
        self.entries, self.vv, self.mtime, self.size = entries, vv, mtime, size


def dominates(a, b):
    return all(a.get(k, 0) >= v for k, v in b.items())


class Device:
    def __init__(self, name):
        self.name = name
        self.state = {}                 # (row, group) -> stamp
        self.folder = {}                # file name -> FileCopy
        self.read_marks = {}            # file name -> vv last imported (device-local)
        self.pending_export = False
        self.hlc = 0
        self.log_seq = 0
        self.log_size = 0
        self.dirty_rows = set()
        self.since_compact = set()       # areas written since the last compaction


class Sim:
    def __init__(self, layout, workload, seed, days, devices):
        self.cfg = LAYOUTS[layout]
        self.layout = layout
        self.w = workload
        self.w["app"].update(workload.get("tuned", {}).get(layout, {}))   # each layout at its tuned knobs
        self.rng = random.Random(seed)
        self.days = days
        self.devs = [Device(n) for n in devices]
        self.rows = {}
        self.areas = list(workload["kinds"])
        self.events = []
        self.seq = 0
        self.truth = {}                 # (row, group) -> max stamp ever written
        self.written_at = {}            # stamp -> wall time it was written
        self.delays = []
        self.m = defaultdict(float)     # metrics
        self.order = 0

    # -- events --------------------------------------------------------------
    def at(self, t, kind, *args):
        self.seq += 1
        heapq.heappush(self.events, (t, self.seq, kind, args))

    def online(self, dev, t):
        sched = self.w["devices"].get(dev.name, {"always": True, "from": 0, "to": 1440})
        minute = (t / 60) % 1440
        return sched["from"] <= minute < sched["to"] or sched.get("always", False)

    def next_online(self, dev, t):
        if dev.name not in self.w["devices"] or self.online(dev, t):
            return t
        sched = self.w["devices"][dev.name]
        day = t - (t % 86400)
        start = day + sched["from"] * 60
        return start if start > t else start + 86400

    # -- local writes -----------------------------------------------------------
    def stamp(self, dev, t):
        dev.hlc = max(dev.hlc + 1, int(t * 1000))
        return (dev.hlc, dev.name)

    def write(self, dev, t, kind):
        k = self.w["kinds"][kind]
        if not self.rows or self.rng.random() < k["create_share"] or not [r for r in self.rows.values() if r.area == kind]:
            self.order += 1
            rid = "%s-%d" % (kind, self.order)
            self.rows[rid] = Row(rid, kind, k["bytes"], self.order)
            row = self.rows[rid]
            groups = k["groups"]
        else:
            mine = [r for r in self.rows.values() if r.area == kind and any((r.id, g) in dev.state for g in k["groups"])]
            if not mine:
                return
            # edits favour recent rows
            mine.sort(key=lambda r: r.order)
            row = mine[min(len(mine) - 1, int(len(mine) * (1 - self.rng.random() ** 3)))]
            groups = [self.rng.choice(k["groups"])]
        s = self.stamp(dev, t)
        self.written_at[s] = t
        for g in groups:
            dev.state[(row.id, g)] = s
            if s > self.truth.get((row.id, g), (0, "")):
                self.truth[(row.id, g)] = s
        dev.dirty_rows.add(row.id)
        if not dev.pending_export:
            dev.pending_export = True
            self.at(t + self.w["app"]["debounce_s"], "export", dev)

    # -- file mapping ---------------------------------------------------------------
    def file_of(self, dev, row):
        unit, owner = self.cfg["unit"], self.cfg["owner"]
        prefix = "" if owner == "shared" else "devices/%s/" % dev.name
        if unit == "all":
            return prefix + "state.json"
        if unit == "area":
            return prefix + "%s.json" % row.area
        if unit == "row":
            return prefix + "rows/%s.json" % row.id
        raise ValueError(unit)

    def entries_for(self, dev, name):
        """What the device writes into a file: its state restricted to the file's rows."""
        unit = self.cfg["unit"]
        if unit == "all":
            return dict(dev.state)
        if unit == "area":
            area = name.rsplit("/", 1)[-1][:-5]
            return {k: v for k, v in dev.state.items() if self.rows[k[0]].area == area}
        rid = name.rsplit("/", 1)[-1][:-5]
        return {k: v for k, v in dev.state.items() if k[0] == rid}

    def size_of(self, entries):
        seen = {k[0] for k in entries}
        return sum(self.rows[r].size for r in seen) + 2

    # -- import / export --------------------------------------------------------------
    def import_folder(self, dev, t):
        reads = 0
        for name, fc in list(dev.folder.items()):
            if fc.entries is None:
                continue
            conflict = ".sync-conflict-" in name
            if conflict and not self.cfg.get("reads_conflicts"):
                continue
            if dev.read_marks.get(name) == fc.vv and not conflict:
                continue
            if self.cfg["unit"] == "log" and "/log-" in name:
                reads += fc.size - (dev.read_marks.get(name + "#off", 0) if not conflict else 0)
                dev.read_marks[name + "#off"] = fc.size
            else:
                reads += fc.size
                self.m["file_opens"] += 1
            stale = self.cfg["owner"] == "shared" and not conflict
            for key, s in fc.entries.items():
                if stale and dev.state.get(key, (0, "")) > s:
                    # the shared file holds an older version than ours: write it again
                    dev.dirty_rows.add(key[0])
                    if not dev.pending_export:
                        dev.pending_export = True
                        self.at(t + self.w["app"]["debounce_s"], "export", dev)
                if s > dev.state.get(key, (0, "")):
                    dev.state[key] = s
                    dev.dirty_rows.add(key[0])
                    if s in self.written_at and t < self.days * 86400:
                        # measured from when this device was next online, so a laptop's night off is not a delay
                        self.delays.append(t - self.next_online(dev, self.written_at[s]))
            dev.read_marks[name] = dict(fc.vv)
            if conflict:
                self.delete_file(dev, name, t)
        self.m["bytes_read"] += reads

    def delete_file(self, dev, name, t):
        dev.folder[name] = FileCopy({}, self.bump(dev.folder[name].vv, dev), t, 0)
        dev.folder[name].entries = None   # tombstone

    def bump(self, vv, dev):
        nv = dict(vv)
        nv[dev.name] = nv.get(dev.name, 0) + 1
        return nv

    def export(self, dev, t):
        dev.pending_export = False
        if not dev.dirty_rows:
            return
        self.import_folder(dev, t)
        if self.cfg["unit"] == "log":
            self.export_log(dev, t)
        elif self.cfg["unit"] == "chunk":
            self.export_chunk(dev, t)
        else:
            names = {self.file_of(dev, self.rows[r]) for r in dev.dirty_rows}
            if self.cfg["owner"] == "shared":
                # read now, write after write_ms: a peer version landing in between is overwritten
                snapshot = {n: (dict(dev.folder[n].vv) if n in dev.folder and dev.folder[n].entries is not None else None)
                            for n in names}
                self.at(t + self.w["app"]["write_ms"] / 1000.0, "write_files", dev, names, snapshot)
            else:
                self.write_files(dev, t, names, None)
        dev.dirty_rows = set()

    def write_files(self, dev, t, names, snapshot):
        for name in names:
            entries = self.entries_for(dev, name)
            old = dev.folder.get(name)
            if snapshot is not None and old is not None and old.entries is not None and snapshot.get(name) != old.vv:
                # a peer's version arrived after we read: anything in it we had not merged is lost
                self.m["race_overwrites"] += 1
            vv = self.bump(old.vv if old else {}, dev)
            size = self.size_of(entries)
            dev.folder[name] = FileCopy(entries, vv, t, size)
            dev.read_marks[name] = dict(vv)
            self.m["bytes_written"] += size
            self.m["file_writes"] += 1

    def export_log(self, dev, t):
        app = self.w["app"]
        entries = {(r, g): s for (r, g), s in dev.state.items() if r in dev.dirty_rows}
        add = self.size_of(entries)
        name = "devices/%s/log-%06d.jsonl" % (dev.name, dev.log_seq)
        old = dev.folder.get(name)
        if old is not None and old.size + add > app["segment_bytes"]:
            dev.log_seq += 1
            name = "devices/%s/log-%06d.jsonl" % (dev.name, dev.log_seq)
            old = None
            if dev.log_seq % app["snapshot_every"] == 0:
                self.compact(dev, t)
        merged = dict(old.entries) if old else {}
        merged.update(entries)
        vv = self.bump(old.vv if old else {}, dev)
        dev.folder[name] = FileCopy(merged, vv, t, (old.size if old else 0) + add)
        dev.read_marks[name] = dict(vv)
        dev.read_marks[name + "#off"] = dev.folder[name].size
        self.m["bytes_written"] += dev.folder[name].size   # temp file + rename rewrites the segment
        self.m["file_creates"] += 0 if old else 1
        self.m["file_writes"] += 1

    def export_chunk(self, dev, t):
        """A new immutable file per export; past `snapshot_every` chunks, fold them into the snapshot."""
        entries = {(r, g): s for (r, g), s in dev.state.items() if r in dev.dirty_rows}
        if self.cfg.get("relay") is False:
            entries = {k: s for k, s in entries.items() if s[1] == dev.name}
            if not entries:
                return
        dev.since_compact |= {self.rows[k[0]].area for k in entries}
        dev.log_seq += 1
        name = "devices/%s/chunk-%06d.json" % (dev.name, dev.log_seq)
        size = self.size_of(entries)
        dev.folder[name] = FileCopy(entries, {dev.name: 1}, t, size)
        dev.read_marks[name] = {dev.name: 1}
        self.m["file_creates"] += 1
        self.m["bytes_written"] += size
        self.m["file_writes"] += 1
        live = [n for n, f in dev.folder.items() if n.startswith("devices/%s/chunk-" % dev.name) and f.entries is not None]
        if len(live) > self.w["app"]["chunks_before_compaction"]:
            self.compact(dev, t, prefix="devices/%s/chunk-" % dev.name, keep=None)

    def compact(self, dev, t, prefix=None, keep="current"):
        """Snapshot this device's state (whole, or only the areas written since), then retire its older files."""
        state = dev.state if self.cfg.get("relay") is not False else {k: s for k, s in dev.state.items() if s[1] == dev.name}
        if self.cfg.get("snapshot") == "area":
            parts = {"devices/%s/snapshot-%s.json" % (dev.name, a): {k: s for k, s in state.items() if self.rows[k[0]].area == a}
                     for a in dev.since_compact}
        else:
            parts = {"devices/%s/snapshot.json" % dev.name: dict(state)}
        dev.since_compact = set()
        for name, part in parts.items():
            old = dev.folder.get(name)
            vv = self.bump(old.vv if old else {}, dev)
            size = self.size_of(part)
            dev.folder[name] = FileCopy(part, vv, t, size)
            dev.read_marks[name] = dict(vv)
            self.m["bytes_written"] += size
        prefix = prefix or "devices/%s/log-" % dev.name
        for n in list(dev.folder):
            if n.startswith(prefix) and dev.folder[n].entries is not None:
                if keep == "current" and n.endswith("%06d.jsonl" % dev.log_seq):
                    continue
                self.delete_file(dev, n, t)

    # -- Syncthing ---------------------------------------------------------------------
    def session(self, a, b, t):
        names = sorted(set(a.folder) | set(b.folder))
        self.rng.shuffle(names)
        cut = len(names) if self.rng.random() > self.w["syncthing"]["cut_chance"] else self.rng.randint(0, len(names))
        for name in names[:cut]:
            fa, fb = a.folder.get(name), b.folder.get(name)
            if fa is not None and fb is not None and fa.vv == fb.vv:
                continue
            if fb is None or (fa is not None and dominates(fa.vv, fb.vv)):
                self.deliver(fa, b, name, fb, t)
            elif fa is None or dominates(fb.vv, fa.vv):
                self.deliver(fb, a, name, fa, t)
            else:
                self.conflict(a, b, name, t)

    def deliver(self, src, dst, name, old, t):
        if src.entries is None:
            dst.folder[name] = FileCopy(None, dict(src.vv), src.mtime, 0)
            self.m["bytes_sent"] += FILE_OVERHEAD
            return
        start = self.first_changed_byte(src, old, name)
        dst.folder[name] = FileCopy(dict(src.entries), dict(src.vv), src.mtime, src.size)
        sent = 0 if start is None else src.size - (start // BLOCK) * BLOCK
        self.m["bytes_sent"] += FILE_OVERHEAD + sent

    def first_changed_byte(self, new, old, name=""):
        """Offset of the first byte that differs; None when nothing does. Rows sit in id order."""
        if old is None or old.entries is None:
            return 0
        if self.cfg["unit"] in ("log", "chunk") and "/snapshot" not in name:
            return old.size if new.size > old.size else 0
        diff = [k for k, s in new.entries.items() if old.entries.get(k) != s]
        if not diff:
            return None
        first = min(self.rows[k[0]].order for k in diff)
        return sum(self.rows[r].size for r in {k[0] for k in new.entries} if self.rows[r].order < first)

    def conflict(self, a, b, name, t):
        fa, fb = a.folder[name], b.folder[name]
        if fa.entries is None and fb.entries is None:
            merged_vv = {k: max(fa.vv.get(k, 0), fb.vv.get(k, 0)) for k in set(fa.vv) | set(fb.vv)}
            for d in (a, b):
                d.folder[name] = FileCopy(None, dict(merged_vv), max(fa.mtime, fb.mtime), 0)
            return
        win, lose = (fa, fb) if (fa.mtime, b.name) > (fb.mtime, a.name) else (fb, fa)
        copy = "%s.sync-conflict-%d" % (name, self.seq)
        self.seq += 1
        merged_vv = dict(fa.vv)
        for k, v in fb.vv.items():
            merged_vv[k] = max(v, merged_vv.get(k, 0))
        for d in (a, b):
            d.folder[name] = FileCopy(dict(win.entries) if win.entries is not None else None, merged_vv, win.mtime, win.size)
            if lose.entries is not None:
                d.folder[copy] = FileCopy(dict(lose.entries), {"conflict": 1}, lose.mtime, lose.size)
        self.m["conflict_copies"] += 1
        self.m["bytes_sent"] += FILE_OVERHEAD + win.size

    # -- run ------------------------------------------------------------------------------
    def preseed(self, history_days):
        """Start from `history_days` of rows already written and synced: every device holds them and
        the folder already carries each layout's files for them. Costs are then measured on top."""
        names = list(self.w["devices"])
        shares = [self.w["devices"][n]["share"] for n in names]
        hlc = 0
        by_row = defaultdict(dict)
        for kind, k in self.w["kinds"].items():
            for _ in range(int(k["per_day"] * k["create_share"] * history_days)):
                self.order += 1
                rid = "%s-%d" % (kind, self.order)
                self.rows[rid] = Row(rid, kind, k["bytes"], self.order)
                author = self.rng.choices(names, shares)[0]
                for g in k["groups"]:
                    hlc += 1
                    s = (hlc, author)
                    self.truth[(rid, g)] = s
                    by_row[rid][(rid, g)] = s
        for d in self.devs:
            d.state = dict(self.truth)
            d.hlc = hlc
        files = {}
        unit, owner = self.cfg["unit"], self.cfg["owner"]
        writers = self.devs[:1] if owner == "shared" else self.devs
        for d in writers:
            prefix = "" if owner == "shared" else "devices/%s/" % d.name
            if unit == "all":
                groups = {prefix + "state.json": dict(self.truth)}
            elif unit == "area":
                groups = defaultdict(dict)
                for key, s in self.truth.items():
                    groups[prefix + "%s.json" % self.rows[key[0]].area][key] = s
            elif unit == "row":
                groups = {prefix + "rows/%s.json" % r: e for r, e in by_row.items()}
            else:
                state = self.truth if self.cfg.get("relay") is not False else {k: s for k, s in self.truth.items() if s[1] == d.name}
                if self.cfg.get("snapshot") == "area":
                    groups = defaultdict(dict)
                    for key, s in state.items():
                        groups[prefix + "snapshot-%s.json" % self.rows[key[0]].area][key] = s
                else:
                    groups = {prefix + "snapshot.json": dict(state)}
            for name, entries in groups.items():
                files[name] = FileCopy(entries, {d.name: 1}, 0, self.size_of(entries))
        for d in self.devs:
            d.folder = {n: FileCopy(dict(f.entries), dict(f.vv), f.mtime, f.size) for n, f in files.items()}
            d.read_marks = {n: dict(f.vv) for n, f in files.items()}
        self.m = defaultdict(float)

    def run(self):
        horizon = self.days * 86400
        for dev in self.devs:
            for kind, k in self.w["kinds"].items():
                rate = k["per_day"] * self.w["devices"][dev.name]["share"]
                t = 0.0
                while rate > 0:
                    t += self.rng.expovariate(rate / 86400)
                    if t >= horizon:
                        break
                    self.at(t, "write", dev, kind)
        step = self.w["syncthing"]["session_every_s"]
        for i in range(int(horizon / step)):
            self.at(i * step, "sync")
        for day in range(self.days):
            self.at(day * 86400 + self.w["devices"][self.devs[-1].name]["from"] * 60, "sample")
        for i in range(int(horizon / (self.w["app"]["import_every_min"] * 60))):
            self.at(i * self.w["app"]["import_every_min"] * 60, "import")
        while self.events:
            t, _, kind, args = heapq.heappop(self.events)
            if kind == "write":
                if self.online(args[0], t) or self.w["devices"][args[0].name].get("writes_offline", True):
                    self.write(args[0], t, args[1])
            elif kind == "export":
                self.export(args[0], t)
            elif kind == "write_files":
                self.write_files(args[0], t, args[1], args[2])
            elif kind == "sample":
                self.sample_single_points(t)
            elif kind == "import":
                for d in self.devs:
                    if self.online(d, t):
                        self.import_folder(d, t)
            elif kind == "sync":
                live = [d for d in self.devs if self.online(d, t)]
                for i, a in enumerate(live):
                    for b in live[i + 1:]:
                        self.session(a, b, t)
        return self.settle(horizon)

    def sample_single_points(self, t):
        """Share of the last week's newest versions held by at most one file on the first device."""
        recent = {k: s for k, s in self.truth.items() if self.written_at.get(s, 0) > t - 7 * 86400}
        if not recent:
            return
        holders = defaultdict(int)
        for name, f in self.devs[0].folder.items():
            if f.entries is None or ".sync-conflict-" in name:
                continue
            for k, s in f.entries.items():
                if recent.get(k) == s:
                    holders[k] += 1
        share = sum(1 for k in recent if holders[k] <= 1) / len(recent)
        self.m["single_point_worst"] = max(self.m["single_point_worst"], share)

    def settle(self, t):
        """Everyone online, no cuts, until nothing changes; then compare with the truth."""
        cut = self.w["syncthing"]["cut_chance"]
        self.w["syncthing"]["cut_chance"] = 0
        self.events = [e for e in self.events if e[2] in ("export", "write_files")]
        for _ in range(12):
            pending, self.events = sorted(self.events), []
            for _, _, kind, args in pending:
                if kind == "export":
                    self.export(args[0], t)
                elif kind == "write_files":
                    self.write_files(args[0], t, args[1], args[2])
            for _, _, kind, args in sorted(self.events):
                if kind == "write_files":
                    self.write_files(args[0], t, args[1], args[2])
            self.events = [e for e in self.events if e[2] == "export"]
            for i, a in enumerate(self.devs):
                for b in self.devs[i + 1:]:
                    self.session(a, b, t)
            for d in self.devs:
                self.import_folder(d, t)
            t += 1
        self.w["syncthing"]["cut_chance"] = cut
        lost = 0
        for d in self.devs:
            lost += sum(1 for k, s in self.truth.items() if d.state.get(k) != s)
        files = len({n for d in self.devs for n, f in d.folder.items() if f.entries is not None})
        join = sum(f.size for n, f in self.devs[0].folder.items() if f.entries is not None and ".sync-conflict-" not in n)
        return {
            "lost_versions": lost,
            "conflict_copies": self.m["conflict_copies"],
            "race_overwrites": self.m["race_overwrites"],
            "written_MB_per_day": round(self.m["bytes_written"] / self.days / len(self.devs) / 1e6, 3),
            "sent_MB_per_day": round(self.m["bytes_sent"] / self.days / 1e6, 3),
            "read_MB_per_day": round(self.m["bytes_read"] / self.days / len(self.devs) / 1e6, 3),
            "files": files,
            "join_MB": round(join / 1e6, 3),
            "rows": len(self.rows),
            "dataset_MB": round(sum(r.size for r in self.rows.values()) / 1e6, 3),
            "single_point_worst": round(self.m["single_point_worst"], 3),
            "file_creates_per_day": round(self.m["file_creates"] / self.days, 1),
            "p95_delay_min": round(sorted(self.delays)[int(0.95 * (len(self.delays) - 1))] / 60, 1) if self.delays else 0,
        }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workload", default=os.path.join(ROOT, "decisions", "options", "13-folder.workload.json"))
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--only", default="")
    args = ap.parse_args()
    w = load_workload(args.workload)
    layouts = args.only.split(",") if args.only else list(LAYOUTS)
    out = {}
    for name in layouts:
        runs = [Sim(name, json.loads(json.dumps(w)), seed, args.days, list(w["devices"])).run() for seed in range(args.seeds)]
        out[name] = {k: round(sum(r[k] for r in runs) / len(runs), 3) for k in runs[0]}
        print("%-20s %s" % (name, out[name]))
    path = os.path.join(ROOT, "decisions", "options", "13-folder.metrics.json")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, indent=1)


if __name__ == "__main__":
    main()
