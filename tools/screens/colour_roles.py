"""The colour-role workshop (decision 15, Q4): which element on which screen takes a module palette colour,
a neutral, a shared state colour, or a colour the user chose. Writes docs/screens/t0/colour-roles.html.

Owner (2026-10-06): the palettes had been applied to elements whose colour the user should choose; decide
per element in a workshop. Fallback for content with no colour of its own: its label's colour, else neutral.

Proposed defaults cite their evidence: the data layer's colour fields (items, labels, activities, trackers,
database options, callouts carry a user colour) and the shared state set. The page embeds the 12 groups
from module_palettes.py, the guided picker's first suggestions (series_contest.py) as sample user colours,
and the state colours; every value is computed there, none is typed here.

    PYTHONUTF8=1 python tools/screens/colour_roles.py
"""
import html
import importlib.util
import itertools
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "docs", "screens", "t0", "colour-roles.html")


def _load(name):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


mp = _load("module_palettes")
sc = _load("series_contest")
pg = mp.pg
THEMES = pg.THEMES

# Sources an element can take. "user" resolves own colour -> label colour -> neutral (owner's fallback).
SOURCES = ["palette primary", "palette secondary", "palette tertiary", "palette container", "palette scale",
           "user", "neutral ink", "neutral dim", "neutral surface", "state done", "state skipped", "state due soon", "state attention"]

# (id, screen, element, proposed source, why). Evidence: the data layer (data/src/commonMain), the state set
# (module-palettes.md), the owner's earlier choices (decision 15).
ELEMENTS = [
    ("hdr", "All screens", "Header stripe", "palette primary", "Says which module you are in; no user content."),
    ("tab", "All screens", "Selected top-row tab", "palette container", "Where-you-are cue."),
    ("cta", "All screens", "Primary action (Save, Confirm)", "palette primary", "One action per screen; not content."),
    ("barico", "All screens", "Bottom-bar icons", "neutral ink", "Owner 2026-10-06: all icons one colour."),
    ("labelchip", "All screens", "Label chips", "user", "Label.color is required in the data layer (label/Label.kt)."),
    ("event", "Calendar", "Events and tasks in Day/Week/Month", "user", "Item.color (item/ItemDao.kt), else its label's, else neutral."),
    ("today", "Calendar", "Today's column", "palette container", "Where-you-are cue in time."),
    ("nowline", "Calendar", "Current-time line", "palette primary", "Where-you-are cue in time."),
    ("tick", "Calendar", "Task done tick", "state done", "Shared state set: done is ink."),
    ("due", "Calendar", "Due soon / still open", "state due soon", "Shared state set: due soon is ink."),
    ("clash", "Calendar", "Clash marker", "state attention", "Shared state set: attention."),
    ("block", "Calendar", "Planner time blocks", "palette scale", "Structure of the day, not content; the module's scale."),
    ("habitid", "Routines", "Habit marker", "user", "A habit shows its label's colour (habits carry labels; ADR 08)."),
    ("log", "Routines", "Log / Open buttons", "palette container", "Repeated actions; the module's container keeps them calm."),
    ("paused", "Routines", "Paused habit", "state skipped", "Shared state set: skipped and paused are dim."),
    ("timer", "Routines", "Running timer", "user", "Activity.color (time/ActivityRepository.kt)."),
    ("lines", "Routines", "Tracker chart lines", "user", "Tracker colour_argb (tracker/TrackerDao.kt) via the guided picker, labelled (series.md)."),
    ("heat", "Routines", "Habit heatmap", "palette scale", "One measure over time; the module's scale (the alternative: the habit's own colour)."),
    ("goal", "Routines", "Goal line", "neutral dim", "A reference, not a series."),
    ("checkprog", "Routines", "Checklist progress", "palette primary", "Progress of the module's own structure."),
    ("mood", "check-in", "Selected mood / energy", "palette container", "The check-in's own answer; no user colour exists."),
    ("ledger", "check-in", "Ledger scale cells", "palette scale", "A scale, owned by the module."),
    ("sensory", "check-in", "Sensory channel chips", "neutral surface", "Five fixed channels; colour would rank them."),
    ("trend", "check-in", "Trend line", "palette primary", "The module's one series."),
    ("trend2", "check-in", "Comparison line", "palette tertiary", "Secondary series of the module."),
    ("burnout", "check-in", "Burnout notice", "state attention", "Triggered state (decision 15): the strongest signal."),
]


