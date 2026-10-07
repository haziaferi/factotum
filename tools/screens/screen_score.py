"""Scores a screen option from its rendered page (decision 15: every screen scored, a control must lose).

Measured, not assumed:
  clutter        edge density of the render (nav_glance.edge_density), mean over light and dark, with the
                 dotted user-data outline hidden
  strong         (strong_nav: in the header, bar or rail only) tappable elements whose effective contrast on the ground is >= 7:1 (opacity included):
                 what the eye lands on first. Fewer = calmer, as long as the main action is among them
  faint          tappable elements whose text reads under 4.5:1 on the ground, opacity included
  small_taps     tappable elements under 48 x 48 dp (Material and WCAG 2.5.8's comfortable size)
  blank_lead     rows whose slot before the title shows nothing (an empty left column)
  title_edges    distinct x positions titles start at, summed over zones (1 per zone is one clean edge)
  rows_visible   item rows wholly inside the phone's content area (how much of the day fits at a glance)
  min_text       the smallest font size of any visible text, in px
  nav            tappable elements in the header, bar and rail
  far_nav        of those, on a phone, the ones centred in the top quarter of the screen (hardest for a thumb)
  steps          for each target, 1 if a tappable element with that name is on the screen, else the
                 option's declared route (counted, and marked as declared)

References: the same clutter measure on real apps' screenshots in _screens-sources/reference (gitignored;
placeholder accounts only), scaled to 360 px wide so the numbers compare.

    from screen_score import score_option, reference_clutter
"""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import tempfile

from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE = os.path.join(ROOT, "_screens-sources", "screen-renders")
REFS = os.path.join(ROOT, "_screens-sources", "reference")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

