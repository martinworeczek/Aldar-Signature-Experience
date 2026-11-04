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
  ask_echo       Ask Echo; while false, the Ask page shows CX Martin, the Copilot Studio agent
                 (cx_martin_chat_url, the agent's web-chat link from Copilot Studio > Channels > App)
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
       "boardSharing": F.get("board_sharing") is False, "askEcho": F.get("ask_echo") is False}
MARTIN_URL = F.get("cx_martin_chat_url") or ""        # the hub's branded chat (app/martin.html) or a Copilot Studio link
MARTIN_MS_URL = F.get("cx_martin_microsoft_url") or "" # Microsoft's own web chat, offered if the branded chat can't connect
assert not MARTIN_URL or MARTIN_URL.startswith(("https://", "/")), "cx_martin_chat_url must be https:// or a site path"
assert not MARTIN_MS_URL or MARTIN_MS_URL.startswith("https://"), "cx_martin_microsoft_url must be an https:// link"
THEMES = [t for t in json.load(open("discovery-themes.json")).get("themes", []) if t.get("title") and t.get("match")]
IMPL = {k: [p for p in v if isinstance(p, dict) and p.get("src")] for k, v in json.load(open("data/implementation-photos.json")).get("photos", {}).items() if isinstance(v, list)}
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
     "      const _slim = cfg.key === 'all'; /* every line in one prompt: send the essentials */\n"
     "      const _items = (_O.rag || _slim) ? items.map(i => { const o = Object.assign({}, i); if (_O.rag) { delete o.rag; delete o.reason; delete o.reasonCluster; } if (_slim) { o.narrative = String(o.narrative || '').slice(0, 140); o.note = String(o.note || '').slice(0, 220); delete o.trail; Object.keys(o).forEach(k => { const v = o[k]; if (v == null || v === '' || v === false || (Array.isArray(v) && !v.length)) delete o[k]; }); } return o; }) : items;\n"
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

