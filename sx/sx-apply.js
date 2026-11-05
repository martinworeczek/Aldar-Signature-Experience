/* Aldar Signature Experience Hub — approved submissions.
 *
 * Business-line leads submit new experiences and updates at /sx/; the Group CX reviewer
 * approves them; /api/sx/published returns the approved records. This file turns those
 * records into each line's own data format and applies them to the line's data set.
 *
 * One copy, used in three places:
 *   - the hub page (index.html loads /sx/sx-apply.js and applies records as each data set loads)
 *   - /mcp and /api/sx (Netlify functions import it), so Echo sees exactly what the hub shows
 *   - the build (tools/build_mcp_data.mjs) for the submission form's choices
 * Plain script (no exports): it defines globalThis.SX_APPLY.
 */
(function (root) {
  "use strict";

  var LINES = {
    cp: { g: "CP_DATA", label: "Corporate Plus", short: "Corporate" },
    hp: { g: "HP_DATA", label: "Hospitality Plus", short: "Hospitality" },
    rp: { g: "RP_DATA", label: "Retail Plus", short: "Retail" },
    edu: { g: "EDU_DATA", label: "Education Plus", short: "Education" },
    dev: { g: "DEV_DATA", label: "Development Plus", short: "Development" },
    est: { g: "EST_DATA", label: "Estates Plus", short: "Estates" },
    pp: { g: "PP_DATA", label: "Project Plus", short: "Project Plus" }
  };
  var STAGE_LABEL = { rev: "In Review", impl: "In Implementation", live: "Deployed & Live", dep: "Backlog (2027)", disc: "Discontinued" };
  // the stages each line's hub view can show
  var STAGES = { cp: ["rev", "impl", "dep"], hp: ["rev", "impl", "live", "dep"], rp: ["rev", "impl", "live", "disc"], edu: ["rev", "impl", "live"], dev: ["rev", "impl", "live"], est: ["rev", "impl", "live"], pp: ["live"] };
  var MON = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"];
  var MONL = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

  function str(v) { return v == null ? "" : String(v).trim(); }
  function arr(v) { return Array.isArray(v) ? v.filter(function (x) { return x != null && x !== ""; }) : (v == null || v === "" ? [] : [v]); }
  // "2026-11" -> "nov2026"; anything else -> "tbc"
  function releaseCode(t) { var m = /^(\d{4})-(\d{2})$/.exec(str(t)); return m && +m[2] >= 1 && +m[2] <= 12 ? MON[+m[2] - 1] + m[1] : "tbc"; }
  function when(iso) { var d = iso ? new Date(iso) : new Date(); if (isNaN(d)) d = new Date(); return d.getUTCDate() + " " + MONL[d.getUTCMonth()] + " " + d.getUTCFullYear(); }
  function slug(s) { return str(s).toLowerCase().replace(/&/g, " and ").replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 60) || "experience"; }
  function esc(s) { return str(s).replace(/[<>]/g, ""); } // history is plain text in the hub
  function stageOk(line, s) { return STAGES[line].indexOf(s) >= 0 ? s : STAGES[line][0]; }

  // assets in scope, each { name, live }; nothing is live unless the stage is live
  function assetList(line, D, list, stage) {
    var tiers = {};
    (D.experiences || []).forEach(function (e) { (e.deployedAssets || []).forEach(function (a) { if (a.tier) tiers[a.name] = a.tier; }); });
    var seen = {};
    return arr(list).map(function (a) {
      var name = str(a && a.name != null ? a.name : a); if (!name || seen[name]) return null; seen[name] = 1;
      var o = { name: name, live: stage === "live" && !!(a && a.live) };
      if (line === "edu" && tiers[name]) o.tier = tiers[name];
      return o;
    }).filter(Boolean);
  }
  function hpCells(D, assets) {
    var byName = {}; (D.assetTable || []).forEach(function (a) { byName[a.name] = a.code; });
    var cells = {}; assets.forEach(function (a) { if (byName[a.name]) cells[byName[a.name]] = a.live ? "impl" : "prog"; });
    return cells;
  }
  function setStage(line, e, stage, D) {
    if (line === "cp") { e.track = stage === "rev" ? "new" : stage === "dep" ? "backlog" : "inflight"; return; }
    if (line === "hp") { e.status = { rev: "rev", impl: "prog", live: "impl", dep: "dep" }[stage]; return; }
    if (line === "pp") return;
    e.status = stage;
  }
  function setNote(line, e, note) {
    if (!note) return;
    e.note = note;
    if (line === "hp") e.roadmapNote = note;
    if (line === "est") e.depNotes = note;
    if (line === "cp") { e.audit = e.audit || {}; e.audit.changed = note; }
  }
  function setAssets(line, e, D, assets) {
    if (line === "cp" || line === "pp") return;
    e.deployedAssets = assets;
    if (line === "hp") e.cells = hpCells(D, assets);
  }
  // photos of the experience as implemented, each tagged with its asset
  function implPhotos(rec) {
    return arr((rec.fields || {}).impl_photos).map(function (p) {
      return p && str(p.src) ? { src: str(p.src), asset: str(p.asset) || "At the experience", caption: str(p.caption), when: when(rec.approved_at) } : null;
    }).filter(Boolean);
  }
  function logEntry(rec, text) {
    return { when: when(rec.approved_at), author: LINES[rec.line].label + (rec.lead ? " · " + rec.lead : ""), text: text };
  }

  // a new experience, in the line's own format
  function toNative(rec, D) {
    var line = rec.line, f = rec.fields || {}, stage = stageOk(line, f.stage);
    var assets = assetList(line, D, f.assets, stage);
    var tp = arr(f.touchpoints).map(str).filter(Boolean);
    var note = str(f.note);
    var e = {
      id: rec.exp_id, name: str(f.name), defining: !!f.defining, essence: str(f.essence), narrative: str(f.narrative),
      image: str(f.photo) || undefined, pillar: str(f.pillar) || undefined,
      log: [logEntry(rec, "Submitted by " + (rec.lead || LINES[line].short + " lead") + " and approved by Group CX." + (note ? " " + esc(note) : ""))],
      sx: { id: rec.id, lead: rec.lead || "", approved_at: rec.approved_at, folder_url: str(f.folder_url) || undefined }
    };
    if (line !== "cp" && line !== "pp") e.release = releaseCode(f.target);
    if (line === "cp") {
      e.phase = str(f.journey) || "ph3"; e.delivery = /^\d{4}/.test(str(f.target)) ? +str(f.target).slice(0, 4) : (stage === "dep" ? 2027 : 2026);
      e.capex = str(f.capex) || "Medium"; e.evp = str(f.evp) || "Engagement";
      e.audit = { insight: "", introduced: str(f.essence), changed: note, next: "" };
      e.existing = []; e.elevated = tp;
      if (str(f.segment)) e.segment = str(f.segment);
    } else if (line === "hp") {
      e.group = str(f.group) || "Portfolio-wide"; e.journey = str(f.journey) || "stay"; e.photos = []; e.note = note; e.roadmapNote = note;
    } else if (line === "rp") {
      e.type = str(f.type) || "Hospitality"; e.journey = str(f.journey) || "duringshop"; e.segment = str(f.segment) || "both"; e.note = note;
    } else if (line === "edu") {
      e.schoolTiers = arr(f.tiers); e.segment = str(f.segment) || e.schoolTiers.join(" · ") || "To be defined once scope is finalised"; e.notInScope = []; e.note = note;
    } else if (line === "dev") {
      e.imageKey = e.id; e.type = str(f.type) || "new"; e.seasonal = str(f.cadence) || "Permanent"; e.segment = str(f.segment) || "General- All Customers"; e.tp = tp; e.notInScope = []; e.note = note;
    } else if (line === "est") {
      var vert = arr(f.verticals); if (!vert.length) vert = ["chs"];
      var jt = vert[0] === "chs" ? "chs" : "pm";
      var J = (jt === "chs" ? D.chsJourney : D.pmJourney) || [];
      var j = J.filter(function (x) { return x.id === str(f.journey); })[0] || J[0] || { id: "", name: "" };
      e.vertical = vert; e.journeyType = jt; e.journeyId = j.id; e.journey = j.name; e.segment = arr(f.segment);
      e.moment = str(f.moment); e.customerBenefit = str(f.customer_benefit); e.aldarBenefit = str(f.aldar_benefit); e.tp = tp; e.notInScope = []; e.depNotes = note;
    } else if (line === "pp") {
      e.type = str(f.type) || "all"; e.moment = str(f.moment); e.customerBenefit = str(f.customer_benefit); e.aldarBenefit = str(f.aldar_benefit); e.tp = tp;
    }
    if ((line === "rp" || line === "dev" || line === "est" || line === "edu") && (f.moment || f.customer_benefit)) {
      if (!e.moment) e.moment = str(f.moment); if (!e.customerBenefit) e.customerBenefit = str(f.customer_benefit); if (!e.aldarBenefit) e.aldarBenefit = str(f.aldar_benefit);
    }
    var ip0 = implPhotos(rec); if (ip0.length) e.photos = ip0;
    setStage(line, e, stage, D);
    setAssets(line, e, D, assets);
    Object.keys(e).forEach(function (k) { if (e[k] === undefined) delete e[k]; });
    return e;
  }

  // the current stage key of a native experience (same rules as the hub's baseStatus)
  function stageOf(line, e, D) {
    if (line === "hp") { var c = e.cells || {}; if (e.status === "dep" || e.status === "rev") return e.status; return (e.status === "impl" || Object.keys(c).some(function (k) { return c[k] === "impl"; })) ? "live" : "impl"; }
    if (line === "rp") { if (e.status === "disc" || e.status === "rev") return e.status; return (e.status === "live" || (e.deployedAssets || []).some(function (x) { return x.live; })) ? "live" : "impl"; }
    if (line === "cp") return e.track === "new" ? "rev" : e.track === "backlog" ? "dep" : "impl";
    if (line === "pp") return "live";
    if (line === "edu") return (e.status === "live" || e.status === "completed") ? "live" : (["rev", "review", "notstarted"].indexOf(e.status) >= 0 ? "rev" : "impl");
    return e.status === "live" ? "live" : (e.status === "rev" || e.status === "review") ? "rev" : "impl";
  }

  // an approved update to an existing experience
  function applyUpdate(rec, e, D) {
    var line = rec.line, f = rec.fields || {}, parts = [];
    var stage = f.stage ? stageOk(line, f.stage) : stageOf(line, e, D);
    if (f.stage && stage !== stageOf(line, e, D)) { setStage(line, e, stage, D); parts.push("Stage: " + STAGE_LABEL[stage].replace(" & ", " and ") + "."); }
    if (f.target !== undefined && f.target !== null && line !== "cp" && line !== "pp") {
      var rc = releaseCode(f.target); if (rc !== e.release) { e.release = rc; parts.push("Target go-live: " + (rc === "tbc" ? "TBC" : MONL[MON.indexOf(rc.slice(0, 3))] + " " + rc.slice(3)) + "."); }
    }
    if (line === "cp" && /^\d{4}/.test(str(f.target))) e.delivery = +str(f.target).slice(0, 4);
    if (Array.isArray(f.assets)) {
      var a = assetList(line, D, f.assets, stage);
      setAssets(line, e, D, a);
      var live = a.filter(function (x) { return x.live; }).map(function (x) { return x.name; });
      if (live.length) parts.push("Live at: " + live.join(", ") + ".");
    } else if (stage !== "live" && line !== "cp" && line !== "pp") {
      // leaving "live": nothing stays marked live
      (e.deployedAssets || []).forEach(function (x) { x.live = false; });
      if (line === "hp") e.cells = hpCells(D, e.deployedAssets || []);
    }
    if (str(f.essence)) e.essence = str(f.essence);
    if (str(f.narrative)) e.narrative = str(f.narrative);
    if (str(f.photo)) { e.image = str(f.photo); e.sxPhoto = e.image; }
    var ip = implPhotos(rec);
    if (ip.length) { e.photos = (Array.isArray(e.photos) ? e.photos : []).concat(ip); parts.push(ip.length + (ip.length === 1 ? " photo" : " photos") + " from the live experience."); }
    var note = str(f.note);
    setNote(line, e, note);
    e.log = (e.log || []).concat([logEntry(rec, esc((note ? note + " " : "") + parts.join(" ")).trim() || "Updated via the hub.")]);
    e.sx_updated = rec.approved_at;
  }

  // apply every approved record for one line to its data set (idempotent per data set object)
  function apply(line, D, records, W) {
    if (!D || !Array.isArray(D.experiences) || D.__sx) return D;
    var list = (records || []).filter(function (r) { return r && r.line === line; })
      .sort(function (a, b) { return String(a.approved_at).localeCompare(String(b.approved_at)); });
    list.forEach(function (rec) {
      try {
        if (rec.kind === "new") {
          if (D.experiences.some(function (x) { return x.id === rec.exp_id; })) return;
          var e = toNative(rec, D);
          D.experiences.push(e);
          // The photo rides on e.image. Never create or touch the line photo maps (HP_IMG,
          // DEV_IMG, EST_IMG) here: this runs before they load, and a map that already exists
          // tells the hub the line's photographs are in memory, so the real ones never load.
        } else if (rec.kind === "update") {
          var t = D.experiences.filter(function (x) { return x.id === rec.exp_id; })[0];
          if (t) applyUpdate(rec, t, D); // a new photo is set on t.image, which the photo loaders never overwrite
        }
      } catch (err) { if (typeof console !== "undefined") console.warn("[sx] could not apply", rec && rec.id, err); }
    });
    try { Object.defineProperty(D, "__sx", { value: true, enumerable: false }); } catch (e) { /* frozen */ }
    return D;
  }

  // choices for the submission form, per line
  function options(W) {
    var out = {};
    Object.keys(LINES).forEach(function (line) {
      var D = W[LINES[line].g]; if (!D) return;
      var ex = D.experiences || [];
      var uniq = function (f) { var s = {}; ex.forEach(function (e) { arr(f(e)).forEach(function (v) { if (typeof v === "string" && v) s[v] = 1; }); }); return Object.keys(s); };
      var o = { label: LINES[line].label, short: LINES[line].short, stages: STAGES[line].map(function (k) { return { key: k, label: STAGE_LABEL[k] }; }) };
      o.pillars = (D.pillars || []).map(function (p) { return { id: p.id, name: p.name }; });
      if (line === "cp") o.journeys = (D.phases || []).map(function (p) { return { id: p.id, name: p.name }; });
      if (line === "hp") o.journeys = [{ id: "pre", name: "Pre-arrival & Arrival" }, { id: "stay", name: "During Stay" }, { id: "post", name: "Check-Out & Post-Departure" }];
      if (line === "rp") o.journeys = Object.keys(D.journeys || {}).map(function (k) { return { id: k, name: D.journeys[k].label, pillar: D.journeys[k].pillar }; });
      if (line === "est") o.journeys = (D.chsJourney || []).map(function (j) { return { id: j.id, name: j.name, group: "chs" }; }).concat((D.pmJourney || []).map(function (j) { return { id: j.id, name: j.name, group: "pm" }; }));
      if (line === "rp") o.types = uniq(function (e) { return e.type; }).map(function (t) { return { id: t, label: t }; });
      if (line === "dev" || line === "pp") o.types = Object.keys(D.tracks || {}).map(function (k) { return { id: k, label: D.tracks[k].label }; });
      if (line === "cp") { o.capex = Object.keys(D.capex || {}); o.evp = uniq(function (e) { return e.evp; }); }
      if (line === "hp") o.groups = uniq(function (e) { return e.group; });
      if (line === "dev") o.cadence = uniq(function (e) { return e.seasonal; });
      if (line === "edu") o.tiers = D.schoolTiers || [];
      if (line === "est") o.verticals = (D.verticals || []).map(function (v) { return { id: v.id, label: v.label, full: v.full }; });
      o.segments = line === "rp" ? [{ id: "both", label: "Mainstream & luxury" }, { id: "luxury", label: "Luxury" }] : uniq(function (e) { return e.segment; }).map(function (s) { return { id: s, label: s }; });
      o.segment_multi = line === "est";
      if (line === "hp") o.assets = (D.assetTable || []).map(function (a) { return { name: a.name, group: a.type }; });
      else if (line === "rp") o.assets = (D.assets || []).map(function (a) { return { name: a.id, group: a.segment }; });
      else if (line !== "cp" && line !== "pp") o.assets = uniq(function (e) { return (e.deployedAssets || []).map(function (a) { return a.name; }); }).filter(function (n) { return !/:$/.test(n); }).map(function (n) { return { name: n }; });
      else o.assets = [];
      o.has = { target: line !== "pp", assets: line !== "cp" && line !== "pp", touchpoints: ["cp", "dev", "est", "pp"].indexOf(line) >= 0, benefits: ["est", "pp"].indexOf(line) >= 0 };
      out[line] = o;
    });
    return out;
  }

  root.SX_APPLY = { LINES: LINES, STAGES: STAGES, STAGE_LABEL: STAGE_LABEL, apply: apply, toNative: toNative, stageOf: stageOf, options: options, releaseCode: releaseCode, slug: slug };
})(typeof window !== "undefined" ? window : globalThis);
