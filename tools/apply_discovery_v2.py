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

# 02 Curated stories, See all (Group CX chose option A, 6 Nov 2026): the full collection opens in place,
# inside the panel, with line chips, a count, Cards / List and Show 15 more. It replaces the old light
# collection overlay, which nothing opens any more. Customer stories' See all still opens its tab.
CHIPCSS = "{ display: 'inline-flex', alignItems: 'center', gap: '7px', fontFamily: 'inherit', fontSize: '11.5px', fontWeight: 500, padding: '6px 12px', borderRadius: '999px', cursor: 'pointer', whiteSpace: 'nowrap', border: '1px solid ' + (on ? '#E8B96A' : 'rgba(255,255,255,.14)'), background: on ? 'rgba(232,185,106,.15)' : 'transparent', color: on ? '#F6F3EC' : 'rgba(255,255,255,.7)' }"
VIEWCSS = "{ fontFamily: 'inherit', fontSize: '11px', fontWeight: 600, cursor: 'pointer', padding: '5px 12px', borderRadius: '7px', border: 0, background: on ? '#E8B96A' : 'transparent', color: on ? '#0A1014' : 'rgba(255,255,255,.7)' }"
LOGIC = ("const exp = !isSt && !!S.dExp, lmapE = this._dLineMap(), allIt = isSt ? [] : DCOLL[tk].items, eLine = S.dExpLine || null;\n"
"    const fl = eLine ? allIt.filter(e => e.line === eLine) : allIt, eN = S.dExpN || 15, eView = S.dExpView || 'cards';\n"
"    d2.exp = exp; d2.showCards = !exp || eView === 'cards'; d2.showList = exp && eView === 'list';\n"
"    d2.tabSeeAllLabel = exp ? 'Show fewer \\u2191' : 'See all ' + (isSt ? CSA.length : allIt.length) + ' \\u2192';\n"
"    d2.tabSeeAll = isSt ? goStories : () => this.setState({ dExp: !exp, dExpLine: null, dExpN: 15 });\n"
"    const shown = exp ? fl.slice(0, eN) : allIt.slice(0, 5);\n"
"    d2.tabCards = isSt ? storyCards : (d2.showCards ? shown.map(e => Object.assign(card(e), { isExp: true })) : []);\n"
"    d2.expRows = d2.showList ? shown.map(card) : [];\n"
"    d2.gridCss = { display: 'grid', gridTemplateColumns: exp ? 'repeat(auto-fill,minmax(min(100%,190px),1fr))' : 'repeat(auto-fit,minmax(min(100%,150px),1fr))', gap: '14px' };\n"
"    const lnames = []; allIt.forEach(e => { if (lnames.indexOf(e.line) < 0) lnames.push(e.line); }); lnames.sort();\n"
"    const echip = (label, val, color) => { const on = eLine === val; return { label, dot: dot(color), onClick: () => this.setState({ dExpLine: val, dExpN: 15 }), css: " + CHIPCSS + " }; };\n"
"    d2.expChips = [echip('All lines', null, '#E8B96A')].concat(lnames.map(n => echip(n, n, lmapE[n] || '#C9A15A')));\n"
"    d2.expCount = fl.length + (fl.length === 1 ? ' experience' : ' experiences');\n"
"    d2.expViews = [['cards', 'Cards'], ['list', 'List']].map(([v, l]) => { const on = eView === v; return { label: l, onClick: () => this.setState({ dExpView: v }), css: " + VIEWCSS + " }; });\n"
"    d2.hasMore = exp && fl.length > eN; d2.moreLabel = 'Show ' + Math.min(15, fl.length - eN) + ' more \\u00b7 ' + (fl.length - eN) + ' left'; d2.more = () => this.setState({ dExpN: eN + 15 });")
FILTER = ('<sc-if value="{{ disc.d2.exp }}" hint-placeholder-val="{{ false }}"><div data-d2-filter="1" style="display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;padding:14px 0;border-top:1px solid rgba(255,255,255,.08);border-bottom:1px solid rgba(255,255,255,.08)">'
  '<div style="display:flex;gap:8px;flex-wrap:wrap"><sc-for list="{{ disc.d2.expChips }}" as="ch" hint-placeholder-count="7"><button sc-camel-on-click="{{ ch.onClick }}" style="{{ ch.css }}"><span style="{{ ch.dot }}"></span>{{ ch.label }}</button></sc-for></div>'
  '<div style="display:flex;align-items:center;gap:14px"><span style="font-size:12px;color:rgba(255,255,255,.55);white-space:nowrap">{{ disc.d2.expCount }}</span><div style="display:flex;gap:3px;background:rgba(255,255,255,.08);border-radius:9px;padding:3px"><sc-for list="{{ disc.d2.expViews }}" as="v" hint-placeholder-count="2"><button sc-camel-on-click="{{ v.onClick }}" style="{{ v.css }}">{{ v.label }}</button></sc-for></div></div></div></sc-if>\n      ')
