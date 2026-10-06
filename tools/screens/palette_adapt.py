"""Palette candidates adapted to the mockups' shared ground (owner, 2026-10-06: "keep the original background colour
and adapt the other hues to it with color-optimization-core"; the ground chosen is the workshop's #F4F4F2 / #17181A).
Writes docs/screens/t0/palette-adapted.html and .md.

For every lexicon pair in palette_candidates.CANDIDATES, light and dark:
  1. designkit writes the refine spec: `palette --from <the lexicon pair> --pin surface=<ground> --mode <mode>`.
  2. Three patches, all stated here:
     - the pinned surface gets a width of 0.01 per dimension, because the optimizer portfolio refuses a zero-width
       range (designkit 2.0.6 writes [v, v]); the surface hex does not change;
     - each free role's saturation and lightness envelope is widened to include the lexicon colour (+-10 S, +-15 L),
       because designkit's generic envelopes (primary S 55-80 in light mode) would force muted palettes such as
       Wabi Sabi to become saturated. The swapped ground is recorded as the seed's surface, so the fidelity budget
       does not count the deliberate change of ground as drift. Text keeps designkit's envelope;
     - roles the lexicon pair does not declare are dropped from the fidelity budget (they were seeded from the
       primary only so that the engine has five roles).
  3. optimization-engines' portfolio runs the spec (OPTIMIZATION_ENGINES_HOME must point at its engine).
  4. The winner is evaluated with designkit's own scorer, and every drawn pair is measured with `dk contrast`.
Roles the lexicon pair does not declare (Civic has no secondary or accent) are seeded from its primary so that the
engine has its five roles, and are not shown.

    OPTIMIZATION_ENGINES_HOME=.../optimization-engines/<ver>/engine PYTHONUTF8=1 python tools/screens/palette_adapt.py
"""
import contextlib
import glob
import importlib.util
import io
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.join(ROOT, "tools", "screens")
OUT_HTML = os.path.join(ROOT, "docs", "screens", "t0", "palette-adapted.html")
OUT_MD = os.path.join(ROOT, "docs", "screens", "t0", "palette-adapted.md")
RUNS = os.path.join(ROOT, "_screens-sources", "palette-adapt")
ENGINE = os.path.dirname(sorted(glob.glob(os.path.expanduser(
    "~/.claude/plugins/cache/gold-standard-local/design-optimization/*/engine/designkit_cli.py")))[-1])
DK = os.path.join(ENGINE, "designkit_cli.py")
GROUND = {"light": "#F4F4F2", "dark": "#17181A"}
ROLES = ["primary", "secondary", "accent", "surface", "text"]

spec_ = importlib.util.spec_from_file_location("pc", os.path.join(HERE, "palette_candidates.py"))
pc = importlib.util.module_from_spec(spec_)
spec_.loader.exec_module(pc)

sys.path.insert(0, ENGINE)
from designkit import bridge, cli as dkcli, palette as dkpal  # noqa: E402

# Dark registers whose identity lives in their ground (a role inversion): on a neutral ground the identity colour
# must come back as the primary, so the dark seed starts from the light register's primary.
DARK_FROM_LIGHT_PRIMARY = {"Ming Blue-and-White"}


def dk(*args):
    return subprocess.run(["python", DK, *args], capture_output=True, text=True).stdout


def seed_list(r):
    return ",".join(r.get(k) or r["primary"] for k in ROLES)


def patch(spec, mode, declared):
    seeded = spec["context"]["seeded_from"]
    for role in [r for r in list(seeded) if r not in declared]:
        del seeded[role]  # seeded only to give the engine five roles: not the lexicon's, so not held to fidelity
    for d in spec["dimensions"]:
        role, dim = d["name"].split(".")
        if d.get("pinned"):
            v = d["range"][0]
            d["range"] = [v - 0.005, v + 0.005] if dim != "hue" else [v, v + 0.01]
            continue
        if dim == "hue" or role not in seeded or role in ("surface", "text"):
            continue  # text keeps the mode's envelope, so a seed the mode cannot honour is excluded, not counted
        h, s, l = dkpal.hex_to_hsl(seeded[role])
        x = {"sat": s, "light": l}[dim]
        pad = 10 if dim == "sat" else 15
        lo, hi = d["range"]
        d["range"] = [max(0, min(lo, x - pad)), min(100, max(hi, x + pad))]
    seeded["surface"] = GROUND[mode]
    for sd in spec.get("seeds", []):
        h, s, l = dkpal.hex_to_hsl(GROUND[mode])
        sd["vector"].update({"surface.hue": h, "surface.sat": s, "surface.light": l})
    return spec


