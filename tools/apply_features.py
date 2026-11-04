"""Show or hide hub sections from features.json (true = shown, false = hidden).

Hidden sections keep their code and data; they are switched off where the page decides what to
render, so menus, tabs, buttons, search results and deep links all respect the switch:

  report_studio  the Report Studio tab and view, Echo's "Open in Report Studio" and report PDF download
  rag_status     the RAG (On track / On watch / Needs a decision) strip on experience cards, and RAG in
                 Ask Echo (its instructions, list dots and reasons, the Health column, spotlight pill)
  idea_exchange  the Idea Exchange menu item and view, "See it in Idea Exchange" on experience cards
  cx_academy     the "In development · CX Academy" menu item and placeholder view
  benchmark_editor  the Benchmark Editor tab inside Benchmark (Library · Transfer Viewer · Boards stay)
  board_sharing  Boards' file sharing: Save board / Import board, a board's Share sheet, "Shared with me"
                 and the download-file reminder; Boards are labelled as private to this browser
  project_plus   Project Plus as a business line: menu, line page, catalogue chips, hero, Portfolio
                 Discovery counts, Activity feed and search; also /mcp and Submit & review

How: the page reads window.__SIG_OFF (written into <head> from features.json); the template carries
small guards that check it (inserted once, idempotent). A few fixed sentences that name a hidden
section are swapped for neutral wording while it is hidden, and swapped back when it is shown.
/mcp reads features.json directly (netlify/functions/_lib/mcp-core.mjs).

Always on (not switches), installed by the same pass:
  - Portfolio Discovery: "Theme of the week" from discovery-themes.json, and the defining moment of the
    week (the showreel opens on it and the Defining moments rail leads with it); both change every Monday
  - the compare view's AI read comes from /api/compare-read (one read per set, shared with CX Martin)
  - the embedded export state carries no one's saved audits or links (userData is emptied)

Usage: python3 tools/apply_features.py    (also run by the Netlify build)
"""
import base64, gzip, json, re

PATH = "index.html"
F = json.load(open("features.json"))
OFF = {"reportStudio": F.get("report_studio") is False, "rag": F.get("rag_status") is False,
       "ideaExchange": F.get("idea_exchange") is False, "cxAcademy": F.get("cx_academy") is False,
       "benchmarkEditor": F.get("benchmark_editor") is False, "projectPlus": F.get("project_plus") is False,
       "boardSharing": F.get("board_sharing") is False}
THEMES = [t for t in json.load(open("discovery-themes.json")).get("themes", []) if t.get("title") and t.get("match")]
O = "(window.__SIG_OFF || {})"