LIST = ('\n      <sc-if value="{{ disc.d2.showList }}" hint-placeholder-val="{{ false }}"><div style="display:flex;flex-direction:column"><sc-for list="{{ disc.d2.expRows }}" as="r" hint-placeholder-count="8">'
  '<div data-d2-row="1" sc-camel-on-click="{{ r.open }}" style="display:grid;grid-template-columns:64px minmax(0,1fr) auto;gap:16px;align-items:center;padding:12px 8px;border-top:1px solid rgba(255,255,255,.08);cursor:pointer" style-hover="background:rgba(255,255,255,.04)">'
  '<div style="position:relative;width:64px;height:64px;border-radius:8px;overflow:hidden;background:#111"><div style="{{ r.img }}"></div></div>'
  '<div style="min-width:0"><div style="display:flex;gap:12px;align-items:center"><span style="display:inline-flex;align-items:center;gap:6px;font-size:10px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:rgba(255,255,255,.6)"><span style="{{ r.dot }}"></span>{{ r.line }}</span><sc-if value="{{ r.defining }}" hint-placeholder-val="{{ false }}"><span style="font-size:9.5px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:#E8B96A">&#10022; Defining</span></sc-if></div>'
  '<div style="font-size:17px;font-weight:300;margin-top:4px;color:#F6F3EC;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ r.name }}</div><div style="font-size:12px;color:rgba(255,255,255,.55);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ r.essence }}</div></div>'
  '<div data-d2-acts="1" style="display:flex;gap:6px;align-items:center"><button sc-camel-on-click="{{ r.onCmp }}" style="{{ r.cmpCss }}">{{ r.cmpLabel }}</button><button sc-camel-on-click="{{ r.onSave }}" style="{{ r.saveCss }}">{{ r.saveLabel }}</button><span style="color:#E8B96A;margin-left:6px">&#8594;</span></div></div></sc-for></div></sc-if>'
  '\n      <sc-if value="{{ disc.d2.hasMore }}" hint-placeholder-val="{{ false }}"><div style="display:flex;justify-content:center"><button sc-camel-on-click="{{ disc.d2.more }}" style="font-family:inherit;font-size:12px;border:1px solid rgba(232,185,106,.5);background:transparent;color:#E8B96A;border-radius:999px;padding:10px 22px;cursor:pointer" style-hover="background:rgba(232,185,106,.15)">{{ disc.d2.moreLabel }}</button></div></sc-if>')