def chosen_groups():
    pals, _ = mp.palettes()
    cands = [{"trip": t, "m": m} for t in itertools.product(*(pals[x] for x in mp.MODULES)) for m in [mp.metrics(t)] if mp.feasible(m)]
    mp.rank(cands)
    groups = []
    for i, c in enumerate(mp.select(cands), 1):
        g = {"name": "Group %d: %s" % (i, " · ".join(p["pair"] for p in c["trip"])), "modules": {}}
        for key, p in zip(("cal", "rou", "chk"), c["trip"]):
            g["modules"][key] = {t: {"primary": p["roles"]["primary"]["themes"][t]["accent"], "secondary": p["roles"]["secondary"]["themes"][t]["accent"],
                                     "tertiary": p["roles"]["tertiary"]["themes"][t]["accent"], "container": p["roles"]["primary"]["themes"][t]["container"],
                                     "scale": p["scale"][t]} for t in THEMES}
        groups.append(g)
    return groups


def data():
    user = sc.fixed_list(8)  # the guided picker's first eight suggestions
    return {
        "groups": chosen_groups(),
        "user": {t: [u["light" if t == "light" else "dark"] for u in user] for t in THEMES},
        "ground": {t: pg.GROUND[t] for t in THEMES},
        "states": {t: {"done": pg.GROUND[t]["ink"], "skipped": pg.GROUND[t]["dim"], "due soon": mp.STATES[t].get("due soon", pg.GROUND[t]["ink"]),
                       "attention": mp.STATES[t]["attention"]} for t in THEMES},
        "elements": [dict(zip(("id", "screen", "element", "source", "why"), e)) for e in ELEMENTS],
        "sources": SOURCES,
    }