GUARDS += [
    # catalogue cards: the pillar shows in the card detail only
    ("c2Pillar: pillar || '',", "c2Pillar: '',", 1),
    # card detail: implementation photos grouped by asset replace the SharePoint asset library
    ('      <div class="{{ modal.ch.assets.cls }}">', '      <sc-if value="{{ modal.showAssetLib }}" hint-placeholder-val="{{ false }}"><div class="{{ modal.ch.assets.cls }}">', 1),
    ('\n\n      <sc-if value="{{ modal.hasPhotos }}" hint-placeholder-val="{{ false }}">\n      <div class="{{ modal.ch.photos.cls }}"><div class="d3-ch-head"><div class="d3-num">{{ modal.ch.photos.n }}</div><div class="d3-lbl">Implementation photos</div></div>\n        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">\n          <sc-for list="{{ modal.photos }}" as="p" hint-placeholder-count="0"><div style="{{ p.d3 }}"></div></sc-for>\n        </div>\n      </div>\n      </sc-if>', '\n      </sc-if>\n\n      <div class="{{ modal.ch.photos.cls }}"><div class="d3-ch-head"><div class="d3-num">{{ modal.ch.photos.n }}</div><div class="d3-lbl">Implementation photos</div></div>\n        <div>\n          <sc-if value="{{ modal.hasPhotos }}" hint-placeholder-val="{{ false }}">\n          <sc-for list="{{ modal.photoGroups }}" as="pg" hint-placeholder-count="1">\n            <div style="margin-bottom:18px">\n              <div style="display:flex;align-items:baseline;gap:10px;margin-bottom:9px"><span style="font-size:10.5px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:#E8B96A">{{ pg.asset }}</span><span style="font-size:11px;color:rgba(255,255,255,.5)">{{ pg.countLabel }}</span></div>\n              <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:10px">\n                <sc-for list="{{ pg.items }}" as="p" hint-placeholder-count="2"><a href="{{ p.src }}" target="_blank" rel="noopener" title="{{ p.title }}" style="{{ p.d3 }}"></a></sc-for>\n              </div>\n            </div>\n          </sc-for>\n          </sc-if>\n          <sc-if value="{{ modal.noPhotos }}" hint-placeholder-val="{{ true }}"><div style="font-size:13px;color:rgba(255,255,255,.62);line-height:1.6;border:1px dashed rgba(255,255,255,.18);border-radius:10px;padding:16px 18px">No photos from the live experience yet. Business-line leads can add them, asset by asset, through <b style="color:#fff;font-weight:600">Submit &amp; review</b>.</div></sc-if>\n        </div>\n      </div>\n', 1),
    ("['audit', true], ['assets', true], ['photos', !!modal.hasPhotos]]", "['audit', true], ['assets', !!modal.showAssetLib], ['photos', true]]", 1),
    ("hasPhotos: !!(tgt.photos && tgt.photos.length), photos: (tgt.photos) ? tgt.photos.map(p => ({ bg: { aspectRatio: '4 / 3', borderRadius: '10px', backgroundImage: 'url(' + p + ')', backgroundSize: 'cover', backgroundPosition: 'center 32%' } })) : [],", 'hasPhotos: (function () { const L = [].concat(tgt.photos || [], ((window.__SIG_IMPL || {})[tgt.id]) || []).filter(Boolean); return L.length > 0; })(), photos: [], photoGroups: (function () { const L = [].concat(tgt.photos || [], ((window.__SIG_IMPL || {})[tgt.id]) || []).filter(Boolean).map(p => typeof p === \'string\' ? { src: p } : p).filter(p => p && p.src); const G = {}; const order = []; L.forEach(p => { const k = p.asset || \'At the experience\'; if (!G[k]) { G[k] = []; order.push(k); } G[k].push(p); }); return order.map(k => ({ asset: k, countLabel: G[k].length + (G[k].length === 1 ? \' photo\' : \' photos\'), items: G[k].map(p => ({ src: p.src, title: [p.caption, p.when].filter(Boolean).join(\' \\u00b7 \') || k, bg: { display: \'block\', aspectRatio: \'4 / 3\', borderRadius: \'8px\', backgroundImage: \'url("\' + p.src + \'")\', backgroundSize: \'cover\', backgroundPosition: \'center 32%\', backgroundColor: \'rgba(255,255,255,.06)\' } })) })); })(),', 1),
    ("(modal.photos || []).forEach(p => { p.d3 = Object.assign({}, p.bg, { borderRadius: '8px' }); });", "(modal.photoGroups || []).forEach(g => (g.items || []).forEach(p => { p.d3 = Object.assign({}, p.bg, { borderRadius: '8px' }); })); modal.noPhotos = !modal.hasPhotos;", 1),
    # Ask Echo: one knowledge base across every line (Hospitality's capabilities everywhere), no tabs
    ("asstScope: 'Education',", "asstScope: 'All',", 1),
    ("scope = scope || this.state.asstScope || 'Corporate';", "scope = scope || this.state.asstScope || 'All';", 1),
    ('    const _c = CFG[scope] || CFG.Corporate;', '    { const LN = [\'Corporate\', \'Hospitality\', \'Retail\', \'Education\', \'Development\', \'Estates\'].filter(k => CFG[k]);\n      CFG.All = { label: \'All lines\', key: \'all\', slug: \'group\', short: \'the Signature Experience Hub (every business line)\', data: null,\n        pillarsLine: LN.length + \' business lines (\' + LN.map(k => CFG[k].short + \': \' + CFG[k].pillarsLine).join(\'; \') + \')\',\n        note: LN.map(k => CFG[k].short + \': \' + CFG[k].note).join(\' \'),\n        intro: \'Echo answers from the live Signature Experience Hub, every business line in one knowledge base. Every answer is factual and grounded in the data: Echo retrieves, summarises and surfaces; it does not give opinions or recommendations.\',\n        docs: [].concat.apply([], LN.map(k => CFG[k].docs || [])),\n        extra: CFG.Hospitality.extra.concat([\'ALL BUSINESS LINES: DATA holds every line and each item carries its "line". When a question names a line, property, mall, school or community, answer for it; otherwise answer across all lines and say which lines are involved. Supporting documents belong to a line: only surface documents from the experience\\u2019s own line.\']),\n        samples: [\'Give me a two-minute executive summary across every line\', \'Show me every defining Signature Experience in Hospitality\', \'Compare Golden Coin and Sundown Ceremony\', \'What is live at Yas Mall?\', \'Show me the Kids Perfume Creation Room video\', \'What is launching in the next three months?\'] };\n    }\n    const _c = CFG[scope] || CFG.Corporate;', 1),
    ('    const cfg = this._asstScopeCfg(scope);\n    let rows = this.reportRows().filter(r => r.lineLabel === cfg.label);', "    const cfg = this._asstScopeCfg(scope);\n    if (cfg.key === 'all') return ['Corporate', 'Hospitality', 'Retail', 'Education', 'Development', 'Estates'].reduce((acc, sc) => acc.concat(this._asstRepo(sc)), []);\n    let rows = this.reportRows().filter(r => r.lineLabel === cfg.label);", 1),
    ("    (cfg.extra || []).forEach(x => lines.push(x));\n", '    (cfg.extra || []).forEach(x => lines.push(x));\n    if (cfg.key === \'all\') {\n      const uq = a => [...new Set(a.filter(Boolean))];\n      lines.push(\'FILTER TAXONOMY across every line: retrieve and combine experiences by these facets exactly as the repository filters do. Facets are listed per line (item field "line"). Journey Stage is DISTINCT from Lifecycle stage.\');\n      uq(items.map(i => i.line)).forEach(ln => { const its = items.filter(i => i.line === ln); const js = uq(its.map(i => i.journeyStage)), pl = uq(its.map(i => i.pillar)), at = uq([].concat(...its.map(i => i.assetTypes || []))), pr = uq([].concat(...its.map(i => i.properties || []))), sg = uq([].concat(...its.map(i => [].concat(i.segment || [], i.segments || [], i.verticals || [])))); lines.push(\'\\u2022 \' + ln + \': journey stages \' + (js.join(\' \\u00b7 \') || \'\\u2014\') + (pl.length ? \'; pillars \' + pl.join(\' \\u00b7 \') : \'\') + (sg.length ? \'; segments / verticals \' + sg.join(\' \\u00b7 \') : \'\') + (at.length ? \'; asset types \' + at.join(\' \\u00b7 \') : \'\') + (pr.length ? \'; properties \' + pr.slice(0, 40).join(\' \\u00b7 \') : \'\') + \'.\'); });\n      lines.push(\'PROPERTY / ASSET questions ("what is live at <property>", "scorecard for <property>"): match the item fields "properties" and "liveAssets"; count only the matching items; never rank one property against another as better or worse.\');\n    }\n', 1),
    ("(cfg.key === 'hp' ? ('; by journey stage {'", "((cfg.key === 'hp' || cfg.key === 'all') ? ('; by journey stage {'", 1),
    ("      asstScopeTabs = [['Corporate', 'Corporate Plus'],", "      asstScopeTabs = asstCfg.key === 'all' ? [] : [['Corporate', 'Corporate Plus'],", 1),
    ('const spDocs = spWantDocs ? asstDocs.map(', "const spDocs = spWantDocs ? ((asstCfg.key === 'all' && sp) ? ((this._asstScopeCfg(sp.line) || {}).docs || []) : asstDocs).map(", 1),
    ('padding-left:12px">Knowledge base</span>', 'padding-left:12px">Knowledge base &middot; every business line</span>', 1),
]

