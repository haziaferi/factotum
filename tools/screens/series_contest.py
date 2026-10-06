"""How trackers, habits and activities get their colours (decision 15, Q4). Writes docs/screens/t0/series.md.

Owner (2026-10-06): avoid "the Notion problem" (a short list of colours that inexorably repeats); real life
has more than 8 activities; score fixed series sets against a colour picker such as Chronicle's.

Options
  F3 F4 F6 F8   a fixed list of k colours; an item takes one (Notion-style), so item i gets colour i mod k.
                The lists are the k most separated colours of a readable ring (farthest-point), off the
                reserved state hues and the owner's forbidden hues.
  PICKER        Chronicle as built (core/ui ColorWheelPicker + SwatchColors): 24 HSV seeds 15 degrees apart,
                each new item defaults to the first unused seed; the wheel allows any colour, used as-is in
                both themes.
  GUIDED        the improved picker: identity = hue + chroma + a soft or deep tier; each theme renders it at the lightness that
                reads 3.2:1 (soft) or 6:1 (deep) on that theme's cards; the wheel leaves out reserved and forbidden hues; a new
                item defaults to the free colour farthest from every colour in use.
  GUIDED+LABELS GUIDED, and a chart whose series fall under dE 10 for protanopia or deuteranopia labels its
                lines directly (a second channel), as Okabe & Ito recommend past a few categories.
  GUIDED+LABELS+WARN  and the wheel marks the colours already in use; a pick under dE 10 from one names
                the item that has it. Modelled as a user who re-picks (up to 5 times) when warned.

User models (assumptions, stated): "defaults" accepts the suggested colour; "free" picks at random from
what the picker allows (for F-k, from its list; for PICKER, anywhere on the HSL wheel, saturation 0.3-1,
lightness 0.3-0.7).

Measures per item count N, averaged over trials
  unique     share of items whose colour is >= dE 10 from every other item (the Notion problem)
  charts     share of charts (2, 3, 4 or 6 items drawn at random) readable by protan and deutan viewers:
             every pair >= dE 10 under both, or labelled directly
  readable   share of item colours >= 3:1 on both the light and the dark cards (WCAG 1.4.11)
  clash      share within dE 15 of a reserved state colour, or of a forbidden hue
  taps       extra taps to set a colour (0 when the default is taken, 3 when picking)

    PYTHONUTF8=1 python tools/screens/series_contest.py
"""
import colorsys
import importlib.util
import itertools
import math
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
T0 = os.path.join(ROOT, "docs", "screens", "t0")
spec = importlib.util.spec_from_file_location("pg", os.path.join(HERE, "palette_groups.py"))
pg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pg)
cs = pg.cs

CARD = {"light": pg.GROUND["light"]["zone"], "dark": pg.GROUND["dark"]["zone"]}
# The default state set (states.md): due soon ochre, attention magenta; done and skipped are ink.
RESERVED = {"light": [pg.solve_accent(85, 0.11, "light", 4.5), pg.solve_accent(335, 0.15, "light", 4.5)],
            "dark": [pg.solve_accent(85, 0.11, "dark", 4.5), pg.solve_accent(335, 0.15, "dark", 4.5)]}
NS = (6, 8, 12, 16, 24)
TRIALS = 40
rng = random.Random(7)


def render(h, C, theme, target=3.2):
    """An identity (hue, chroma) drawn for one theme at 3.2:1 on that theme's card."""
    card = CARD[theme]
    dark_side = theme == "light"
    lo, hi = (0.2, 0.8) if dark_side else (0.4, 0.97)
    for _ in range(30):
        mid = (lo + hi) / 2
        r = pg.ratio(pg.oklch_hex(mid, C, h), card)
        if dark_side:
            lo, hi = (mid, hi) if r > target else (lo, mid)
        else:
            lo, hi = (lo, mid) if r > target else (mid, hi)
    return pg.oklch_hex(lo if dark_side else hi, C, h)


def bad(hx_light):
    L, C, h = pg.hex_to_oklch(hx_light)
    cls = pg.hue_class(L, C, h, adapted=True)
    return cls.startswith("forbidden") or any(pg.de(hx_light, r) < 15 for r in RESERVED["light"])


# The guided picker's space: hue every 6 degrees x three chroma levels x two lightness tiers, rendered per
# theme, minus bad ones. Two tiers, because equal lightness collapses for colour-blind viewers.
GUIDED_SPACE = []
for h in range(0, 360, 6):
    for C in (0.06, 0.10, 0.14):
        for tier in (3.2, 6.0):
            item = {"light": render(h, C, "light", tier), "dark": render(h, C, "dark", tier)}
            if not bad(item["light"]):
                GUIDED_SPACE.append(item)


