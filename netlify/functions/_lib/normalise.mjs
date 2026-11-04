// Normalise the hub's native data sets (the window globals index.html defines) into the
// MCP dataset: one experience schema across the seven lines, using the hub's own status rules.
// Used at build time (tools/build_mcp_data.mjs) and at request time by /mcp, which re-applies
// approved hub submissions (sx/sx-apply.js) to the native data before normalising.
export function buildDataset(W, full = [], SITE = "https://aldar-signature-experience.netlify.app") {
  // ---- helpers ----
  const abs = (u) => (u && typeof u === "string" && u.startsWith("/")) ? SITE + u : (u || null);
  const strip = (h) => String(h || "").replace(/<li>/gi, "\n• ").replace(/<br\s*\/?>/gi, "\n").replace(/<[^>]+>/g, "").replace(/&nbsp;/g, " ").replace(/&amp;/g, "&").replace(/[ \t]+/g, " ").trim();
  const MO = { jan: 1, feb: 2, mar: 3, apr: 4, may: 5, jun: 6, jul: 7, aug: 8, sep: 9, sept: 9, oct: 10, nov: 11, dec: 12 };
  const MOL = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  // same rules as the hub's _relLabel, plus a sortable YYYY-MM
  function release(code) {
    if (!code) return { label: "TBC", sort: null };
    const c = String(code).toLowerCase().replace(/\s+/g, "");
    if (c === "tbc") return { label: "TBC", sort: null };
    if (c === "na") return { label: "—", sort: null };
    let m = /^q([1-4])-(\d{4})$/.exec(c); if (m) return { label: "Q" + m[1] + " " + m[2], sort: m[2] + "-" + String(+m[1] * 3).padStart(2, "0") };
    m = /^([a-z]{3,4})(\d{4})$/.exec(c); if (m && MO[m[1]]) return { label: MOL[MO[m[1]]] + " " + m[2], sort: m[2] + "-" + String(MO[m[1]]).padStart(2, "0") };
    if (/^\d{4}$/.test(c)) return { label: c, sort: c + "-12" };
    return { label: ((W.HP_DATA.relLabels || {})[code]) || "TBC", sort: null };
  }
  const STAGE = { rev: "In Review", impl: "In Implementation", live: "Deployed & Live", audited: "Audited", dep: "Backlog (2027)", disc: "Discontinued" };
  // the hub's baseStatus, per line
  function stageKey(e, line) {
    if (line === "hp") {
      const cells = e.cells || {}; const scoped = W.HP_DATA.assetTable.filter((a) => cells[a.code]);
      if (e.status === "dep") return "dep"; if (e.status === "rev") return "rev";
      if (e.status === "impl" || scoped.some((a) => cells[a.code] === "impl")) return "live"; return "impl";
    }
    if (line === "rp") { if (e.status === "disc") return "disc"; if (e.status === "rev") return "rev"; if (e.status === "live" || (e.deployedAssets || []).some((x) => x.live)) return "live"; return "impl"; }
    if (line === "edu") { if (e.status === "live" || e.status === "completed") return "live"; if (["rev", "review", "notstarted"].includes(e.status)) return "rev"; return "impl"; }
    if (line === "cp") { if (e.track === "new") return "rev"; if (e.track === "backlog") return "dep"; return "impl"; }
    if (line === "pp") return "live";
    if (line === "dev" || line === "est") { if (e.status === "live") return "live"; if (e.status === "rev" || e.status === "review") return "rev"; return "impl"; }
    return "rev";
  }
  const audited = (a) => a && (a.enps != null || a.csat != null || (a.summary && String(a.summary).trim()));

  const LINES = {
    cp: { label: "Corporate Plus", data: W.CP_DATA, img: (e) => e.image },
    hp: { label: "Hospitality Plus", data: W.HP_DATA, img: (e) => e.sxPhoto || (W.HP_IMG || {})[e.id] || e.image },
    rp: { label: "Retail Plus", data: W.RP_DATA, img: (e) => e.image },
    edu: { label: "Education Plus", data: W.EDU_DATA, img: (e) => e.image },
    dev: { label: "Development Plus", data: W.DEV_DATA, img: (e) => e.sxPhoto || (W.DEV_IMG || {})[e.imageKey] || e.image },
    est: { label: "Estates Plus", data: W.EST_DATA, img: (e) => e.sxPhoto || (W.EST_IMG || {})[e.id] || e.image },
    pp: { label: "Project Plus", data: W.PP_DATA, img: (e) => e.image },
  };
  const HP_J = { pre: "Pre-arrival & Arrival", stay: "During Stay", post: "Check-Out & Post-Departure" };

  // asset folders (SharePoint) by experience id
  const folders = {};
  for (const lib of Object.values(W.SIG_ASSETS || {})) for (const [id, r] of Object.entries(lib.map || {})) {
    folders[id] = { library: lib.label, folder: r.folder, url: r.url, photographs: r.img || 0, films: r.vid || 0, documents: r.doc || 0, files: r.files || [] };
  }
  // Idea Exchange: moves an experience embodies, and benchmarks that informed it
  const movesByKey = Object.fromEntries(W.IX_ENGINE.MOVES.map((m) => [m.k, m]));
  const benchByExp = {};
  for (const b of W.BM_LINKS) for (const id of b.inf || []) (benchByExp[id] = benchByExp[id] || []).push(b.id);

  function journeyOf(e, line, D) {
    if (line === "hp") return HP_J[e.journey] || null;
    if (line === "rp") return ((D.journeys || {})[e.journey] || {}).label || null;
    if (line === "cp") return ((D.phases || []).find((p) => p.id === e.phase) || {}).name || null;
    if (line === "est") return e.journey || null;
    return null;
  }
  function deployment(e, line, D, live) {
    if (line === "hp") {
      const cells = e.cells || {};
      const inScope = D.assetTable.filter((a) => cells[a.code]).map((a) => ({ name: a.name, type: a.type, live: cells[a.code] === "impl" }));
      return { assets: inScope, in_scope: inScope.length, live: inScope.filter((a) => a.live).length, out_of_scope: D.assetTable.filter((a) => !cells[a.code]).map((a) => a.name) };
    }
    if (line === "cp") return { assets: [{ name: "Aldar HQ", live }], in_scope: 1, live: live ? 1 : 0, out_of_scope: [] };
    const a = (e.deployedAssets || []).map((x) => ({ name: x.name, live: !!x.live, ...(x.tier ? { tier: x.tier } : {}) }));
    return { assets: a, in_scope: a.length, live: a.filter((x) => x.live).length, out_of_scope: (e.notInScope || []).map((x) => x.name || x) };
  }

  const experiences = [];
  for (const [line, L] of Object.entries(LINES)) {
    const D = L.data;
    for (const e of D.experiences) {
      let k = stageKey(e, line);
      const au = e.seedAudit || null;
      if (k === "live" && audited(au)) k = "audited";
      const rel = release(e.release);
      const target = (k === "live" || k === "audited") ? "Already live" : k === "dep" ? "Parked to 2027" : k === "disc" ? "Discontinued" : rel.label;
      const pillar = ((D.pillars || []).find((p) => p.id === e.pillar) || {}).name || null;
      const dep = deployment(e, line, D, k === "live" || k === "audited");
      const type = line === "dev" || line === "pp" ? (((D.tracks || {})[e.type] || {}).label || e.type || null) : (line === "rp" ? e.type || null : null);
      experiences.push({
        id: e.id, line, line_label: L.label, name: e.name, defining: !!e.defining,
        stage: STAGE[k], stage_key: k, pillar, journey_stage: journeyOf(e, line, D),
        target_go_live: target, target_sort: (k === "rev" || k === "impl") ? rel.sort : null,
        essence: e.essence || "", narrative: e.narrative || "",
        latest_note: strip(e.note || e.roadmapNote || e.depNotes || ""),
        scope_group: e.group || null, segment: Array.isArray(e.segment) ? e.segment.join(", ") : (e.segment || null),
        type, cadence: e.seasonal || null,
        verticals: line === "est" ? (e.vertical || []).map((v) => ((D.verticals || []).find((x) => x.id === v) || {}).label || v) : undefined,
        school_tiers: line === "edu" ? e.schoolTiers || [] : undefined,
        capex: line === "cp" ? e.capex : undefined, evp: line === "cp" ? e.evp : undefined,
        moment_of_truth: e.moment || undefined, customer_benefit: e.customerBenefit || undefined, aldar_benefit: e.aldarBenefit || undefined,
        touchpoints: e.tp || (line === "cp" ? [].concat(e.existing || [], e.elevated || []) : undefined),
        programme_story: line === "cp" ? e.audit || undefined : undefined,
        deployment: dep,
        audit: audited(au) ? { enps: au.enps ?? null, csat: au.csat ?? null, summary: au.summary || "", when: au.when || "", report: au.report || "" } : null,
        history: (e.log || []).map((x) => ({ when: x.when, author: x.author || L.label, text: strip(x.text) })),
        image_url: abs(L.img(e)),
      implementation_photos: [].concat(e.photos || [], (W.SIG_IMPL || {})[e.id] || []).map((x) => (typeof x === "string" ? { src: x } : x)).filter((x) => x && x.src).map((x) => ({ asset: x.asset || null, url: abs(x.src), caption: x.caption || null, when: x.when || null })),
        asset_folder: folders[e.id] || (e.sx && e.sx.folder_url ? { folder: "SharePoint", url: e.sx.folder_url } : null),
        ...(e.sx ? { submitted_via_hub: { lead: e.sx.lead, approved_at: e.sx.approved_at } } : {}),
        ...(e.sx_updated ? { last_hub_update: e.sx_updated } : {}),
        idea_moves: (W.EXP_MOVES || {})[e.id] ? W.EXP_MOVES[e.id].map((m) => ({ key: m, label: (movesByKey[m] || {}).label || m })) : [],
        informed_by_benchmarks: benchByExp[e.id] || [],
      });
    }
  }
  for (const x of experiences) for (const k of Object.keys(x)) if (x[k] === undefined) delete x[k];

  // ---- programmes (one per line) ----
  const programmes = Object.entries(LINES).map(([line, L]) => {
    const D = L.data, keep = {};
    for (const k of ["programme", "vision", "operatingModel", "tiers", "principles", "research", "voc", "pillars", "phases", "journeys", "chsJourney", "pmJourney", "verticals", "segments", "schoolTiers", "tracks", "capex"]) if (D[k] !== undefined) keep[k] = D[k];
    if (line === "hp") keep.properties = D.assetTable.map((a) => ({ name: a.name, type: a.type }));
    if (line === "rp") keep.malls = D.assets;
    return { line, line_label: L.label, ...keep, experience_count: experiences.filter((x) => x.line === line).length };
  });

  // ---- benchmarks: the gallery's full records, joined with the link index ----
  const fullById = Object.fromEntries(full.map((b) => [b.id, b]));
  const LN = { cp: "Corporate", hp: "Hospitality", rp: "Retail", edu: "Education", dev: "Development", est: "Estates", pp: "Project Plus" };
  const bmImg = Object.assign({}, W.BM_IMAGES_A, W.BM_IMAGES_B, W.BM_IMAGES_C, W.BM_IMAGES_D);
  const benchmarks = W.BM_LINKS.map((b) => {
    const f = fullById[b.id] || {};
    const r = { id: b.id, title: b.t, brand: b.br, industry: b.ind, line: b.ln, line_label: LN[b.ln] || b.ln, pillar: b.pil, themes: b.th || [], summary: b.s, informs_experiences: b.inf || [], image_url: abs(bmImg[b.id]) };
    for (const k of ["lead", "why", "transfer", "moment", "source", "added"]) if (f[k] != null && f[k] !== "") r[k === "transfer" ? "transfer_to_lines" : k] = f[k];
    return r;
  });

  // ---- CX Time ----
  const cx_time = W.AT_DATA.editions.map((ed) => ({
    edition: ed.n, date: ed.date,
    stories: ed.items.map((s) => ({
      id: s.id, edition: ed.n, format: s.format, signal_of_the_week: !!s.lead, tag: s.tag, source: s.source, source_url: s.sourceUrl, published: s.published, duration: s.meta || null,
      title: s.title, dek: s.dek, summary: s.summary || [], key_insights: s.insights || s.keyInsights || [], why_it_matters: s.why, quote: s.excerpt || null,
      relevant_lines: s.lines || [], signature_experience_idea: s.opps || (s.oppTitle ? [{ lines: s.lines || [], title: s.oppTitle, text: s.oppText }] : []),
      speakers: s.speakers || [], transcript_url: s.transcriptUrl || null, insight_type: s.insight || s.insightType || null, related: s.related || [],
      image_url: abs((W.AT_IMG || {})[s.id]),
    })),
  }));

  // ---- Idea Exchange ----
  const idea_moves = W.IX_ENGINE.MOVES.map((m) => ({
    key: m.k, label: m.label, journey_bucket: (W.IX_ENGINE.BUCKETS.find((b) => b.k === m.b) || {}).label || m.b, description: m.blurb,
    becomes_by_line: Object.fromEntries(Object.entries(m.becomes || {}).map(([k, v]) => [LINES[k] ? LINES[k].label : k, v])),
    experiences: experiences.filter((x) => x.idea_moves.some((y) => y.key === m.k)).map((x) => ({ id: x.id, name: x.name, line: x.line_label })),
  }));

  const count = (arr, f) => arr.reduce((o, x) => { const k = f(x) ?? "—"; o[k] = (o[k] || 0) + 1; return o; }, {});
  const dataset = {
    generated_at: new Date().toISOString(), site: SITE,
    data_stamps: Object.fromEntries(Object.entries(LINES).map(([k, L]) => [L.label, (L.data.programme || {}).updated || L.data.dataStamp || null])),
    counts: {
      experiences: experiences.length, by_line: count(experiences, (x) => x.line_label), by_stage: count(experiences, (x) => x.stage),
      benchmarks: benchmarks.length, cx_time_editions: cx_time.length, cx_time_stories: cx_time.reduce((n, e) => n + e.stories.length, 0),
      idea_moves: idea_moves.length, asset_folders: Object.keys(folders).length,
    },
    programmes, experiences, benchmarks, cx_time, idea_moves,
  };
  return dataset;
}

// The globals the dataset is built from (what the build snapshots for /mcp).
export const NATIVE_GLOBALS = ["CP_DATA", "HP_DATA", "RP_DATA", "EDU_DATA", "DEV_DATA", "EST_DATA", "PP_DATA", "HP_IMG", "DEV_IMG", "EST_IMG", "SIG_ASSETS", "IX_ENGINE", "EXP_MOVES", "BM_LINKS", "BM_IMAGES_A", "BM_IMAGES_B", "BM_IMAGES_C", "BM_IMAGES_D", "AT_DATA", "AT_IMG"];