def repair(vec, spec):
    """The smallest move that makes the lexicon seed feasible, in the skill's order: lightness first, hue only where a
    constraint is about hue. The portfolio scores every infeasible candidate 0, so a seed that breaks a constraint
    leaves it a flat landscape; this gives it a feasible start. Returns (vector, notes)."""
    v, notes = dict(vec), []
    rep = lambda: dp_report(v, spec)
    if "color.accent_distinct" in rep():
        d = ((v["accent.hue"] - v["primary.hue"] + 540) % 360) - 180
        half = (20.5 - abs(d)) / 2 * (1 if d >= 0 else -1)  # split the move, so neither role drifts alone
        v["accent.hue"], v["primary.hue"] = (v["accent.hue"] + half) % 360, (v["primary.hue"] - half) % 360
        notes.append("primary and accent hues moved %.0f° apart each, to the 20° designkit's accent_distinct asks" % abs(half))
    rng = {d["name"]: d["range"] for d in spec["dimensions"]}

    def closest(name, ok):
        base = v[name]
        lo, hi = rng[name]
        for step in range(0, 181):
            for x in ((base + step / 2, base - step / 2) if step else (base,)):
                if lo <= x <= hi:
                    v[name] = x
                    if ok():
                        return abs(x - base)
        v[name] = base
        return None

    if closest("text.light", lambda: dkpal.body_contrast_ok(v) and dkpal.text_separates_from_surface(v)) is None:
        notes.append("text could not reach its floor by lightness")
    for role in ("primary", "accent"):
        def fill_ok(role=role):
            c, s = dkpal.contrast_pairs(v), dkpal.separation_pairs(v)
            return c.get("on-%s/%s" % (role, role), 99) >= 4.5 and s.get("%s/surface" % role, 99) >= 10
        moved = closest(role + ".light", fill_ok)
        if moved:
            notes.append("%s lightness moved %.1f to carry a label and stand off the ground" % (role, moved))
        elif moved is None:
            notes.append("%s could not be made legible by lightness alone" % role)
    return v, notes


def dp_report(v, spec):
    return dkpal.constraint_report(v, spec)["violated"]


def optimise(tag, seed, mode, declared):
    out = os.path.join(RUNS, tag + "-" + mode)
    os.makedirs(out, exist_ok=True)
    dk("palette", "--from", seed, "--pin", "surface=" + GROUND[mode], "--mode", mode, "-d", out)
    path = os.path.join(out, "spec.json")
    with open(path, encoding="utf-8") as fh:
        spec = patch(json.load(fh), mode, declared)
    fixed, notes = repair(spec["seeds"][0]["vector"], spec)
    spec["seeds"].insert(0, {"name": "repaired", "vector": fixed})
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(spec, fh, indent=1)
    bridge.load_optimizer()  # puts optimization-engines on sys.path
    from optimizer.cli import main as opt_main  # type: ignore
    from optimizer.runner import Run  # type: ignore
    from optimizer.scorers import Registry  # type: ignore
    run_dir = os.path.join(out, "run")
    with contextlib.redirect_stdout(io.StringIO()):
        opt_main(["run", path, "-d", run_dir, "-q", "--scorer-path", bridge.scorer_path()])
    reg = Registry()
    reg.load_path(bridge.scorer_path())
    best = Run.load(run_dir, reg).archive.best
    if best is None:  # the portfolio found nothing feasible: report the repaired seed, and say so
        notes.append("portfolio found no feasible candidate; repaired seed shown")
    res = dkcli._evaluate("palette", best.vector if best else fixed, spec["context"], spec)
    pal = {k: v.upper() for k, v in res["palette"].items()}
    pal["surface"] = GROUND[mode]  # the pin's 0.01 width cannot move the hex; set it exactly
    cons = res.get("constraints") or {}
    return pal, round(res["fitness"], 3), list(cons.get("violated") or []), notes


