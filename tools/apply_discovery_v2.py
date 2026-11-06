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

# 02 Curated stories: five tabs. Two added after the v2 handoff (Group CX, 6 Nov 2026):
#   Recently added: newest to the hub, dated by the Submit & review approval, or else the first
#     entry in the experience's dated history (no line records an "added" date of its own).
#   Customer stories: the Customer Stories records (CS_DATA, hidden ones left out); cards open
#     the Customer Stories tab.
TABS2 = [
    ("pillar: p ? (p.short || p.name || p.label || '') : (e.pillar || ''), status: e.status || 'impl', defining: !!e.defining });",
     "pillar: p ? (p.short || p.name || p.label || '') : (e.pillar || ''), status: e.status || 'impl', defining: !!e.defining, added: this._dAdded(e) });"),
    ("  _dSig() {",
     "  // when an experience joined the hub: its Submit & review approval, else its first dated history entry\n"
     "  _dAdded(e) { if (e.sx && e.sx.approved_at) { const t = Date.parse(e.sx.approved_at); if (!isNaN(t)) return t; } let m = 0; (e.log || []).forEach(l => { const t = Date.parse(l && l.when); if (!isNaN(t) && (!m || t < m)) m = t; }); return m; }\n"
     "  _dSig() {"),
    ("welcome: { title: dwelTheme.title, accent: dwelTheme.accent, items: dwel } };",
     "welcome: { title: dwelTheme.title, accent: dwelTheme.accent, items: dwel }, added: { title: 'Recently added', accent: '#5A82B5', items: dall.filter(e => e.image && e.added).sort((a, b) => b.added - a.added || String(a.name).localeCompare(String(b.name))).slice(0, 24) } };"),
    ("Three ways into the portfolio", "Five ways into the portfolio"),
    ("const TABS = [['defining',",
     "const CSA = ((window.CS_DATA && window.CS_DATA.stories) || []).filter(x => x && !x.hidden);\n"
     "    const CSL = { Development: '#C9A24A', Estates: '#A5443A', Hospitality: '#D08A4C', Retail: '#D9786A', Education: '#5A82B5', Corporate: '#4FB58C' };\n"
     "    const CSG = { Development: '#5A4A22', Estates: '#5E2A24', Hospitality: '#5E3F22', Retail: '#5B3330', Education: '#2E4160', Corporate: '#24473A' };\n"
     "    const goStories = () => this.go('stories');\n"
     "    const storyCards = CSA.filter(x => x.photo).concat(CSA.filter(x => !x.photo)).slice(0, 5).map(x => ({ id: x.id, name: x.title, essence: x.memorable, line: x.line, defining: false, notDef: true, isExp: false, dot: dot(CSL[x.line] || '#E8B96A'), img: Object.assign(img(x.photo, CSG[x.line] || '#24473A'), x.photo_position ? { backgroundPosition: x.photo_position } : {}), open: goStories }));\n"
     "    const TABS = [['defining',"),
    ("['welcome', 'This week: '",
     "['added', 'The newest experiences to join the hub, from Submit & review and the business lines\\u2019 latest records.'], ['stories', 'Moments told by the colleagues who made them, each an expression of a Signature Experience in the field.'], ['welcome', 'This week: '"),
    ("const tk = S.dTab && DCOLL[S.dTab] ? S.dTab : 'defining';",
     "const tk = S.dTab && (DCOLL[S.dTab] || S.dTab === 'stories') ? S.dTab : 'defining'; const isSt = tk === 'stories';\n"
     "    const TORD = ['defining', 'live', 'added', 'welcome', 'stories']; TABS.sort((p, q) => TORD.indexOf(p[0]) - TORD.indexOf(q[0]));"),
    ("d2.tabs = TABS.map(([k]) => { const on = k === tk; return { label: k === 'welcome' ? 'Theme of the week' : DCOLL[k].title, n: DCOLL[k].items.length,",
     "d2.tabs = TABS.map(([k]) => { const on = k === tk; return { label: k === 'welcome' ? 'Theme of the week' : k === 'stories' ? 'Customer stories' : DCOLL[k].title, n: k === 'stories' ? CSA.length : DCOLL[k].items.length,"),
    ("d2.tabSeeAllLabel = 'See all ' + DCOLL[tk].items.length + ' \\u2192';", "d2.tabSeeAllLabel = 'See all ' + (isSt ? CSA.length : DCOLL[tk].items.length) + ' \\u2192';"),
    ("d2.tabSeeAll = dOpenColl(tk);", "d2.tabSeeAll = isSt ? goStories : dOpenColl(tk);"),
    ("d2.tabCards = DCOLL[tk].items.slice(0, 5).map(card);", "d2.tabCards = isSt ? storyCards : DCOLL[tk].items.slice(0, 5).map(e => Object.assign(card(e), { isExp: true }));"),
    # cards open the experience's full detail view (the dark 3a design) directly; the old light
    # preview popup (it still mentioned RAG status) is no longer used
    ("  _dOpen(id) { return (ev) => { if (ev && ev.stopPropagation) ev.stopPropagation(); this.setState({ dPeekId: id }); }; }",
     "  _dOpen(id) { return (ev) => { if (ev && ev.stopPropagation) ev.stopPropagation(); this.setState({ dPeekId: null, dColKey: null }); this.openExp(id); }; }"),
    # story cards carry no Compare / Save
    ('<div style="display:flex;gap:6px"><button sc-camel-on-click="{{ c.onCmp }}" style="{{ c.cmpCss }}">{{ c.cmpLabel }}</button><button sc-camel-on-click="{{ c.onSave }}" style="{{ c.saveCss }}">{{ c.saveLabel }}</button></div><span style="font-size:11px;font-weight:500;color:#E8B96A;white-space:nowrap">Open &#8594;</span>',
     '<sc-if value="{{ c.isExp }}" hint-placeholder-val="{{ true }}"><div style="display:flex;gap:6px"><button sc-camel-on-click="{{ c.onCmp }}" style="{{ c.cmpCss }}">{{ c.cmpLabel }}</button><button sc-camel-on-click="{{ c.onSave }}" style="{{ c.saveCss }}">{{ c.saveLabel }}</button></div></sc-if><span style="font-size:11px;font-weight:500;color:#E8B96A;white-space:nowrap;margin-left:auto">Open &#8594;</span>'),
]

# 01 Showreel: the defining moments only, eight of them (one tick each), opening on the week's
REEL_OLD = "const rest = this._dShuffle(withImg.filter(e => !e.defining), this.state.dSeed + 7); return def.concat(rest); }"
REEL_NEW = "return def.slice(0, 8); } /* v2: eight defining moments; was def + every other experience */"

html = open(PATH, encoding="utf-8").read()
m = re.search(r'(<script type="__bundler/template">\s*)(".*?")(\s*</script>)', html, re.S)
t = json.loads(m.group(2))
if 'id="sec-reel"' in t:
    n0 = t
    for old, new in TABS2:
        if new not in t:
            assert t.count(old) == 1, old[:70]
            t = t.replace(old, new, 1)
    if t != n0:
        html = html[:m.start(2)] + json.dumps(t).replace("</", "<\\u002F") + html[m.end(2):]
        open(PATH, "w", encoding="utf-8").write(html); print("discovery v2: five curated-stories tabs")
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
    for old, new in TABS2:
        assert t.count(old) == 1, old[:70]
        t = t.replace(old, new, 1)
    html = html[:m.start(2)] + json.dumps(t).replace("</", "<\\u002F") + html[m.end(2):]
    open(PATH, "w", encoding="utf-8").write(html)
    print("discovery v2: applied")