GRID_OLD = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,150px),1fr));gap:14px">\n        <sc-for list="{{ disc.d2.tabCards }}"'
GRID_NEW = FILTER + '<sc-if value="{{ disc.d2.showCards }}" hint-placeholder-val="{{ true }}"><div style="{{ disc.d2.gridCss }}">\n        <sc-for list="{{ disc.d2.tabCards }}"'
END_OLD = '        </sc-for>\n      </div>\n    </section>\n\n    <sc-if value="{{ disc.showModules }}"'
END_NEW = '        </sc-for>\n      </div></sc-if>' + LIST + '\n    </section>\n\n    <sc-if value="{{ disc.showModules }}"'
EXPAND = [
    ("go: () => this.setState({ dTab: k }),", "go: () => this.setState({ dTab: k, dExpLine: null, dExpN: 15 }),"),
    ("d2.tabSeeAllLabel = 'See all ' + (isSt ? CSA.length : DCOLL[tk].items.length) + ' \\u2192';\n    d2.tabSeeAll = isSt ? goStories : dOpenColl(tk);\n    d2.tabCards = isSt ? storyCards : DCOLL[tk].items.slice(0, 5).map(e => Object.assign(card(e), { isExp: true }));", LOGIC),
    (GRID_OLD, GRID_NEW),
    (END_OLD, END_NEW),
    # tab renamed (Group CX, 6 Nov 2026)
    ("'Customer stories' : DCOLL[k].title", "'Recent customer stories' : DCOLL[k].title"),
]

