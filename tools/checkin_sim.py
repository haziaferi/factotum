"""Contest 05 (check-in): store each owner's real check-ins in each candidate model, read them
back the way each owner app reads them, and check nothing changed meaning.

    python tools/checkin_sim.py      # writes decisions/options/05-checkin.sim.json + a table

Readers ported from the verified source:
  tendril   level -> label/colour (CheckIns.kt:16-23); one scale per row (CheckIn.kt:14-15)
  equipoise quadrant key energy<0.5, pleasantness<0.5 (DirectionModel.kt:25); LowMoment score
            energy + w*pleasantness over rows with both axes (LowMoment.kt:47, Repositories.kt:63);
            "even grids only" so a discrete value never sits on the 0.5 midline (CheckInShape.kt)

Options
  onto          Tendril's mood maps onto pleasantness, levels to bin centres (k-0.5)/5; energy and
                pleasantness both nullable, CHECK at least one
  onto+levels   onto, plus source_levels (5 for a Tendril-origin row, NULL for continuous) so a
                reader knows a value came from a 5-step scale
  own-axis      mood keeps its own INT column beside energy and pleasantness
  tendril-ints  everything as 1-5 integers
  two-tables    both apps' tables side by side, unmerged
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOOD = {1: "Awful", 2: "Bad", 3: "Okay", 4: "Good", 5: "Great"}
ENERGY = {1: "Drained", 2: "Low", 3: "Steady", 4: "Charged", 5: "Full"}

# real shapes of check-in the two apps write
T_MOOD = {"src": "tendril", "mood": 4}
T_MOOD_OK = {"src": "tendril", "mood": 3}
T_ENERGY = {"src": "tendril", "energy": 2}
E_GRID = {"src": "equipoise", "energy": 0.625, "pleasantness": 0.375}     # GRID4 cell centre
E_PAD = {"src": "equipoise", "energy": 0.81, "pleasantness": 0.62}        # PAD, continuous
E_WIDGET = {"src": "equipoise", "energy": 0.3, "pleasantness": None}      # one-tap energy log


def centre(k):
    return (k - 0.5) / 5


def level(x):
    return min(5, int(x * 5) + 1)


def store(opt, ci):
    """Encode one app-level check-in as the option's row, or None if it cannot be held."""
    if opt in ("onto", "onto+levels"):
        if ci["src"] == "tendril":
            row = {"energy": centre(ci["energy"]) if "energy" in ci else None,
                   "pleasantness": centre(ci["mood"]) if "mood" in ci else None}
            if opt == "onto+levels":
                row["levels"] = 5
            return row
        return {"energy": ci["energy"], "pleasantness": ci["pleasantness"], "levels": None}
    if opt == "own-axis":
        if ci["src"] == "tendril":
            return {"mood": ci.get("mood"), "energy": centre(ci["energy"]) if "energy" in ci else None,
                    "pleasantness": None, "levels": 5 if "energy" in ci else None}
        return {"mood": None, "energy": ci["energy"], "pleasantness": ci["pleasantness"], "levels": None}
    if opt == "tendril-ints":
        if ci["src"] == "tendril":
            return {"mood": ci.get("mood"), "energy": ci.get("energy")}
        return {"mood": level(ci["pleasantness"]) if ci["pleasantness"] is not None else None,
                "energy": level(ci["energy"])}
    if opt == "two-tables":
        return dict(ci, table=ci["src"])
    if opt == "coalesce":   # CONTROL: Equipoise's NOT NULL energy, a missing axis filled with 0.5
        row = store("onto", ci)
        return {k: (0.5 if v is None and k in ("energy", "pleasantness") else v) for k, v in row.items()}
    raise ValueError(opt)


# --- tendril readers ---------------------------------------------------------------------------
def t_mood_label(opt, row):
    if opt in ("onto", "onto+levels", "coalesce"):
        return MOOD[level(row["pleasantness"])] if row["pleasantness"] is not None else None
    if opt in ("own-axis", "tendril-ints", "two-tables"):
        return MOOD.get(row.get("mood"))


def t_energy_label(opt, row):
    e = row.get("energy")
    if e is None:
        return None
    return ENERGY[e] if isinstance(e, int) else ENERGY[level(e)]


