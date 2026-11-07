"""Apply the Benchmark v3 uplift (docs/benchmark-v3/README.md) to the Benchmark Gallery module in index.html.

Replaces the gallery's old Chapter 01 (Newly added procession) and Chapter 02 (Explore band, lenses and the
full collection ledger) with: 01 Showreel (2a), 02 The library (3c Browse by + All benchmarks, 1a cards),
and the 1c quick-detail overlay. The hero is unchanged. Source: docs/benchmark-v3/benchmark-v3.extract.html.

Local adaptations to the extract:
  - Already informs: the experience photo uses the hub's photo maps (HP_IMG, DEV_IMG, EST_IMG, sxPhoto),
    so every line gets a thumbnail.
  - "Adapt in Idea Exchange" is shown only while Idea Exchange is switched on (features.json).
  - Project Plus benchmarks stay hidden while Project Plus is switched off, as elsewhere in the hub.

Idempotent: a module that already has data-bm-reel is left alone. Usage: python3 tools/apply_benchmark_v3.py
"""
import base64, gzip, json, re

PATH = "index.html"
EXTRACT = open("docs/benchmark-v3/benchmark-v3.extract.html", encoding="utf-8").read()

# ---- the template block (01 showreel, 02 library, 1c quick detail) ----
a = EXTRACT.index("  <!-- 01 SHOWREEL")
b = EXTRACT.rindex("  </sc-if>", 0, EXTRACT.index("<script>")) + len("  </sc-if>")
BLOCK = EXTRACT[a:b] + "\n"
ADAPT = '<button onClick="{{ u3.d.onAdapt }}"'
i = BLOCK.index(ADAPT); j = BLOCK.index("</button>", i) + len("</button>")
BLOCK = BLOCK[:i] + '<sc-if value="{{ u3.d.showAdapt }}" hint-placeholder-val="{{ true }}">' + BLOCK[i:j] + "</sc-if>" + BLOCK[j:]

# ---- the _u3 logic method ----
s0 = EXTRACT.index("  // ---- v3 uplift"); s1 = EXTRACT.index("</script>", s0)
METHOD = EXTRACT[s0:s1].rstrip() + "\n\n"
def sub(old, new):
    global METHOD
    assert METHOD.count(old) == 1, old
    METHOD = METHOD.replace(old, new)
sub("const R = (S.line && S.line !== 'all') ? DATA.filter(b => b.line === S.line) : DATA.slice();",
    "const PPOFF = !!(window.__SIG_OFF || {}).projectPlus;\n    const R = ((S.line && S.line !== 'all') ? DATA.filter(b => b.line === S.line) : DATA.slice()).filter(b => !(PPOFF && b.line === 'pp'));")
sub("const e2 = this._expMeta(eid) || {};",
    "const e2 = this._expMeta(eid) || {}; const eimg = e2.sxPhoto || (window.HP_IMG || {})[eid] || (window.DEV_IMG || {})[e2.imageKey] || (window.EST_IMG || {})[eid] || e2.image || '';")
sub("backgroundImage: e2.image ? 'url(\"' + e2.image + '\")'", "backgroundImage: eimg ? 'url(\"' + eimg + '\")'")
sub("hasInf: (x.informed || []).length > 0 };", "hasInf: (x.informed || []).length > 0, showAdapt: !(window.__SIG_OFF || {}).ideaExchange };")