MEASURE_JS = r"""
<script>
(function(){
  function lum(c){var m=c.match(/[\d.]+/g).map(Number);var a=m.slice(0,3).map(function(v){v/=255;return v<=0.04045?v/12.92:Math.pow((v+0.055)/1.055,2.4)});return {l:0.2126*a[0]+0.7152*a[1]+0.0722*a[2],a:m.length>3?m[3]:1}}
  function op(el){var o=1;for(;el&&el.nodeType===1;el=el.parentElement){o*=parseFloat(getComputedStyle(el).opacity)}return o}
  var bg=lum(getComputedStyle(document.body).backgroundColor).l;
  var out={taps:[],min_text:99,nav:0};
  document.querySelectorAll('[data-tap]').forEach(function(el){
    var r=el.getBoundingClientRect(); if(!r.width||!r.height) return;
    // contrast against the nearest painted background (the button's own fill), not the page's
    var g=el,bgl=bg;for(;g&&g.nodeType===1;g=g.parentElement){var bc=getComputedStyle(g).backgroundColor;var q=lum(bc);if(q.a>0.5){bgl=q.l;break}}
    var c=lum(getComputedStyle(el).color), o=op(el);
    var L=c.l*o+bgl*(1-o); var hi=Math.max(L,bgl)+0.05, lo=Math.min(L,bgl)+0.05;
    out.taps.push({name:el.getAttribute('data-tap'),w:Math.round(r.width),h:Math.round(r.height),x:Math.round(r.left+r.width/2),y:Math.round(r.top+r.height/2),contrast:+(hi/lo).toFixed(2),box:[r.left,r.top,r.width,r.height],seen:(function(){var cx=r.left+r.width/2,cy=r.top+r.height/2;if(cx<0||cy<0||cx>=innerWidth||cy>=innerHeight)return false;var hit=document.elementFromPoint(cx,cy);return !!hit&&(el===hit||el.contains(hit))})(),
                   nav:!!el.closest('.hdr,.bar,.rail')});
  });
  var w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
  while(w.nextNode()){var n=w.currentNode;if(!n.textContent.trim())continue;var p=n.parentElement;var r=p.getBoundingClientRect();
    if(!r.width||!r.height)continue;var fs=parseFloat(getComputedStyle(p).fontSize);if(fs<out.min_text)out.min_text=fs}
  // lead column: a row whose slot before the title shows nothing (no text, no ::before mark, no border) is a blank lead;
  // title edges: how many different x positions titles start at, per zone (1 = one clean left edge)
  out.blank_lead=0;out.title_edges=0;
  function shows(c){if(c.textContent.trim())return true;var b=getComputedStyle(c,'::before').content;if(b&&b!=='none'&&b!=='normal')return true;  // content:"" still draws (the circles)
    var s=getComputedStyle(c);return parseFloat(s.borderLeftWidth)>0||parseFloat(s.borderTopWidth)>0||(s.backgroundColor!=='rgba(0, 0, 0, 0)'&&c.getBoundingClientRect().width>0)}
  document.querySelectorAll('.zone').forEach(function(z){var xs={};z.querySelectorAll('.row').forEach(function(r){var t=r.querySelector('.t');if(!t)return;
    xs[Math.round(t.getBoundingClientRect().left)]=1;var any=false;for(var c=r.firstElementChild;c&&c!==t;c=c.nextElementSibling){if(shows(c)){any=true;break}}
    if(!any)out.blank_lead++});out.title_edges+=Object.keys(xs).length});
  var b=document.querySelector('.body');if(b){var bb=b.getBoundingClientRect();out.rows_visible=0;
    document.querySelectorAll('.body .row').forEach(function(r){var q=r.getBoundingClientRect();if(q.height&&q.top>=bb.top&&q.bottom<=bb.bottom)out.rows_visible++})}
  // capture sheets: the sheet's height and how many lines the typed text wraps to
  var sh=document.querySelector('.sheet');if(sh)out.sheet_h=Math.round(sh.getBoundingClientRect().height);
  // an opaque full-screen capture (.cover) hides everything above the keyboard, not just its line's strip
  var cv=document.querySelector('.cover'),kb=document.querySelector('.cover .kb');if(cv&&kb)out.sheet_h=Math.round(kb.getBoundingClientRect().top-cv.getBoundingClientRect().top);
  var li=document.querySelector('.line .in .ud');if(li){var lh=parseFloat(getComputedStyle(li).lineHeight)||parseFloat(getComputedStyle(li).fontSize)*1.2;out.line_lines=Math.round(li.getBoundingClientRect().height/lh)}
  // element boxes for visual-weight scoring (sheet_weight.py)
  out.boxes={};[['sheet','.sheet'],['line','.line .in'],['linebox','.line'],['chips','.chips'],['route','.route'],['legend','.legend'],['hubsheet','.hubsheet'],['hubpanel','.hubpanel']].forEach(function(p){var el=document.querySelector(p[1]);if(el){var q=el.getBoundingClientRect();out.boxes[p[0]]=[q.left,q.top,q.width,q.height]}});
  // drawn (visual) parts of sheet controls, apart from their 48 px targets: harmony compares these
  out.vis=[].map.call(document.querySelectorAll('.sheet .vis'),function(el){var q=el.getBoundingClientRect();return [el.getAttribute('data-vis')||'',Math.round(q.left),Math.round(q.top),Math.round(q.width),Math.round(q.height)]});
  // is the typed line drawn, or covered by something above it? sampled at its left, middle and right
  var ln=document.querySelector('.line .in');if(ln){var q=ln.getBoundingClientRect(),line=ln.closest('.line');out.line_covered=[0.1,0.5,0.9].some(function(f){var h=document.elementFromPoint(q.left+q.width*f,q.top+q.height/2);return !(h&&line.contains(h))})}
  // legend items (.lgi) actually readable: inside the viewport and drawn at their centre (not scrolled or clipped away)
  out.lgi=[].map.call(document.querySelectorAll('.lgi'),function(el){var q=el.getBoundingClientRect(),cx=q.left+q.width/2,cy=q.top+q.height/2;var ok=q.left>=0&&q.right<=innerWidth&&cy>=0&&cy<innerHeight;var h=ok?document.elementFromPoint(cx,cy):null;return ok&&!!h&&(el===h||el.contains(h))});
  // card headers' boxes (Hub sheet: their visual weight against the feature names)
  out.h5=[].map.call(document.querySelectorAll('.card h5, .card .hlab'),function(el){var q=el.getBoundingClientRect();return [q.left,q.top,q.width,q.height]});
  var pre=document.createElement('pre');pre.id='__measure';pre.textContent=JSON.stringify(out);document.body.appendChild(pre);
})();
</script>"""


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, "tools", "screens", name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(mod)
    return mod


def _edge(args, out_flag, key, doc, w, h):
    os.makedirs(CACHE, exist_ok=True)
    src = os.path.join(CACHE, key + ".html")
    with open(src, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)
    with tempfile.TemporaryDirectory() as prof:
        return subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                               "--window-size=%d,%d" % (w, h), "--user-data-dir=" + prof, "--virtual-time-budget=3000"] + args +
                              ["file:///" + src.replace("\\", "/")], capture_output=True, timeout=120, text=out_flag)