# (old, new, count): guards that read the runtime switches. Applied once; skipped if already there.
GUARDS = [
    # views: a hidden view falls back to Portfolio Discovery (covers menus, deep links and #report)
    ("    if (isAlt && V === 'academy') V = 'discover';\n",
     "    if (isAlt && V === 'academy') V = 'discover';\n    { const _OFF = " + O + "; if ((_OFF.reportStudio && V === 'report-studio') || (_OFF.ideaExchange && V === 'transfer') || (_OFF.cxAcademy && V === 'academy')) V = 'discover'; }\n", 1),
    # sidebar / phone menu
    ("    if (isCat) navGroups.forEach(g => { g.items = g.items.filter(it => ['Benchmark', 'Idea Exchange', 'Boards', 'Aldar CX Time'].indexOf(it.label) === -1); });\n",
     "    if (isCat) navGroups.forEach(g => { g.items = g.items.filter(it => ['Benchmark', 'Idea Exchange', 'Boards', 'Aldar CX Time'].indexOf(it.label) === -1); });\n"
     "    { const _O = " + O + "; navGroups.forEach(g => { g.items = g.items.filter(it => !(_O.ideaExchange && it.label === 'Idea Exchange') && !(_O.reportStudio && it.label === 'Report Studio') && !(_O.cxAcademy && it.label === 'CX Academy')); }); for (let gi = navGroups.length - 1; gi >= 0; gi--) if (!navGroups[gi].items.length) navGroups.splice(gi, 1); }\n", 1),
    # Signature Experiences tabs (Catalogue · Activity · Report Studio), both places they are built
    (".filter(t => !(isLines || isAlt) || t.k !== 'report-studio');",
     ".filter(t => !(isLines || isAlt || " + O + ".reportStudio) || t.k !== 'report-studio');", 1),
    (".filter(p => window.__SIG_EDITION !== 'alt' || p[0] !== 'report-studio')",
     ".filter(p => (window.__SIG_EDITION !== 'alt' && !" + O + ".reportStudio) || p[0] !== 'report-studio')", 1),
    # search everything (⌘K): hidden destinations are not offered
    ("const _ed = window.__SIG_EDITION; views.filter(",
     "const _ed = window.__SIG_EDITION; const _O5 = " + O + "; views.filter(v => !(_O5.reportStudio && v[0] === 'report-studio') && !(_O5.ideaExchange && v[0] === 'transfer') && !(_O5.cxAcademy && v[0] === 'academy') && !(_O5.projectPlus && v[0] === 'line-projectplus')).filter(", 1),
    # experience card: "See it in Idea Exchange" and the RAG strip
    ("has: live && window.__SIG_EDITION !== 'cat',", "has: live && window.__SIG_EDITION !== 'cat' && !" + O + ".ideaExchange,", 1),
    ("showRag: !isLines,", "showRag: !isLines && !" + O + ".rag,", 1),
    # Portfolio Discovery: the "CX Academy highlights" placeholder panel
    ("showAcademy: window.__SIG_EDITION !== 'alt' && window.__SIG_EDITION !== 'cat',", "showAcademy: window.__SIG_EDITION !== 'alt' && window.__SIG_EDITION !== 'cat' && !" + O + ".cxAcademy,", 1),
    # Ask Echo: answer cards
    ("ragColor: RAGC[x.rag] || '#8A929A'", "ragColor: " + O + ".rag ? 'transparent' : (RAGC[x.rag] || '#8A929A')", 2),
    ("reason: String(x.reason || ''),", "reason: " + O + ".rag ? '' : String(x.reason || ''),", 1),
    ("const cols = [...new Set([...CANON, ...req])].filter(c => COLDEF[c])", "const cols = [...new Set([...CANON, ...req])].filter(c => COLDEF[c]).filter(c => c !== 'rag' || !" + O + ".rag)", 1),
    ("spHasRag: !!spRag,", "spHasRag: !!spRag && !" + O + ".rag,", 1),
    ("const report = dd.report ? {", "const report = (dd.report && !" + O + ".reportStudio) ? {", 1),
    ("const download = dd.download ? {", "const download = (dd.download && !" + O + ".reportStudio) ? {", 1),
    # Ask Echo: suggested questions
    ("    return CFG[scope] || CFG.Corporate;\n  }\n  setAsstScope(",
     "    const _c = CFG[scope] || CFG.Corporate; const _O = " + O + ";\n    if (_c && Array.isArray(_c.samples)) _c.samples = _c.samples.filter(s => !(_O.rag && /\\b(Red|Amber|Green|RAG)\\b/.test(s)) && !(_O.reportStudio && /\\breport\\b|PDF/i.test(s)));\n    return _c;\n  }\n  setAsstScope(", 1),
    # Ask Echo: instructions and data sent to the model
    ("    lines.push('DATA=' + JSON.stringify(items));\n",
     "    { const _O = " + O + ";\n"
     "      if (_O.rag || _O.reportStudio || _O.ideaExchange) {\n"
     "        for (let i = lines.length - 1; i >= 0; i--) if ((_O.rag && /RAG is pre-computed|^REASON CLUSTERS/.test(lines[i])) || (_O.reportStudio && /^\\u2022 (REPORT|DOWNLOAD) \\u2014/.test(lines[i]))) lines.splice(i, 1);\n"
     "        for (let i = 0; i < lines.length; i++) { if (_O.rag) lines[i] = lines[i].replace(/; by RAG health \\{[^}]*\\}/, '').replace(/,? ?Health\\/RAG/g, '').replace(/ \\+ a RAG health dot/, '').replace(/,? the RAG split/g, '').replace(/,? ?RAG \\+ reason/g, '').replace(/\\(the RAG or lifecycle split\\)/g, '(the lifecycle split)').replace(/\\|\"rag\"/g, '').replace(/, Reds needing attention/g, '').replace(/, Reds,/g, ',').replace(/ all Red,/g, ''); if (_O.reportStudio) lines[i] = lines[i].replace(/ These match the Report Studio board exactly\\./, ''); }\n"
     "        lines.push('NOT PART OF THE HUB RIGHT NOW: ' + [_O.rag ? 'RAG / Red-Amber-Green health ratings' : '', _O.reportStudio ? 'Report Studio and report downloads' : '', _O.ideaExchange ? 'the Idea Exchange' : ''].filter(Boolean).join(', ') + '. Never mention, rate, group or filter by them, and never offer them. Describe status only by lifecycle stage (In Review, In Implementation, Deployed & Live, Audited).');\n"
     "      }\n"
     "      const _items = _O.rag ? items.map(i => { const o = Object.assign({}, i); delete o.rag; delete o.reason; delete o.reasonCluster; return o; }) : items;\n"
     "      lines.push('DATA=' + JSON.stringify(_items)); }\n", 1),
]

