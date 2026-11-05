"""Apply Portfolio Discovery v2 (docs/discovery-v2/README.md) to the hub template in index.html.

Replaces the Discover tab's chapters (hero → journey) with the v2 template from
docs/discovery-v2/discovery-v2.extract.html and adds the _disc2() view-model method.
Local adaptations:
  - Theme of the week: the third tab is labelled "Theme of the week"; its blurb names this week's
    theme from discovery-themes.json (the hub's existing weekly rotation), so it is never stale.
  - Wording: "Aldar CX Times" (the section's current name).
  - Section links (On this page) follow the new chapters; Benchmark and CX Times are left out in
    the Catalogue edition, where those chapters are hidden.
Idempotent: a template that already has id="sec-reel" is left alone. Usage: python3 tools/apply_discovery_v2.py
"""
import json, re

PATH = "index.html"
EX = open("docs/discovery-v2/discovery-v2.extract.html", encoding="utf-8").read()

a = EX.index("    <!-- CHAPTER 00 · HERO")
b = EX.index("<!-- ===== 2 · Logic")
BLOCK = EX[a:b].rstrip()  # ends with "  </div>\n  </sc-if>"
assert BLOCK.endswith("</sc-if>")
BLOCK = re.sub(r'\bon([A-Z][a-z]+)="', lambda m: "sc-camel-on-" + m.group(1).lower() + '="', BLOCK)
BLOCK = BLOCK.replace("04 &middot; Aldar CX Time<", "04 &middot; Aldar CX Times<")
STORY_GRID_OLD = '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:14px">\n        <sc-for list="{{ disc.d2.tabCards }}"'
STORY_GRID_NEW = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,150px),1fr));gap:14px">\n        <sc-for list="{{ disc.d2.tabCards }}"'
BLOCK = BLOCK.replace(STORY_GRID_OLD, STORY_GRID_NEW)  # five cards share one row

s0 = EX.index("  // Portfolio Discovery v2"); s1 = EX.index("  // called at the end of the existing")
METHOD = EX[s0:s1].rstrip() + "\n\n"
def sub(old, new):
    global METHOD
    assert METHOD.count(old) == 1, old
    METHOD = METHOD.replace(old, new)
sub("const S = this.state, { dall, dreel, didx, dcur, DCOLL, DSTAGES, dActive, ddrillAll, ddLine, ddView, BX, openBench, dOpenColl } = x;",
    "const S = this.state, { dall, dreel, didx, dcur, DCOLL, DSTAGES, dActive, ddrillAll, ddLine, ddView, BX, openBench, dOpenColl, dwelTheme } = x;")
sub("['welcome', 'This week: arrival & welcome — how we greet people across every line in the first ninety seconds. The theme rotates weekly.']",
    "['welcome', 'This week: ' + String((dwelTheme || {}).title || 'arrival & welcome').toLowerCase() + ' \\u2014 ' + String((dwelTheme || {}).blurb || '').replace(/\\.$/, '') + '. The theme rotates weekly.']")
sub("return { label: DCOLL[k].title, n: DCOLL[k].items.length,", "return { label: k === 'welcome' ? 'Theme of the week' : DCOLL[k].title, n: DCOLL[k].items.length,")

CALL = "      disc.d2 = this._disc2(disc, { dall, dreel, didx, dcur, DCOLL, DSTAGES, dActive, ddrillAll, ddLine, ddView, BX, openBench, dOpenColl, dwelTheme });\n"

OLD_START = "    <!-- CHAPTER 01 · ARRIVAL -->"
OLD_END = "\n\n  <!-- DISCOVERY · CURATED COLLECTION OVERLAY -->"
ANCH_OLD = """    if (view === 'discover') return [
      { id: 'sec-showreel', label: 'Showreel' },
      { id: 'sec-stories', label: 'Curated stories' },
      { id: 'sec-collection', label: 'Full collection' },
      { id: 'sec-journey', label: 'The journey' }
    ];"""
ANCH_NEW = """    if (view === 'discover') return [
      { id: 'sec-reel', label: 'Showreel' },
      { id: 'sec-stories', label: 'Curated stories' }
    ].concat(window.__SIG_EDITION === 'cat' ? [] : [{ id: 'sec-bench', label: 'Benchmark' }, { id: 'sec-times', label: 'CX Times' }]).concat([
      { id: 'sec-journey', label: 'The journey' }
    ]);"""

# 01 Showreel: the defining moments only, eight of them (one tick each), opening on the week's
REEL_OLD = "const rest = this._dShuffle(withImg.filter(e => !e.defining), this.state.dSeed + 7); return def.concat(rest); }"
REEL_NEW = "return def.slice(0, 8); } /* v2: eight defining moments; was def + every other experience */"

html = open(PATH, encoding="utf-8").read()
m = re.search(r'(<script type="__bundler/template">\s*)(".*?")(\s*</script>)', html, re.S)
t = json.loads(m.group(2))
if 'id="sec-reel"' in t:
    if STORY_GRID_OLD in t:
        t = t.replace(STORY_GRID_OLD, STORY_GRID_NEW, 1)
        html = html[:m.start(2)] + json.dumps(t).replace("</", "<\\u002F") + html[m.end(2):]
        open(PATH, "w", encoding="utf-8").write(html); print("discovery v2: stories on one row")
    if REEL_OLD in t:
        t = t.replace(REEL_OLD, REEL_NEW, 1)
        html = html[:m.start(2)] + json.dumps(t).replace("</", "<\\u002F") + html[m.end(2):]
        open(PATH, "w", encoding="utf-8").write(html); print("discovery v2: showreel limited to eight defining moments")
    else:
        print("discovery v2: already applied")
else:
    i = t.index(OLD_START); j = t.index(OLD_END, i)
    # the old region ends with the wrapper's "</div>\n  </sc-if>"; the new block brings its own
    assert t[i:j].rstrip().endswith("</sc-if>")
    t = t[:i] + BLOCK + t[j:]
    k = t.index("      disc = Object.assign({}, disc, { reel: dreelVM, rails: drails,")
    e = t.index("\n", t.index("timesPreview: this._timesPreview() });", k)) + 1
    t = t[:e] + CALL + t[e:]
    assert t.count("  _dMeta() {") == 1
    t = t.replace("  _dMeta() {", METHOD + "  _dMeta() {", 1)
    assert t.count(ANCH_OLD) == 1
    t = t.replace(ANCH_OLD, ANCH_NEW, 1)
    assert t.count(REEL_OLD) == 1
    t = t.replace(REEL_OLD, REEL_NEW, 1)
    html = html[:m.start(2)] + json.dumps(t).replace("</", "<\\u002F") + html[m.end(2):]
    open(PATH, "w", encoding="utf-8").write(html)
    print("discovery v2: applied")