def render(doc, w, h):
    key = hashlib.sha256((doc + "%dx%d" % (w, h)).encode("utf-8")).hexdigest()[:20]
    png = os.path.join(CACHE, key + ".png")
    if not os.path.exists(png):
        _edge(["--screenshot=" + png], False, key, doc, w, h)
    if not os.path.exists(png):
        raise RuntimeError("render failed")
    return png


def measure(doc, w, h):
    key = hashlib.sha256((doc + MEASURE_JS + "m%dx%d" % (w, h)).encode("utf-8")).hexdigest()[:20]  # the script is part of the key
    cached = os.path.join(CACHE, key + ".json")
    if os.path.exists(cached):
        return json.load(open(cached, encoding="utf-8"))
    res = _edge(["--dump-dom"], True, key, doc.replace("</body>", MEASURE_JS + "</body>"), w, h)
    m = re.search(r'<pre id="__measure">(.*?)</pre>', res.stdout, re.S)
    if not m:
        raise RuntimeError("measure failed: " + res.stderr[-400:])
    data = json.loads(m.group(1).replace("&quot;", '"').replace("&amp;", "&"))
    json.dump(data, open(cached, "w", encoding="utf-8"))
    return data


def edge_density(png, threshold=40):
    im = Image.open(png).convert("L").filter(ImageFilter.FIND_EDGES)
    hist = im.histogram()
    return sum(hist[threshold:]) / float(im.size[0] * im.size[1])


def score_option(make_doc, w, h, targets=None, declared=None):
    """make_doc(theme, score) -> full HTML document. targets: names whose steps to report; declared: {name: steps}
    for targets not on this screen."""
    clutter = sum(edge_density(render(make_doc(t, True), w, h)) for t in ("light", "dark")) / 2
    m = measure(make_doc("light", True), w, h)
    names = {t["name"] for t in m["taps"]}
    steps = {}
    for t in targets or []:
        steps[t] = (1, "on screen") if t in names else ((declared or {}).get(t), "declared")
    return {"clutter": round(clutter, 4), "strong": sum(t["contrast"] >= 7 for t in m["taps"]),
            "strong_nav": sum(t["contrast"] >= 7 and t["nav"] for t in m["taps"]),
            # labelled targets read below 4.5:1 (WCAG 1.4.3), opacity included: receding must not mean unreadable
            "faint": sorted({"%s %.1f" % (t["name"], t["contrast"]) for t in m["taps"] if t["contrast"] < 4.5}),
            # header/bar/rail targets in the top quarter of a phone: the zone a thumb reaches worst (Hoober 2013)
            "far_nav": sum(t["nav"] and t["y"] < h * 0.25 for t in m["taps"]) if w < 600 else 0,
            "small_taps": sorted({"%s %dx%d" % (t["name"], t["w"], t["h"]) for t in m["taps"] if t["w"] < 48 or t["h"] < 48}),
            "taps_raw": m["taps"],
            "min_text": m["min_text"], "sheet_h": m.get("sheet_h"), "boxes": m.get("boxes", {}), "vis": m.get("vis", []), "line_covered": m.get("line_covered", False), "lgi": m.get("lgi", []), "h5": m.get("h5", []), "line_lines": m.get("line_lines"), "rows_visible": m.get("rows_visible", 0), "blank_lead": m.get("blank_lead", 0), "title_edges": m.get("title_edges", 0), "nav": sum(t["nav"] for t in m["taps"]), "steps": steps}


def reference_clutter(names):
    """Edge density of reference screenshots (paths under _screens-sources/reference), scaled to 360 px wide."""
    out = {}
    for rel in names:
        p = os.path.join(REFS, rel)
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGB")
        im = im.resize((360, round(im.size[1] * 360 / im.size[0])))
        tmp = os.path.join(CACHE, "ref-" + hashlib.sha256(rel.encode()).hexdigest()[:12] + ".png")
        os.makedirs(CACHE, exist_ok=True)
        im.save(tmp)
        out[rel] = round(edge_density(tmp), 4)
    return out


# Differences smaller than these are noise, not design: the same page renders a few edge pixels differently
# with a moved element of equal weight. A front decided by a thousandth of clutter says nothing.
TOLERANCE = {"clutter": 0.002, "desk_clutter": 0.002}


def front(rows, low=("clutter", "strong", "small", "min_text_short", "steps_sum")):
    """Indices of options no other option beats on every measure (beyond TOLERANCE)."""
    def better(a, b, k):
        return a[k] < b[k] - TOLERANCE.get(k, 0)

    def dom(a, b):
        return all(not better(b, a, k) for k in low) and any(better(a, b, k) for k in low)
    return [i for i, r in enumerate(rows) if not any(dom(o, r) for j, o in enumerate(rows) if j != i)]