GUARDS += [
    # Project Plus: the hub's own "no Project Plus" switch (menu, line view, catalogue, hero, discovery)
    ("const noPP = isLines || isAlt;", "const noPP = isLines || isAlt || " + O + ".projectPlus;", 1),
    ("(this._audience() === 'lines' || window.__SIG_EDITION === 'alt') && x[0] === 'pp')); }", "(this._audience() === 'lines' || window.__SIG_EDITION === 'alt' || " + O + ".projectPlus) && x[0] === 'pp')); }", 1),
    ("const AE = this._activityEvents();", "const AE = this._activityEvents().filter(e => e.line !== 'pp' || !" + O + ".projectPlus);", 1),
    ("['est', 'Estates Plus'], ['pp', 'Project Plus']];\n    const _actLine", "['est', 'Estates Plus'], ['pp', 'Project Plus']].filter(l => l[0] !== 'pp' || !" + O + ".projectPlus);\n    const _actLine", 1),
]

RAIL_OLD = "{ key: 'welcome', idx: '03', kicker: 'A theme', accent: '#3D5958', band: 'linear-gradient(118deg,#3D5958 0%,#26403F 100%)', title: 'Arrival & welcome', blurb: 'How we greet people across every business line — one thread running through the portfolio.', "
GUARDS += [
    # weekly rotation: the defining moment of the week leads the Defining moments rail ...
    ("const ddef = this._dShuffle(dall.filter(e => e.defining && e.image), this.state.dSeed + 3);",
     "const _WK = Math.floor((Date.now() - Date.UTC(2026, 0, 5)) / 604800000); /* weeks since Mon 5 Jan 2026 */\n      const ddef = ((arr, k) => { const g = {}; arr.slice().sort((a, b) => String(a.id).localeCompare(String(b.id))).forEach(e => { (g[e.line] = g[e.line] || []).push(e); }); const ks = Object.keys(g).sort(); if (!ks.length) return arr; const L = g[ks[((k % ks.length) + ks.length) % ks.length]]; const first = L[Math.floor(Math.abs(k) / ks.length) % L.length]; const rr = []; for (let i = 0; rr.length < arr.length; i++) ks.forEach(x => { if (g[x][i]) rr.push(g[x][i]); }); return [first].concat(rr.filter(e => e !== first)); })(dall.filter(e => e.defining), _WK).filter(e => e.image); /* each week: the next business line, then its next flagship */", 1),
    # ... and opens the showreel
    ("const def = this._dShuffle(withImg.filter(e => e.defining), this.state.dSeed);",
     "const _wk = Math.floor((Date.now() - Date.UTC(2026, 0, 5)) / 604800000); const def = ((arr, k) => { const g = {}; arr.slice().sort((a, b) => String(a.id).localeCompare(String(b.id))).forEach(e => { (g[e.line] = g[e.line] || []).push(e); }); const ks = Object.keys(g).sort(); if (!ks.length) return arr; const L = g[ks[((k % ks.length) + ks.length) % ks.length]]; const first = L[Math.floor(Math.abs(k) / ks.length) % L.length]; const rr = []; for (let i = 0; rr.length < arr.length; i++) ks.forEach(x => { if (g[x][i]) rr.push(g[x][i]); }); return [first].concat(rr.filter(e => e !== first)); })(this._dAll().filter(e => e.defining), _wk).filter(e => e.image); /* opens on the defining moment of the week */", 1),
    ("if (n0 > 1) { this.setState({ dReelIdx: Math.floor(Math.random() * n0) }); return; }",
     "if (n0 > 1) { this.setState({ dReelIdx: 0 }); return; } /* opens on the defining moment of the week */", 1),
    # the showreel waits behind the welcome screen, then opens on the defining moment of the week
    ("_endIntro() { if (!this.state.intro) return; clearTimeout(this._introT); this.setState({ intro: false }); }",
     "_endIntro() { if (!this.state.intro) return; clearTimeout(this._introT); this.setState({ intro: false, dReelIdx: 0 }); }", 1),
    ("if (this.state.view !== 'discover' || !this.state.dReelPlaying) return;", "if (this.state.view !== 'discover' || !this.state.dReelPlaying || this.state.intro) return;", 1),
    # theme of the week (discovery-themes.json -> window.__SIG_THEMES)
    ("const dwelRe = /welcom|arriv|first|onboard|greet|check-in|check in/i;\n      const dwel = this._dShuffle(dall.filter(e => e.image && dwelRe.test(e.name + ' ' + e.essence)), this.state.dSeed + 17);",
     "const _TH = (window.__SIG_THEMES && window.__SIG_THEMES.length) ? window.__SIG_THEMES : [{ title: 'Arrival & welcome', blurb: 'How we greet people across every business line, one thread running through the portfolio.', match: 'welcom|arriv|first|onboard|greet|check-in|check in', accent: '#3D5958', deep: '#26403F' }];\n"
     "      const _thOk = _TH.map(th => { let re; try { re = new RegExp(th.match, 'i'); } catch (e) { re = /(?!)/; } return { th: th, items: dall.filter(e => e.image && re.test(e.name + ' ' + e.essence)) }; }).filter(x => x.items.length >= 4);\n"
     "      const _thPick = _thOk.length ? _thOk[((_WK % _thOk.length) + _thOk.length) % _thOk.length] : { th: _TH[0], items: [] };\n"
     "      const dwelTheme = Object.assign({ accent: '#3D5958', deep: '#26403F', blurb: '' }, _thPick.th);\n"
     "      const dwel = this._dShuffle(_thPick.items, this.state.dSeed + 17);", 1),
    ("welcome: { title: 'Arrival & welcome', accent: '#3D5958', items: dwel }", "welcome: { title: dwelTheme.title, accent: dwelTheme.accent, items: dwel }", 1),
    (RAIL_OLD, "{ key: 'welcome', idx: '03', kicker: 'Theme of the week', accent: dwelTheme.accent, band: 'linear-gradient(118deg,' + dwelTheme.accent + ' 0%,' + dwelTheme.deep + ' 100%)', title: dwelTheme.title, blurb: dwelTheme.blurb, ", 1),
    # compare view: the AI read comes from the site (shared with CX Martin); the in-page reader is the fallback
    ("Promise.resolve(cc({ system: sys, messages: [{ role: 'user', content: JSON.stringify(recs, null, 1) }], max_tokens: 700 })).then(txt => {",
     "Promise.resolve((/^https?:$/.test(location.protocol) ? fetch('/api/compare-read', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ ids: ids, refresh: !!force }) }).then(r => r.ok ? r.text() : Promise.reject(new Error('remote'))) : Promise.reject(new Error('local'))).catch(() => cc({ system: sys, messages: [{ role: 'user', content: JSON.stringify(recs, null, 1) }], max_tokens: 700 }))).then(txt => {", 1),
]