PAGE = r"""<!doctype html><html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Factotum colour roles</title><style>
*{box-sizing:border-box}body{margin:0;padding:20px 16px 48px;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,sans-serif}
h1{font-size:21px;margin:0 0 4px}h3{font-size:14px;margin:14px 0 6px}p{max-width:95ch}.dim{color:var(--dim)}
.bar1{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:10px 0}select,button{font:inherit;color:var(--ink);background:var(--zone);border:1px solid var(--zone2);border-radius:8px;padding:4px 8px}
button.on{background:var(--ink);color:var(--bg)}
.ws{display:flex;gap:20px;flex-wrap:wrap;align-items:flex-start}.panel{flex:1 1 420px;max-width:560px}
table{border-collapse:collapse;width:100%;font-size:12.5px}td{padding:4px 6px;border-top:1px solid var(--zone2);vertical-align:top}td small{color:var(--dim);display:block}
tr.chg td:first-child{box-shadow:inset 3px 0 0 var(--ink)}
.screens{display:flex;gap:14px;flex-wrap:wrap}
.ph{width:260px;height:520px;border-radius:18px;background:var(--bg);overflow:hidden;display:flex;flex-direction:column;flex:none;box-shadow:0 0 0 1px var(--zone2);font-size:11px}
.hd{height:34px;display:flex;align-items:center;padding:0 10px;font-weight:600;font-size:12px;box-shadow:inset 3px 0 0 var(--c-hdr)}
.bd{flex:1;padding:4px 8px;display:flex;flex-direction:column;gap:6px;overflow:hidden}
.z{background:var(--zone);border-radius:9px;padding:6px 7px}.z h4{margin:0 0 3px;font-size:9px;letter-spacing:.05em;text-transform:uppercase;color:var(--dim)}
.row{display:flex;align-items:center;gap:6px;padding:3px 0}.row .t{flex:1}
.pill{border-radius:999px;padding:1px 8px;font-size:10px}
.tabs{display:flex;gap:4px}.tabs span{padding:2px 8px;border-radius:999px;font-size:10px;color:var(--dim)}.tabs .on{background:var(--c-tab);color:var(--ink)}
.wk{display:grid;grid-template-columns:repeat(5,1fr);gap:3px}.wk>div{background:var(--zone);border-radius:6px;min-height:170px;padding:3px;display:flex;flex-direction:column;gap:3px;position:relative}
.wk>div.today{background:var(--c-today)}.wk small{font-size:9px;color:var(--dim);text-align:center}
.ev{border-radius:4px;padding:2px 3px;font-size:8.5px;line-height:1.2;background:color-mix(in oklch,var(--u) 22%,var(--zone));box-shadow:inset 2px 0 0 var(--u)}
.now{position:absolute;left:0;right:0;top:70px;height:1.5px;background:var(--c-nowline)}
.blk{display:grid;grid-template-columns:repeat(5,1fr);gap:2px}.blk i{height:14px;border-radius:3px}
.lab{border-radius:999px;padding:0 6px;font-size:9px;background:color-mix(in oklch,var(--u) 25%,var(--zone));box-shadow:inset 0 0 0 1px var(--u)}
.dot{width:8px;height:8px;border-radius:50%;background:var(--u)}
.heat{display:grid;grid-template-columns:repeat(7,1fr);gap:2px}.heat i{height:11px;border-radius:2px}
.btm{height:40px;display:flex;background:var(--zone2)}.btm div{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:8.5px;color:var(--dim)}
.btm i{font-style:normal;font-size:11px;color:var(--c-barico)}.btm .on{color:var(--ink);font-weight:600}
textarea{width:100%;min-height:140px;font:12px ui-monospace,monospace;background:var(--zone);color:var(--ink);border:1px solid var(--zone2);border-radius:8px;padding:8px}
</style></head><body>
<h1>Colour roles: palette, neutral, state or yours</h1>
<p class="dim">Each element takes one source. <b>user</b> means the colour you chose for that thing: its own colour, else its label's, else neutral (your fallback rule).
The samples show all three cases: <i>Dentist</i> has its own colour, <i>Bank</i> only a label colour, <i>Bins</i> neither.
Sample user colours are the guided picker's first suggestions. Rows you change are marked; copy the summary when done.</p>
<div class="bar1">Palette group <select id="grp"></select>
<button data-t="light" class="on">Light</button><button data-t="dark">Dark</button><button data-t="oled">OLED</button></div>
<div class="ws"><div class="panel"><table id="tbl"></table><h3>Your choices</h3><textarea id="sum" readonly></textarea><p><button id="copy">Copy</button> <span id="ok" class="dim"></span></p></div>
<div class="screens" id="screens"></div></div>
<script>
const D = __DATA__;
let theme = "light", grp = 0;
const choice = Object.fromEntries(D.elements.map(e => [e.id, e.source]));
try { const s = JSON.parse(localStorage.getItem("factotum-colour-roles")); if (s) Object.assign(choice, s); } catch (e) {}
const MOD = {"Calendar": "cal", "Routines": "rou", "check-in": "chk"};
// A sample thing's user colour: own, else label, else null (neutral).
function userOf(own, label) { const u = D.user[theme]; return own != null ? u[own] : label != null ? u[label] : null; }
function resolve(id, mod, own, label) {
  const src = choice[id], g = D.ground[theme], p = D.groups[grp].modules[mod][theme], st = D.states[theme];
  if (src === "user") return userOf(own, label) || g.dim;
  if (src.startsWith("palette")) { const r = src.split(" ")[1]; return r === "scale" ? p.scale[3] : p[r]; }
  if (src === "neutral ink") return g.ink; if (src === "neutral dim") return g.dim; if (src === "neutral surface") return g.zone2;
  return st[src.replace("state ", "")];
}
function scaleOf(id, mod, k, own) {  // 0..4 ramp: the palette scale, or the user colour mixed into the card
  const src = choice[id], p = D.groups[grp].modules[mod][theme], g = D.ground[theme];
  if (src === "palette scale") return p.scale[k];
  const c = resolve(id, mod, own, null);
  return `color-mix(in oklch, ${c} ${[8, 30, 50, 75, 100][k]}%, ${g.zone})`;
}
const BTM = on => `<div class="btm">${[["◷","Today"],["▦","Week"],["✱","Hub"],["↻","Routines"],["☰","Pages"]].map(([i,l])=>`<div class="${l===on?"on":""}"><i>${i}</i>${l}</div>`).join("")}</div>`;
function screens() {
  const ev = (t, own, label, extra="") => `<span class="ev" style="--u:${resolve("event","cal",own,label)}">${t}${extra}</span>`;
  const cal = `<div class="ph" style="--c-hdr:${resolve("hdr","cal")};--c-tab:${resolve("tab","cal")};--c-today:${resolve("today","cal")};--c-nowline:${resolve("nowline","cal")};--c-barico:${resolve("barico","cal")}">
   <div class="hd">Week · 5–11 Oct</div><div class="bd"><div class="tabs"><span>Day</span><span class="on">Week</span><span>Month</span><span>Planner</span></div>
   <div class="wk"><div class="today"><small>Mon</small>${ev("09:00 Dentist",0,null)}${ev("15:00 Bank",null,1)}<span class="now"></span></div>
   <div><small>Tue</small>${ev("Bins",null,null)}</div><div><small>Wed</small>${ev("10:00 Call",2,null)}</div>
   <div><small>Thu</small>${ev("Gym",null,3)}<span class="ev" style="--u:${resolve("due","cal")};background:transparent;box-shadow:inset 0 0 0 1px var(--u);color:var(--u)">Due: form</span></div>
   <div><small>Fri</small>${ev("Trip",null,1)}<span class="row"><span style="color:${resolve("tick","cal")}">✓</span><span class="t" style="color:var(--dim)">Order ink</span></span></div></div>
   <div class="z"><h4>Planner · time blocks</h4><div class="blk">${[0,1,2,3,4].map(k=>`<i style="background:${scaleOf("block","cal",k,4)}"></i>`).join("")}</div>
   <div class="row"><span style="color:${resolve("clash","cal")}">●</span><span class="t">Clash: Gym and Call</span><span class="pill" style="background:${resolve("cta","cal")};color:var(--bg)">Confirm</span></div>
   <div class="row"><span class="lab" style="--u:${resolve("labelchip","cal",null,1)}">work</span><span class="lab" style="--u:${resolve("labelchip","cal",null,3)}">health</span></div></div></div>${BTM("Week")}</div>`;
  const rou = `<div class="ph" style="--c-hdr:${resolve("hdr","rou")};--c-tab:${resolve("tab","rou")};--c-barico:${resolve("barico","rou")}">
   <div class="hd">Routines</div><div class="bd"><div class="tabs"><span class="on">Habits</span><span>Trackers</span><span>Charts</span></div>
   <div class="row"><span class="pill" style="background:color-mix(in oklch,${resolve("timer","rou",5,null)} 25%,var(--zone));box-shadow:inset 0 0 0 1px ${resolve("timer","rou",5,null)}">● Reading · 0:24 Stop</span></div>
   <div class="z"><h4>Due today</h4>${[["Walk",null,3],["Water · 3 of 8",6,null],["Stretch",null,null],["Read · paused","p",null]].map(([n,o,l])=>{
      const paused = o==="p"; const mk = paused ? resolve("paused","rou") : resolve("habitid","rou",o,l);
      return `<div class="row"><span class="dot" style="--u:${mk}"></span><span class="t" style="${paused?`color:${mk}`:""}">${n}</span><span class="pill" style="background:${paused?"var(--zone2)":resolve("log","rou")}">${paused?"–":"Log"}</span></div>`}).join("")}
   <div class="row"><span class="t">Morning routine 3/5</span><span style="width:60px;height:5px;border-radius:3px;background:var(--zone2);overflow:hidden"><i style="display:block;width:60%;height:100%;background:${resolve("checkprog","rou")}"></i></span></div></div>
   <div class="z"><h4>Trackers</h4><svg viewBox="0 0 130 52" width="100%" height="60">${[["Sleep",0,"M0,26 L20,22 L40,26 L60,16 L80,14 L100,6"],["Energy",1,"M0,40 L20,36 L40,44 L60,34 L80,36 L100,40"],["Water",2,"M0,30 L20,32 L40,24 L60,26 L80,24 L100,23"]].map(([n,k,d],i)=>{
      const c = choice.lines==="user" ? D.user[theme][k] : resolve("lines","rou"); return `<path d="${d}" fill="none" stroke="${c}" stroke-width="1.6"/><text x="103" y="${d.split(",").pop()}" font-size="6.5" fill="${c}">${n}</text>`}).join("")}
     <path d="M0,20 L100,20" stroke="${resolve("goal","rou")}" stroke-dasharray="3 2" stroke-width="1"/></svg></div>
   <div class="z"><h4>Walk · last 4 weeks</h4><div class="heat">${[0,2,3,1,4,4,2,3,0,1,4,3,2,4,1,3,4,2,0,3,4,4,3,2,1,4,3,4].map(v=>`<i style="background:${scaleOf("heat","rou",v,3)}"></i>`).join("")}</div></div></div>${BTM("Routines")}</div>`;
  const chk = `<div class="ph" style="--c-hdr:${resolve("hdr","chk")};--c-barico:${resolve("barico","chk")}">
   <div class="hd">check-in</div><div class="bd"><div class="z"><h4>How are things right now?</h4><div class="row">
   <span class="pill" style="background:${resolve("mood","chk")}">Low energy</span><span class="pill" style="background:var(--zone2)">Calm</span><span class="t"></span>
   <span class="pill" style="background:${resolve("cta","chk")};color:var(--bg)">Save</span></div></div>
   <div class="z"><h4>Ledger · today</h4>${[["Masking",3],["Effort",2],["Recovery",4]].map(([n,v])=>`<div class="row"><span class="t">${n}</span><span style="display:flex;gap:2px">${[1,2,3,4].map(k=>`<i style="width:12px;height:9px;border-radius:2px;background:${k<=v?scaleOf("ledger","chk",k,null):"var(--zone2)"}"></i>`).join("")}</span></div>`).join("")}</div>
   <div class="z"><h4>Sensory</h4><div class="row">${["Sound","Light","Touch","Smell","Taste"].map(n=>`<span class="pill" style="background:${resolve("sensory","chk")}">${n}</span>`).join("")}</div></div>
   <div class="z"><h4>How things have felt</h4><svg viewBox="0 0 130 40" width="100%" height="46"><path d="M0,28 C20,20 30,30 50,22 S80,12 100,18 S120,24 130,20" fill="none" stroke="${resolve("trend","chk")}" stroke-width="1.8"/>
   <path d="M0,32 C25,30 40,34 60,30 S100,26 130,28" fill="none" stroke="${resolve("trend2","chk")}" stroke-width="1.2" stroke-dasharray="3 2"/></svg></div>
   <div class="z" style="box-shadow:inset 3px 0 0 ${resolve("burnout","chk")}"><h4 style="color:${resolve("burnout","chk")}">Notice</h4>Fourteen heavy days in a row. Worth a lighter week?</div></div>${BTM("")}</div>`;
  document.getElementById("screens").innerHTML = cal + rou + chk;
}
function table() {
  let html = "", last = "";
  for (const e of D.elements) {
    if (e.screen !== last) { html += `<tr><td colspan="2"><b>${e.screen}</b></td></tr>`; last = e.screen; }
    html += `<tr class="${choice[e.id]!==e.source?"chg":""}"><td>${e.element}<small>${e.why}</small></td><td><select data-id="${e.id}">${D.sources.map(s=>`<option ${s===choice[e.id]?"selected":""}>${s}</option>`).join("")}</select></td></tr>`;
  }
  document.getElementById("tbl").innerHTML = html;
  document.getElementById("sum").value = "Colour roles\n" + D.elements.map(e => `${e.screen} · ${e.element}: ${choice[e.id]}${choice[e.id]!==e.source?"   (proposed: "+e.source+")":""}`).join("\n");
}
function render() {
  const g = D.ground[theme], r = document.documentElement.style;
  for (const k of ["bg","zone","zone2","ink","dim"]) r.setProperty("--" + k, g[k]);
  table(); screens();
  try { localStorage.setItem("factotum-colour-roles", JSON.stringify(choice)); } catch (e) {}
}
document.getElementById("grp").innerHTML = D.groups.map((g,i)=>`<option value="${i}">${g.name}</option>`).join("");
document.getElementById("grp").onchange = ev => { grp = +ev.target.value; render(); };
document.querySelectorAll("button[data-t]").forEach(b => b.onclick = () => { theme = b.dataset.t; document.querySelectorAll("button[data-t]").forEach(x => x.classList.toggle("on", x === b)); render(); });
document.getElementById("tbl").addEventListener("change", ev => { if (ev.target.dataset.id) { choice[ev.target.dataset.id] = ev.target.value; render(); } });
document.getElementById("copy").onclick = async () => { try { await navigator.clipboard.writeText(document.getElementById("sum").value); document.getElementById("ok").textContent = "Copied."; } catch (e) { document.getElementById("sum").select(); document.getElementById("ok").textContent = "Selected: press Ctrl+C."; } };
if (matchMedia("(prefers-color-scheme: dark)").matches) document.querySelector("button[data-t=dark]").click(); else render();
</script></body></html>"""


def main():
    page = PAGE.replace("__DATA__", json.dumps(data(), ensure_ascii=False))
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(page)
    return OUT


if __name__ == "__main__":
    print(main())