GUARDS += [
    # Ask: CX Martin (Copilot Studio) in place of Echo while ask_echo is false
    ("  <!-- ===================== ASSISTANT ===================== -->\n", '  <!-- ============ ASK CX MARTIN (Copilot Studio web chat, features.json) ============ -->\n  <sc-if value="{{ vMartin }}" hint-placeholder-val="{{ false }}">\n  <section style="max-width:none;padding:26px 28px 40px;width:100%">\n    <div style="position:relative;border-radius:20px;overflow:hidden;border:1px solid rgba(232,185,106,.26);background:radial-gradient(120% 140% at 50% 0%,#16232B 0%,#0A1014 70%);padding:30px 34px 28px">\n      <div style="font-size:9.5px;font-weight:700;letter-spacing:.24em;text-transform:uppercase;color:#E8B96A">Aldar &middot; Ask CX Martin</div>\n      <div style="font-family:\'Poppins\',sans-serif;color:#F6F3EC;font-size:clamp(26px,2.8vw,36px);font-weight:300;line-height:1.15;margin-top:12px;letter-spacing:-.015em">Ask CX Martin, Aldar&rsquo;s CX agent</div>\n      <div style="font-size:14px;font-weight:300;color:rgba(246,243,236,.72);line-height:1.6;margin-top:8px;max-width:70ch">The same agent as in Microsoft Copilot and Teams, answering live from the hub: signature experiences across every line, deployment, benchmarks, Aldar CX Time and side-by-side comparisons.</div>\n    </div>\n    <div style="margin-top:18px;border-radius:16px;overflow:hidden;border:1px solid rgba(232,185,106,.26);background:#0A1014;box-shadow:0 18px 44px -18px rgba(11,17,22,.45)">\n      <iframe src="{{ martinUrl }}" title="Ask CX Martin" allow="clipboard-write" style="display:block;width:100%;height:max(560px, calc(100vh - 300px));border:0;background:#0A1014"></iframe>\n    </div>\n  </section>\n  </sc-if>\n\n' + "  <!-- ===================== ASSISTANT ===================== -->\n", 1),
    ("vAssistant: V === 'assistant',", "vAssistant: V === 'assistant' && !" + O + ".askEcho, vMartin: V === 'assistant' && !!" + O + ".askEcho, martinUrl: window.__SIG_MARTIN_URL || '',", 1),
    ("iconItem('\u2726', 'Ask Echo', 'assistant')", "iconItem('\u2726', " + O + ".askEcho ? 'Ask CX Martin' : 'Ask Echo', 'assistant')", 1),
    ("['assistant', 'Ask Echo', 'The CX assistant'],", "['assistant', " + O + ".askEcho ? 'Ask CX Martin' : 'Ask Echo', " + O + ".askEcho ? 'Aldar\u2019s Copilot CX agent' : 'The CX assistant'],", 1),
    ("assistant: ['Overview', 'Ask Echo', ''],", "assistant: ['Overview', " + O + ".askEcho ? 'Ask CX Martin' : 'Ask Echo', ''],", 1),
]