# guards inside bundled modules: (old, new, count)
ASSET_GUARDS = [
    # Benchmark: the Benchmark Editor tab (both tab lists) and its view
    ("{ k: 'curator', label: '\\u270E Benchmark Editor' }].map(t => {", "{ k: 'curator', label: '\\u270E Benchmark Editor' }].filter(t => t.k !== 'curator' || !" + O + ".benchmarkEditor).map(t => {", 1),
    ("['curator', 'Benchmark Editor'], ['boards', 'Boards']];", "['curator', 'Benchmark Editor'], ['boards', 'Boards']].filter(x => x[0] !== 'curator' || !" + O + ".benchmarkEditor);", 1),
    ("isGallery: S.view === 'gallery',", "isGallery: S.view === 'gallery' || (S.view === 'curator' && !!" + O + ".benchmarkEditor),", 1),
    ("isCurator: S.view === 'curator',", "isCurator: S.view === 'curator' && !" + O + ".benchmarkEditor,", 1),
    # Boards: file sharing (Shared with me, Share sheet, download-file reminder, shelf tab)
    ("bHasShared: bShared.length > 0,", "bHasShared: bShared.length > 0 && !" + O + ".boardSharing,", 1),
    ("sh: sh, hasSh: !!sh,", "sh: sh, hasSh: !!sh && !" + O + ".boardSharing,", 1),
    ("dirty: !!S.dirty, onSaveRepo", "dirty: !!S.dirty && !" + O + ".boardSharing, onSaveRepo", 1),
    ("[['all', 'All'], ['mine', 'Mine'], ['shared', 'Shared with me']].map(", "[['all', 'All'], ['mine', 'Mine'], ['shared', 'Shared with me']].filter(p => p[0] !== 'shared' || !" + O + ".boardSharing).map(", 1),
]