# 02 Curated stories, Recent customer stories (Group CX, 6 Nov 2026):
#   Recent = added to the hub in the last 90 days (each story's `added` date in
#   data/customer-stories.js), newest first; if fewer than 5 qualify, the newest 5 still show.
#   Stories added the same day: photographed ones first, rotating across business lines.
#   Open reads the full story in place (a dark reader with ‹ › to the next story); See all
#   expands in place like the other tabs. The Customer Stories tab stays the full archive.
CS_RECENT = ("    const csT = x => { const t = Date.parse((x && x.added) || ''); return isNaN(t) ? 0 : t; };\n"
"    const csRR = g => { const q = {}, ord = []; g.forEach(x => { if (!q[x.line]) { q[x.line] = []; ord.push(x.line); } q[x.line].push(x); }); const out = []; while (out.length < g.length) ord.forEach(l => { if (q[l].length) out.push(q[l].shift()); }); return out; };\n"
"    const csDays = {}; CSA.forEach(x => { const k = csT(x); (csDays[k] = csDays[k] || []).push(x); });\n"
"    const csOrd = []; Object.keys(csDays).map(Number).sort((a, b) => b - a).forEach(k => { const g = csDays[k]; csRR(g.filter(x => x.photo)).concat(csRR(g.filter(x => !x.photo))).forEach(x => csOrd.push(x)); });\n"
"    const csIn = csOrd.filter(x => csT(x) && Date.now() - csT(x) <= 90 * 864e5);\n"
"    const csRecent = csIn.length >= 5 ? csIn : csOrd.slice(0, 5);\n"
"    const storyItems = csRecent.map(x => ({ id: x.id, name: x.title, essence: x.memorable, line: x.line, defining: false, notDef: true, isExp: false, dot: dot(CSL[x.line] || '#E8B96A'), img: Object.assign(img(x.photo, CSG[x.line] || '#24473A'), x.photo_position ? { backgroundPosition: x.photo_position } : {}), open: (ev) => { if (ev && ev.stopPropagation) ev.stopPropagation(); this.setState({ dStory: x.id }); } }));\n"
"    const storyCards = storyItems.slice(0, 5);\n")
READER_VM = ("\n    { const si = S.dStory ? csRecent.findIndex(x => x.id === S.dStory) : -1; d2.hasStory = si >= 0; d2.story = null;\n"
"      if (si >= 0) { const x = csRecent[si], n = csRecent.length, ex = x.experience, D = this._csDeco(x), at = csT(x);\n"
"        const go = (j) => (ev) => { if (ev && ev.stopPropagation) ev.stopPropagation(); this.setState({ dStory: csRecent[(j + n) % n].id }); };\n"
"        d2.story = { title: x.title, line: x.line, place: x.place || x.category || '', story: x.story, memorable: x.memorable, colleagues: x.colleagues || '', source: x.source || '', dot: dot(CSL[x.line] || '#E8B96A'),\n"
"          added: at ? 'Added ' + new Date(at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }) : '',\n"
"          bandCss: { position: 'relative', aspectRatio: '16 / 7', flex: '0 0 auto', backgroundColor: '#111', backgroundImage: x.photo ? 'url(\"' + x.photo + '\")' : D.grad, backgroundSize: 'cover', backgroundPosition: x.photo_position || 'center' },\n"
"          hasExp: !!ex, expKicker: ex && ex.sure ? 'Signature Experience' : 'Likely Signature Experience', expName: ex ? ex.name : '',\n"
"          openExp: (ev) => { if (ev && ev.stopPropagation) ev.stopPropagation(); this.setState({ dStory: null }); this.openExp(ex.id); },\n"
"          close: () => this.setState({ dStory: null }), keep: (ev) => { if (ev && ev.stopPropagation) ev.stopPropagation(); },\n"
"          prev: go(si - 1), next: go(si + 1), pos: (si + 1) + ' of ' + n, all: (ev) => { if (ev && ev.stopPropagation) ev.stopPropagation(); this.setState({ dStory: null }); goStories(); } }; } }")
NAV = "font-family:inherit;width:40px;height:40px;border-radius:50%;border:1px solid rgba(255,255,255,.22);background:transparent;color:#F6F3EC;font-size:18px;cursor:pointer"
READER = ('\n      <sc-if value="{{ disc.d2.hasStory }}" hint-placeholder-val="{{ false }}"><div data-d2-story="1" sc-camel-on-click="{{ disc.d2.story.close }}" style="position:fixed;inset:0;z-index:9000;background:rgba(4,7,9,.8);backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);display:flex;align-items:center;justify-content:center;padding:28px 16px">'
  '<div data-d2-story-panel="1" role="dialog" aria-label="Customer story" sc-camel-on-click="{{ disc.d2.story.keep }}" style="position:relative;width:100%;max-width:860px;max-height:calc(100vh - 56px);overflow:auto;background:#0E171D;border:1px solid rgba(232,185,106,.28);border-radius:20px;box-shadow:0 40px 90px -30px rgba(0,0,0,.9);color:#F6F3EC;display:flex;flex-direction:column">'
  '<div style="{{ disc.d2.story.bandCss }}"><div style="position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.45) 0%,rgba(0,0,0,0) 35%,rgba(14,23,29,0) 60%,#0E171D 100%)"></div>'
  '<div style="position:absolute;top:16px;left:18px;right:16px;display:flex;justify-content:space-between;align-items:center;gap:10px"><span style="font-size:10px;font-weight:600;letter-spacing:.2em;text-transform:uppercase;color:#0A1014;background:#E8B96A;border-radius:999px;padding:5px 11px">&#10077; Customer story</span>'
  '<button sc-camel-on-click="{{ disc.d2.story.close }}" aria-label="Close" style="font-family:inherit;width:38px;height:38px;border-radius:50%;border:1px solid rgba(255,255,255,.3);background:rgba(0,0,0,.5);color:#fff;font-size:16px;cursor:pointer">&#10005;</button></div></div>'
  '<div data-d2-story-body="1" style="padding:6px 40px 34px;display:flex;flex-direction:column;gap:18px">'
  '<div style="display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;font-size:10.5px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:rgba(255,255,255,.6)"><span style="display:inline-flex;align-items:center;gap:7px"><span style="{{ disc.d2.story.dot }}"></span>{{ disc.d2.story.line }}</span><span>{{ disc.d2.story.place }}</span><span style="color:rgba(255,255,255,.4)">{{ disc.d2.story.added }}</span></div>'
  '<div style="font-family:\'Fraunces\',serif;font-size:34px;line-height:1.12;letter-spacing:-.01em;text-wrap:balance">{{ disc.d2.story.title }}</div>'
  '<div style="font-size:15.5px;line-height:1.75;font-weight:300;color:rgba(246,243,236,.88);text-wrap:pretty">{{ disc.d2.story.story }}</div>'
  '<div style="border-left:2px solid #E8B96A;background:rgba(232,185,106,.07);border-radius:0 12px 12px 0;padding:16px 20px"><div style="font-size:10px;font-weight:600;letter-spacing:.2em;text-transform:uppercase;color:#E8B96A;margin-bottom:6px">What made it memorable</div><div style="font-size:14.5px;line-height:1.65;color:#F6F3EC;text-wrap:pretty">{{ disc.d2.story.memorable }}</div></div>'
  '<div style="display:flex;flex-wrap:wrap;gap:8px 28px;font-size:12.5px;color:rgba(255,255,255,.62)"><div><span style="color:rgba(255,255,255,.4)">Colleagues&nbsp;&nbsp;</span>{{ disc.d2.story.colleagues }}</div><div><span style="color:rgba(255,255,255,.4)">Source&nbsp;&nbsp;</span>{{ disc.d2.story.source }}</div></div>'
  '<sc-if value="{{ disc.d2.story.hasExp }}" hint-placeholder-val="{{ true }}"><button sc-camel-on-click="{{ disc.d2.story.openExp }}" style="font-family:inherit;text-align:left;display:flex;align-items:center;justify-content:space-between;gap:16px;width:100%;padding:14px 18px;border-radius:14px;border:1px solid rgba(232,185,106,.4);background:rgba(232,185,106,.06);color:#F6F3EC;cursor:pointer" style-hover="background:rgba(232,185,106,.14)"><span style="min-width:0"><span style="display:block;font-size:10px;font-weight:600;letter-spacing:.18em;text-transform:uppercase;color:#E8B96A">{{ disc.d2.story.expKicker }}</span><span style="display:block;font-size:17px;font-weight:300;margin-top:3px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ disc.d2.story.expName }}</span></span><span style="color:#E8B96A;font-size:12px;font-weight:500;white-space:nowrap">Open experience &#8594;</span></button></sc-if>'
  '<div style="display:flex;align-items:center;justify-content:space-between;gap:12px;border-top:1px solid rgba(255,255,255,.1);padding-top:18px;flex-wrap:wrap">'
  '<div style="display:flex;align-items:center;gap:10px"><button sc-camel-on-click="{{ disc.d2.story.prev }}" aria-label="Previous story" style="' + NAV + '">&#8249;</button><button sc-camel-on-click="{{ disc.d2.story.next }}" aria-label="Next story" style="' + NAV + '">&#8250;</button><span style="font-size:12px;color:rgba(255,255,255,.55)">{{ disc.d2.story.pos }} recent stories</span></div>'
  '<button sc-camel-on-click="{{ disc.d2.story.all }}" style="font-family:inherit;font-size:12px;border:0;background:transparent;color:#E8B96A;cursor:pointer;padding:6px 0">All customer stories &#8594;</button></div>'
  '</div></div></div></sc-if>')