def farthest(space, used, k=None):
    """Greedy farthest-point: the colour in `space` farthest (min dE, light and dark) from `used`."""
    def gap(c):
        if not used:
            return 1e9
        return min(min(pg.de(c["light"], u["light"]), pg.de(c["dark"], u["dark"])) for u in used)
    return max(space, key=gap)


def fixed_list(k):
    chosen = []
    for _ in range(k):
        chosen.append(farthest(GUIDED_SPACE, chosen))
    return chosen


CHRONICLE_SEEDS = []
for i in range(24):
    r, g, b = colorsys.hsv_to_rgb(i * 15 / 360, 0.55, 0.82)
    hx = cs.to_hex([r * 255, g * 255, b * 255])
    CHRONICLE_SEEDS.append({"light": hx, "dark": hx})


def assign(option, n, model, warn=False):
    items = []
    if option.startswith("F"):
        lst = fixed_list(int(option[1:]))
        for i in range(n):
            items.append(lst[i % len(lst)] if model == "defaults" else rng.choice(lst))
    elif option == "PICKER":
        for i in range(n):
            if model == "defaults":
                items.append(CHRONICLE_SEEDS[i % 24])
            else:
                r, g, b = colorsys.hls_to_rgb(rng.random(), rng.uniform(0.3, 0.7), rng.uniform(0.3, 1.0))
                hx = cs.to_hex([r * 255, g * 255, b * 255])
                items.append({"light": hx, "dark": hx})
    else:
        for i in range(n):
            if model == "defaults":
                items.append(farthest(GUIDED_SPACE, items))
                continue
            pick = rng.choice(GUIDED_SPACE)
            for _ in range(5 if warn else 0):  # the wheel marks colours in use; a heeding user re-picks
                if all(pg.de(pick["light"], u["light"]) >= 10 for u in items):
                    break
                pick = rng.choice(GUIDED_SPACE)
            items.append(pick)
    return items


def measure(items, labels):
    n = len(items)
    unique = sum(all(pg.de(a["light"], b["light"]) >= 10 for j, b in enumerate(items) if j != i) for i, a in enumerate(items)) / n
    readable = sum(all(pg.ratio(a[t], CARD[t]) >= 3.0 for t in CARD) for a in items) / n
    clash = sum(bad(a["light"]) for a in items) / n
    ok = tot = 0
    for m in (2, 3, 4, 6):
        if m > n:
            continue
        for _ in range(12):
            drawn = rng.sample(items, m)
            sep = all(pg.de(cs.simulate_cvd(a[t], kd), cs.simulate_cvd(b[t], kd)) >= 10
                      for a, b in itertools.combinations(drawn, 2) for t in CARD for kd in ("protanopia", "deuteranopia"))
            ok += sep or labels
            tot += 1
    return {"unique": unique, "charts": ok / tot, "readable": readable, "clash": clash}


OPTIONS = ["F3", "F4", "F6", "F8", "PICKER", "GUIDED", "GUIDED+LABELS", "GUIDED+LABELS+WARN"]


def run():
    res = {}
    for opt in OPTIONS:
        for model in ("defaults", "free"):
            for n in NS:
                acc = {"unique": 0, "charts": 0, "readable": 0, "clash": 0}
                trials = 1 if (model == "defaults" and opt != "PICKER") else TRIALS
                for _ in range(trials):
                    items = assign(opt.split("+")[0], n, model, warn=opt.endswith("WARN"))
                    for k, v in measure(items, "LABELS" in opt).items():
                        acc[k] += v / trials
                acc["taps"] = 0 if model == "defaults" else (1 if opt.startswith("F") else 3)
                res[(opt, model, n)] = acc
    return res


def main():
    res = run()
    out = ["# Colours for trackers, habits and activities", "", "Generated by `tools/screens/series_contest.py`; options, user models and measures are in its docstring.",
           "", "Guided picker space: %d colours (hue every 6°, three chromas, two lightness tiers at 3.2:1 and 6:1 on the cards, reserved and forbidden hues removed)." % len(GUIDED_SPACE), ""]
    for model in ("defaults", "free"):
        out += ["## When the user %s" % ("accepts the suggested colour" if model == "defaults" else "picks freely"), "",
                "| Option | " + " | ".join("N=%d unique · charts" % n for n in NS) + " | Readable (N=24) | Clash (N=24) | Taps |",
                "|---|" + "---|" * (len(NS) + 3)]
        for opt in OPTIONS:
            row = [res[(opt, model, n)] for n in NS]
            out.append("| %s | %s | %.0f%% | %.0f%% | %d |" % (opt, " | ".join("%.0f%% · %.0f%%" % (100 * r["unique"], 100 * r["charts"]) for r in row),
                                                              100 * row[-1]["readable"], 100 * row[-1]["clash"], row[-1]["taps"]))
        out.append("")
    with open(os.path.join(T0, "series.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out) + "\n")
    return res, out


if __name__ == "__main__":
    res, out = main()
    print("\n".join(out))