# --- equipoise readers -------------------------------------------------------------------------
def engine_rows(opt, rows):
    """Rows Equipoise's engines may read: both axes present, and (where the model can say so)
    not a 5-step value sitting on the midline the engine's even-grid rule keeps empty."""
    out = []
    for r in rows:
        if opt == "two-tables" and r.get("table") != "equipoise":
            continue
        e, p = r.get("energy"), r.get("pleasantness")
        if opt == "tendril-ints":
            e = centre(e) if e else None
            p = centre(r["mood"]) if r.get("mood") else None
        if e is None or p is None:
            continue
        out.append((e, p, r.get("levels")))
    return out


def case_mood_roundtrip(opt):
    return 1 if t_mood_label(opt, store(opt, T_MOOD)) == "Good" else 0


def case_energy_roundtrip(opt):
    return 1 if t_energy_label(opt, store(opt, T_ENERGY)) == "Low" else 0


def case_one_scale(opt):
    """tendril: a mood-only row holds no invented energy, an energy-only row no invented mood."""
    m, e = store(opt, T_MOOD), store(opt, T_ENERGY)
    return 1 if m.get("energy") is None and t_mood_label(opt, e) is None else 0


def case_continuous(opt):
    """equipoise: a PAD value keeps its resolution."""
    r = store(opt, E_PAD)
    return 1 if r.get("energy") == 0.81 and r.get("pleasantness") == 0.62 else 0


def case_widget_null(opt):
    """equipoise: the widget's energy-only row keeps pleasantness absent (not 0.5, not a level)."""
    r = store(opt, E_WIDGET)
    return 1 if r.get("pleasantness") is None and r.get("mood") is None else 0


def case_no_midline(opt):
    """equipoise: no engine input is a discrete value sitting on 0.5 unless the row says it is discrete."""
    rows = [tendril_day(opt, 3, 4), store(opt, E_GRID), store(opt, E_PAD)]     # "Okay" day
    bad = [x for x in engine_rows(opt, rows) if (x[0] == 0.5 or x[1] == 0.5) and x[2] is None]
    return 0 if bad else 1


def tendril_day(opt, mood, energy):
    """Tendril writes one scale per row; the engine pairs a day's latest of each scale."""
    m = store(opt, {"src": "tendril", "mood": mood})
    e = store(opt, {"src": "tendril", "energy": energy})
    if opt in ("onto", "onto+levels", "coalesce"):
        return {"energy": e["energy"], "pleasantness": m["pleasantness"], "levels": m.get("levels")}
    if opt == "tendril-ints":
        return {"energy": e["energy"], "mood": m["mood"]}
    merged = dict(e, pleasantness=None)                              # mood is not an engine axis
    if opt == "two-tables":
        merged["table"] = "tendril"
    return merged


def case_one_history(opt):
    """shared: a Tendril day (mood + energy) and Equipoise rows reach the same engine as one history."""
    return 1 if len(engine_rows(opt, [tendril_day(opt, 4, 4), store(opt, E_PAD)])) == 2 else 0


CASES = {
    "tendril-mood-roundtrip": ("tendril", case_mood_roundtrip),
    "tendril-energy-roundtrip": ("tendril", case_energy_roundtrip),
    "tendril-one-scale-per-row": ("tendril", case_one_scale),
    "equipoise-continuous": ("equipoise", case_continuous),
    "equipoise-widget-energy-only": ("equipoise", case_widget_null),
    "equipoise-no-midline": ("equipoise", case_no_midline),
    "shared-one-history": ("shared", case_one_history),
}
OPTIONS = ["onto", "onto+levels", "own-axis", "tendril-ints", "two-tables", "coalesce"]


def main():
    sim = {o: {cid: fn(o) for cid, (_, fn) in CASES.items()} for o in OPTIONS}
    with open(os.path.join(ROOT, "decisions", "options", "05-checkin.sim.json"), "w",
              encoding="utf-8", newline="") as fh:
        json.dump(sim, fh, indent=1)
    print("%-30s" % "case" + "".join("%-14s" % o for o in OPTIONS))
    for cid in CASES:
        print("%-30s" % cid + "".join("%-14s" % sim[o][cid] for o in OPTIONS))


if __name__ == "__main__":
    main()