OLD_LIST_ACTS = '<div data-d2-acts="1" style="display:flex;gap:6px;align-items:center"><button sc-camel-on-click="{{ r.onCmp }}" style="{{ r.cmpCss }}">{{ r.cmpLabel }}</button><button sc-camel-on-click="{{ r.onSave }}" style="{{ r.saveCss }}">{{ r.saveLabel }}</button>'
STORIES = [
    ("    const storyCards = CSA.filter(x => x.photo).concat(CSA.filter(x => !x.photo)).slice(0, 5).map(x => ({ id: x.id, name: x.title, essence: x.memorable, line: x.line, defining: false, notDef: true, isExp: false, dot: dot(CSL[x.line] || '#E8B96A'), img: Object.assign(img(x.photo, CSG[x.line] || '#24473A'), x.photo_position ? { backgroundPosition: x.photo_position } : {}), open: goStories }));\n", CS_RECENT),
    ("['stories', 'Moments told by the colleagues who made them, each an expression of a Signature Experience in the field.']",
     "['stories', 'Moments told by the colleagues who made them, newest first: every customer story added in the last 90 days.']"),
    ("n: k === 'stories' ? CSA.length : DCOLL[k].items.length,", "n: k === 'stories' ? csRecent.length : DCOLL[k].items.length,"),
    ("const exp = !isSt && !!S.dExp, lmapE = this._dLineMap(), allIt = isSt ? [] : DCOLL[tk].items,", "const exp = !!S.dExp, lmapE = this._dLineMap(), allIt = isSt ? storyItems : DCOLL[tk].items,"),
    ("'See all ' + (isSt ? CSA.length : allIt.length) + ' \\u2192';", "'See all ' + allIt.length + ' \\u2192';"),
    ("d2.tabSeeAll = isSt ? goStories : () => this.setState({ dExp: !exp,", "d2.tabSeeAll = () => this.setState({ dExp: !exp,"),
    ("d2.tabCards = isSt ? storyCards : (d2.showCards ? shown.map(e => Object.assign(card(e), { isExp: true })) : []);", "d2.tabCards = d2.showCards ? (isSt ? shown : shown.map(e => Object.assign(card(e), { isExp: true }))) : [];"),
    ("d2.expRows = d2.showList ? shown.map(card) : [];", "d2.expRows = d2.showList ? (isSt ? shown : shown.map(e => Object.assign(card(e), { isExp: true }))) : [];"),
    ("d2.expCount = fl.length + (fl.length === 1 ? ' experience' : ' experiences');",
     "d2.expCount = fl.length + (isSt ? (fl.length === 1 ? ' story' : ' stories') : (fl.length === 1 ? ' experience' : ' experiences'));"),
    ("d2.more = () => this.setState({ dExpN: eN + 15 });", "d2.more = () => this.setState({ dExpN: eN + 15 });" + READER_VM),
    (OLD_LIST_ACTS, OLD_LIST_ACTS.replace('<button sc-camel-on-click="{{ r.onCmp }}"', '<sc-if value="{{ r.isExp }}" hint-placeholder-val="{{ true }}"><button sc-camel-on-click="{{ r.onCmp }}"').replace('{{ r.saveLabel }}</button>', '{{ r.saveLabel }}</button></sc-if>')),
    ("{{ disc.d2.moreLabel }}</button></div></sc-if>\n    </section>", "{{ disc.d2.moreLabel }}</button></div></sc-if>" + READER + "\n    </section>"),
    ("if (this.state.intro) { this._endIntro(); return; }", "if (this.state.intro) { this._endIntro(); return; }\n        if (this.state.dStory) { this.setState({ dStory: null }); return; }"),
    # benchmark cards open the Benchmark library's quick detail (the new design), not the full story
    ("const openBench = (id) => { if (id) { try { window.__BM_OPEN = id; } catch (e) {} } this.go('benchmark-hub'); };",
     "const openBench = (id) => { if (id) { try { window.__BM_OPEN = id; window.__BM_QUICK = true; } catch (e) {} } this.go('benchmark-hub'); };"),
]