GUARDS += [
    # sidebar: no "New" badge on Benchmark and Boards
    ("    // ---- view header text ----\n", "    navGroups.forEach(g => g.items.forEach(it => { if (it.right === 'New' && (it.label === 'Benchmark' || it.label === 'Boards')) { it.right = ''; it.rightCss = {}; } }));\n    // ---- view header text ----\n", 1),
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
    ("dirty: !!S.dirty, onSaveRepo", "dirty: false && !!S.dirty, onSaveRepo", 1),  # boards save automatically: no "download updated file" reminder
    ("[['all', 'All'], ['mine', 'Mine'], ['shared', 'Shared with me']].map(", "[['all', 'All'], ['mine', 'Mine'], ['shared', 'Shared with me']].filter(p => p[0] !== 'shared' || !" + O + ".boardSharing).map(", 1),
]

# (shown, hidden, switch): fixed wording that names a section
TEXTS = [
    ("summarise the portfolio, or download the report \u2014 every answer", "or summarise the portfolio \u2014 every answer", "reportStudio"),
]
_BS = json.load(open("tools/board-sharing.json"))
OFF["always"] = True  # wording that always applies
ASSET_TEXTS = [(p["shown"], p["hidden"], "always") for p in _BS["autosave"]] + [(p["shown"], p["hidden"], "boardSharing") for p in _BS["sharing_off"]]
ASSET_TEXTS += [  # inside bundled modules
    ("this read, the benchmark recommendations and the Idea Exchange translations", "this read and the benchmark recommendations", "ideaExchange"),
    ("Ask Echo, the comparison reads and Idea Exchange generation call a language model", "Ask Echo and the comparison reads call a language model", "ideaExchange"),
]

html = open(PATH, encoding="utf-8").read()

# 1. runtime switches in <head>
html = re.sub(r'<script id="__sig_features">.*?</script>\n', "", html)
tag = ('<script id="__sig_features">window.__SIG_OFF=' + json.dumps(OFF, separators=(",", ":")) + ';window.__SIG_THEMES='
       + json.dumps([{k: t.get(k) for k in ("title", "blurb", "match", "accent", "deep") if t.get(k)} for t in THEMES], separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
       + ';window.__SIG_MARTIN_URL=' + json.dumps(MARTIN_URL) + ';window.__SIG_MARTIN_MS_URL=' + json.dumps(MARTIN_MS_URL) + ';window.__SIG_IMPL=' + json.dumps(IMPL, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/") + ';</script>\n')
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