# (shown, hidden, switch): fixed wording that names a section
TEXTS = [
    ("summarise the portfolio, or download the report \u2014 every answer", "or summarise the portfolio \u2014 every answer", "reportStudio"),
]
ASSET_TEXTS = [(p["shown"], p["hidden"], "boardSharing") for p in json.load(open("tools/board-sharing.json"))["pairs"]]
ASSET_TEXTS += [  # inside bundled modules
    ("this read, the benchmark recommendations and the Idea Exchange translations", "this read and the benchmark recommendations", "ideaExchange"),
    ("Ask Echo, the comparison reads and Idea Exchange generation call a language model", "Ask Echo and the comparison reads call a language model", "ideaExchange"),
]

html = open(PATH, encoding="utf-8").read()

# 1. runtime switches in <head>
html = re.sub(r'<script id="__sig_features">.*?</script>\n', "", html)
tag = ('<script id="__sig_features">window.__SIG_OFF=' + json.dumps(OFF, separators=(",", ":")) + ';window.__SIG_THEMES='
       + json.dumps([{k: t.get(k) for k in ("title", "blurb", "match", "accent", "deep") if t.get(k)} for t in THEMES], separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/") + ';</script>\n')
i = html.find('<script id="__sig_edition">')
assert i > 0, "edition hook not found"
html = html[:i] + tag + html[i:]

# 2. template guards + wording
m = re.search(r'(<script type="__bundler/template">\s*)(".*?")(\s*</script>)', html, re.S)
t = json.loads(m.group(2))
for old, new, n in GUARDS:
    if t.count(new) >= n:
        continue
    assert t.count(old) == n, f"guard anchor found {t.count(old)}x (expected {n}): {old[:70]}"
    t = t.replace(old, new)
for shown, hidden, k in TEXTS:
    want, other = (hidden, shown) if OFF[k] else (shown, hidden)
    if want not in t:
        assert other in t, "wording not found: " + shown[:60]
        t = t.replace(other, want)
html = html[:m.start(2)] + json.dumps(t).replace("</", "<\\u002F") + html[m.end(2):]

# 3. wording inside bundled modules
mm = re.search(r'(<script type="__bundler/manifest">\s*)(\{.*?\})(\s*</script>)', html, re.S)
man = json.loads(mm.group(2)); changed = False
for uid, e in man.items():
    if not re.search(r"html|javascript", e.get("mime", "")):
        continue
    raw = base64.b64decode(e["data"]); body = (gzip.decompress(raw) if e.get("compressed") else raw).decode("utf-8")
    new = body
    for old, gnew, n in ASSET_GUARDS:
        if old.split(".filter(")[0] in new and new.count(gnew) < n:
            if new.count(old) == n: new = new.replace(old, gnew)
    for shown, hidden, k in ASSET_TEXTS:
        want, other = (hidden, shown) if OFF[k] else (shown, hidden)
        new = new.replace(other, want)
    if new != body:
        b = new.encode("utf-8"); e["data"] = base64.b64encode(gzip.compress(b, 9, mtime=0) if e.get("compressed") else b).decode("ascii"); changed = True
if changed:
    html = html[:mm.start(2)] + json.dumps(man, separators=(",", ":")) + html[mm.end(2):]

# 4. the embedded export state carries no one's personal saves (audits, links); status overrides stay
ms = re.search(r'(<script type="application/json" id="__sig_state">)(.*?)(</script>)', html, re.S)
if ms:
    st = json.loads(ms.group(2))
    if st.get("userData"):
        st["userData"] = {}
        html = html[:ms.start(2)] + json.dumps(st, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/") + html[ms.end(2):]

open(PATH, "w", encoding="utf-8").write(html)
print("features:", {k: ("hidden" if v else "shown") for k, v in OFF.items()})