# 01 Showreel: the defining moments only, eight of them (one tick each), opening on the week's
REEL_OLD = "const rest = this._dShuffle(withImg.filter(e => !e.defining), this.state.dSeed + 7); return def.concat(rest); }"
REEL_NEW = "return def.slice(0, 8); } /* v2: eight defining moments; was def + every other experience */"

html = open(PATH, encoding="utf-8").read()
m = re.search(r'(<script type="__bundler/template">\s*)(".*?")(\s*</script>)', html, re.S)
t = json.loads(m.group(2))
if 'id="sec-reel"' in t:
    n0 = t
    # MARKS: text a step leaves behind even after a later step rewrites its output, so a rerun
    # doesn't apply it a second time
    MARKS = {"const TABS = [['defining',": "const CSA = ((window.CS_DATA", "['welcome', 'This week: '": "['added', 'The newest experiences"}
    for old, new in TABS2 + EXPAND + STORIES:
        if old in MARKS and MARKS[old] in t: continue
        if new not in t and old in t:  # absent both ways: a later step rewrote that text
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
    for old, new in TABS2 + EXPAND + STORIES:
        assert t.count(old) == 1, old[:70]
        t = t.replace(old, new, 1)
    html = html[:m.start(2)] + json.dumps(t).replace("</", "<\\u002F") + html[m.end(2):]
    open(PATH, "w", encoding="utf-8").write(html)
    print("discovery v2: applied")