def ratio(fg, bg):
    out = dk("contrast", fg, bg)
    return float(re.search(r"ratio\s+([\d.]+):1", out).group(1)), float(re.search(r"delta-E 2000\s+([\d.]+)", out).group(1))


def main():
    st = bridge.status()
    if st["mode"] != "portfolio":
        raise SystemExit("optimizer portfolio not reachable (set OPTIMIZATION_ENGINES_HOME): " + st["mode"])
    data, rows = {}, []
    for module, cands in pc.CANDIDATES.items():
        data[module] = []
        for kw, shard, obl, note, pairs in cands:
            ps = []
            for name, light, dark in pairs:
                regs = {}
                for mode in ("light", "dark"):
                    src, started = (light if mode == "light" else dark), None
                    if mode == "dark" and (dark is None or kw in DARK_FROM_LIGHT_PRIMARY):
                        base = dict(dark or light)
                        base["primary"] = light["primary"]
                        started = "no dark register in the lexicon" if dark is None else "started from the light primary (identity lives in the ground)"
                        src = base
                    declared = [k for k in ROLES if k in src]
                    tag = re.sub(r"\W+", "-", "%s-%s-%s" % (module, kw, name.split(" (")[0])).strip("-").lower()
                    # with no dark register in the lexicon there is no dark text to be faithful to: only the hues are held
                    faithful = [k for k in declared if not (dark is None and mode == "dark" and k == "text")]
                    pal, fit, violated, notes = optimise(tag, seed_list(src), mode, faithful)
                    shown = {k: pal[k] for k in declared}
                    t, _ = ratio(shown["text"], shown["surface"])
                    p, sep = ratio(shown["primary"], shown["surface"])
                    drift = {k: round(ratio(src[k], shown[k])[1], 1) for k in declared if k != "surface"}
                    regs[mode] = dict(colors=shown, orig={k: src[k] for k in declared}, text=t, primary=p, sep=sep,
                                      fitness=fit, violated=violated, drift=drift, started=started, notes=notes)
                    rows.append((module, kw, name, mode, shown, t, p, sep, fit, violated, drift, started, notes))
                ps.append(dict(name=name, **regs))
            data[module].append(dict(keyword=kw, shard=shard, oblique=obl, note=note, pairs=ps))
    return data, rows


def write(data, rows):
    out = ["# Palette candidates adapted to the shared ground", "",
           "Generated by `tools/screens/palette_adapt.py`; its docstring states the two spec patches. Ground: light `%s`, dark `%s`. "
           "Every keyword stays a separate candidate. Ratios and drift (CIEDE2000 from the lexicon colour) are measured with designkit." % (GROUND["light"], GROUND["dark"]),
           "", "| Module | Keyword | Pair | Mode | Text | Primary | Primary vs ground (dE) | Largest drift | Fitness | Constraints | Note |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for module, kw, name, mode, shown, t, p, sep, fit, violated, drift, started, notes in rows:
        worst = max(drift.items(), key=lambda kv: kv[1]) if drift else ("", 0)
        out.append("| %s | %s | %s | %s | %.1f | %.1f | %.1f | %s %.1f | %.3f | %s | %s |" % (
            module, kw, name.split(" (")[0], mode, t, p, sep, worst[0], worst[1], fit, ", ".join(violated) or "all met", started or ""))
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out) + "\n")
    with open(OUT_HTML.replace(".html", ".template.html"), encoding="utf-8") as fh:
        page = fh.read()
    with open(OUT_HTML, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(page.replace("/*DATA*/null", json.dumps(data, ensure_ascii=False)))
    return out


if __name__ == "__main__":
    print("\n".join(write(*main())))