# small refinements after the first application: (old, new)
FOLLOWUPS = [
    # the gallery's section links name the new chapter
    ("label: 'Explore the library'", "label: 'The library'"),
    # the showreel keeps its full size (1860 x 640); it shows only photos that can fill it
    ('<div id="bm-newly" data-bm-reel="1" style="padding:40px 28px 0"><div style="max-width:1280px;margin:0 auto">',
     '<div id="bm-newly" data-bm-reel="1" style="padding:40px 28px 0"><div style="max-width:1860px;margin:0 auto">'),
    ('<div style="position:relative;height:560px;border-radius:20px;overflow:hidden;background:#000;box-shadow:0 30px 80px rgba(0,0,0,.25);container-type:inline-size">',
     '<div style="position:relative;height:640px;border-radius:20px;overflow:hidden;background:#000;box-shadow:0 30px 80px rgba(0,0,0,.25);container-type:inline-size">'),
    ("const reelSet = R.filter(b => b.added).sort((x, y) => String(y.added).localeCompare(String(x.added))).concat(R.filter(b => !b.added && b.feat)).slice(0, 8);",
     "const OKR = window.__BM_REEL_OK, okImg = b => !OKR || OKR.indexOf(b.id) >= 0; // data/benchmark-showreel.json\n    const reelSet = R.filter(b => b.added && okImg(b)).sort((x, y) => String(y.added).localeCompare(String(x.added))).concat(R.filter(b => !b.added && b.feat && okImg(b))).slice(0, 8);"),
    # Browse by: the three cards share the full width of the panel
    ('<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:16px">\n            <sc-for list="{{ u3.ix.p3 }}"',
     '<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px">\n            <sc-for list="{{ u3.ix.p3 }}"'),
    # All benchmarks: the rail is a set of categories to move between, not stacking filters.
    # One click shows that category; clicking it again (or another one) moves on; no filter pills.
    ("const setF = (lk, val) => { const cur = (fs[lk] || []).slice(); const i = cur.indexOf(val); i >= 0 ? cur.splice(i, 1) : cur.push(val); this.setState({ u3Sel: Object.assign({}, fs, { [lk]: cur }) }); };",
     "const setF = (lk, val) => { const on = (fs[lk] || []).indexOf(val) >= 0; this.setState({ u3Sel: on ? {} : { [lk]: [val] } }); };"),
    ("pills, hasPills: pills.length > 0,", "pills, hasPills: false,"),
    # the quick detail clears the hub's sticky top bar
    ("backdrop-filter:blur(5px);display:flex;justify-content:center;overflow-y:auto;padding:40px 20px\"",
     "backdrop-filter:blur(5px);display:flex;justify-content:center;overflow-y:auto;padding:84px 20px 40px\""),
    # Portfolio Discovery's benchmark cards set window.__BM_QUICK: open the quick detail over the
    # library (the new design), not the full feature story. Other links still open the full story.
    ("if (DATA.some(d => d.id === want)) { this._open(want); opened = true;",
     "if (DATA.some(d => d.id === want)) { if (window.__BM_QUICK) { window.__BM_QUICK = null; this.setState({ view: 'gallery', sel: null, u3Open: want }); } else this._open(want); opened = true;"),
    ("if (DATA.some(d => d.id === want0)) { this._open(want0);",
     "if (DATA.some(d => d.id === want0)) { if (window.__BM_QUICK) { window.__BM_QUICK = null; this._pubView('gallery'); this.setState({ view: 'gallery', sel: null, from: null, infOpen: null, u3Open: want0 }); return; } this._open(want0);"),
    # images generated as illustrations (window.SIG_GEN, from data/generated-images.json) carry a label
    ("backgroundPosition: 'center' } }; }),\n        hasInf: (x.informed || []).length > 0, showAdapt",
     "backgroundPosition: 'center' } }; }),\n        isGen: !!(((window.SIG_GEN || {}).benchmarks || {})[x.id]), hasInf: (x.informed || []).length > 0, showAdapt"),
    ('{{ u3.d.industry }}</span><button onClick="{{ u3.close }}"',
     '{{ u3.d.industry }}</span><sc-if value="{{ u3.d.isGen }}" hint-placeholder-val="{{ false }}"><span title="Generated with AI to illustrate the idea; not a photograph of the organisation" style="font-size:10px;font-weight:500;letter-spacing:.06em;color:rgba(255,255,255,.85);background:rgba(0,0,0,.55);border:1px dashed rgba(255,255,255,.35);border-radius:999px;padding:5px 10px;white-space:nowrap">Illustrative image &middot; AI</span></sc-if><button onClick="{{ u3.close }}"'),
]

OLD_START = "  <!-- CHAPTER 01 · NEWLY ADDED · procession -->"
OLD_END = "\n\n\n</div>\n</sc-if>\n\n<!-- ==================== COLLECTION"

html = open(PATH, encoding="utf-8").read()
mm = re.search(r'(<script type="__bundler/manifest">\s*)(\{.*?\})(\s*</script>)', html, re.S)
man = json.loads(mm.group(2))
done = False
for k, e in man.items():
    if "html" not in e.get("mime", ""): continue
    raw = base64.b64decode(e["data"]); z = e.get("compressed")
    s = (gzip.decompress(raw) if z else raw).decode("utf-8")
    if OLD_START not in s and 'data-bm-reel="1"' not in s: continue
    if 'data-bm-reel="1"' in s:
        # follow-ups on an applied module (each applied once, when its old text is still there)
        n0 = s
        for old, new in FOLLOWUPS:
            if old in s: s = s.replace(old, new)  # the old text is gone once applied
        if s == n0:
            print("benchmark v3: already applied"); done = True; break
        b2 = s.encode("utf-8"); b2 = gzip.compress(b2, 9, mtime=0) if z else b2
        e["data"] = base64.b64encode(b2).decode()
        html = html[:mm.start(2)] + json.dumps(man, separators=(",", ":")) + html[mm.end(2):]
        open(PATH, "w", encoding="utf-8").write(html)
        print("benchmark v3: follow-ups applied"); done = True; break
    i = s.index(OLD_START); j = s.index(OLD_END, i)
    s = s[:i] + BLOCK + s[j:]
    assert s.count("  renderVals() {") == 1
    s = s.replace("  renderVals() {", METHOD + "  renderVals() {", 1)
    r = s.index("  renderVals() {"); ret = s.index("\n    return {\n", r)
    s = s[:ret] + "\n    return {\n      u3: this._u3(S, RDY)," + s[ret + len("\n    return {"):]
    for old, new in FOLLOWUPS:
        if old in s: s = s.replace(old, new)  # the old text is gone once applied
    b2 = s.encode("utf-8")
    if z: b2 = gzip.compress(b2, 9, mtime=0)
    e["data"] = base64.b64encode(b2).decode()
    html = html[:mm.start(2)] + json.dumps(man, separators=(",", ":")) + html[mm.end(2):]
    open(PATH, "w", encoding="utf-8").write(html)
    print("benchmark v3: applied to module", k); done = True; break
assert done, "Benchmark Gallery module not found"
