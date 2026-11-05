// Aldar Signature Experience Hub — MCP tools over the site dataset.
// Pure functions: (dataset, args) -> result. The /mcp function wires them to JSON-RPC.
import FEATURES from "../../../features.json" with { type: "json" };
import { compareRead, CompareError } from "./compare-read.mjs";

const norm = (s) => String(s ?? "").toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, "").trim();
const LINE_ALIASES = {
  cp: ["cp", "corporate", "corporate plus"], hp: ["hp", "hospitality", "hospitality plus", "hotels"],
  rp: ["rp", "retail", "retail plus", "malls"], edu: ["edu", "education", "education plus", "schools"],
  dev: ["dev", "development", "development plus"], est: ["est", "estates", "estates plus", "pm & leasing", "community"],
  pp: ["pp", "project plus", "project", "projects"],
};
export function lineKey(v) {
  if (v == null || v === "") return null;
  const n = norm(v);
  for (const [k, al] of Object.entries(LINE_ALIASES)) if (al.includes(n)) {
    if (k === "pp" && FEATURES.project_plus === false) throw new ToolError("Project Plus is not part of the hub right now. Use one of: Corporate, Hospitality, Retail, Education, Development, Estates.");
    return k;
  }
  throw new ToolError(`Unknown business line "${v}". Use one of: Corporate, Hospitality, Retail, Education, Development, Estates${FEATURES.project_plus === false ? "" : ", Project Plus"}.`);
}
export class ToolError extends Error {}

const STAGES = ["In Review", "In Implementation", "Deployed & Live", "Audited", "Backlog (2027)", "Discontinued"];
function stageMatch(v) {
  const n = norm(v);
  const hit = STAGES.find((s) => norm(s) === n || norm(s).startsWith(n) || (n === "live" && s === "Deployed & Live") || (n === "backlog" && s.startsWith("Backlog")) || (n === "parked" && s.startsWith("Backlog")));
  if (!hit) throw new ToolError(`Unknown stage "${v}". Use one of: ${STAGES.join(", ")}.`);
  return hit;
}
const has = (hay, needle) => norm(hay).includes(norm(needle));
const words = (q) => norm(q).split(/[^a-z0-9&]+/).filter((w) => w.length > 1);
// relevance: matched query words weighted by rarity across the corpus (IDF), phrase bonus
const DF = new WeakMap();
function idf(corpus, txt) {
  let m = DF.get(corpus);
  if (!m) { m = { n: corpus.length, df: {} }; for (const x of corpus) for (const w of new Set(words(txt(x)))) m.df[w] = (m.df[w] || 0) + 1; DF.set(corpus, m); }
  return (w) => Math.log(1 + m.n / (1 + (m.df[w] || 0)));
}
function scorer(corpus, txt, q) {
  const W = idf(corpus, txt), qs = [...new Set(words(q))], phrase = norm(q);
  return (x) => {
    const t = norm(txt(x)); let s = 0, hit = 0;
    for (const w of qs) if (t.includes(w)) { s += W(w); hit++; }
    if (!hit) return 0;
    if (qs.length > 1 && t.includes(phrase)) s += 3;
    return s * (hit / qs.length);
  };
}
const rank = (corpus, txt, q) => { const f = scorer(corpus, txt, q); return corpus.map((x) => [f(x), x]).filter(([v]) => v > 0).sort((a, b) => b[0] - a[0]); };
const page = (arr, limit, offset) => {
  const L = Math.max(1, Math.min(Number(limit) || 25, 200)), O = Math.max(0, Number(offset) || 0);
  return { total: arr.length, offset: O, limit: L, returned: Math.min(L, Math.max(0, arr.length - O)), items: arr.slice(O, O + L) };
};

// ---------------- experiences ----------------
const expText = (x) => [x.name, x.essence, x.narrative, x.latest_note, x.pillar, x.journey_stage, x.scope_group, x.segment, x.type,
  (x.touchpoints || []).join(" "), x.customer_benefit, x.aldar_benefit, x.moment_of_truth, (x.deployment?.assets || []).map((a) => a.name).join(" "),
  (x.idea_moves || []).map((m) => m.label).join(" ")].join(" ");
const expRow = (x) => ({
  id: x.id, name: x.name, line: x.line_label, stage: x.stage, defining: x.defining, pillar: x.pillar, journey_stage: x.journey_stage,
  target_go_live: x.target_go_live, essence: x.essence,
  deployment: x.deployment ? `${x.deployment.live} of ${x.deployment.in_scope} assets live` : null,
  properties: (x.deployment?.assets || []).map((a) => a.name + (a.live ? " (live)" : "")),
  latest_note: x.latest_note ? x.latest_note.slice(0, 280) : "",
});
function filterExperiences(D, a = {}) {
  let r = D.experiences;
  const lk = lineKey(a.line);
  if (lk) r = r.filter((x) => x.line === lk);
  if (a.stage) { const st = [].concat(a.stage).map(stageMatch); r = r.filter((x) => st.includes(x.stage)); }
  if (a.defining != null) r = r.filter((x) => !!x.defining === !!a.defining);
  if (a.pillar) r = r.filter((x) => has(x.pillar, a.pillar));
  if (a.journey_stage) r = r.filter((x) => has(x.journey_stage, a.journey_stage));
  if (a.property) r = r.filter((x) => (x.deployment?.assets || []).some((p) => has(p.name, a.property) || has(p.type, a.property)) || has(x.scope_group, a.property));
  if (a.live_at) r = r.filter((x) => (x.deployment?.assets || []).some((p) => p.live && (has(p.name, a.live_at) || has(p.type, a.live_at))));
  if (a.target_from) r = r.filter((x) => x.target_sort && x.target_sort >= a.target_from);
  if (a.target_to) r = r.filter((x) => x.target_sort && x.target_sort <= a.target_to);
  if (a.idea_move) r = r.filter((x) => (x.idea_moves || []).some((m) => has(m.key, a.idea_move) || has(m.label, a.idea_move)));
  if (a.query) r = rank(r, expText, a.query).map(([, x]) => x);
  const sort = a.sort || (a.query ? "relevance" : "line");
  if (sort === "target") r = [...r].sort((p, q) => (p.target_sort || "9999").localeCompare(q.target_sort || "9999"));
  else if (sort === "name") r = [...r].sort((p, q) => p.name.localeCompare(q.name));
  return r;
}
function findExperience(D, id) {
  const n = norm(id);
  return D.experiences.find((x) => norm(x.id) === n) || D.experiences.find((x) => norm(x.name) === n)
    || D.experiences.find((x) => norm(x.name).includes(n));
}

// ---------------- other categories ----------------
const bmText = (b) => [b.title, b.brand, b.industry, b.summary, b.lead, (b.themes || []).join(" "), (b.why || []).map((w) => (w.head || "") + " " + (w.body || "")).join(" "), (b.transfer_to_lines || []).map((t) => t.how).join(" ")].join(" ");
const bmRow = (b) => ({ id: b.id, title: b.title, brand: b.brand, industry: b.industry, line: b.line_label, pillar: b.pillar, themes: b.themes, summary: b.summary, informs_experiences: b.informs_experiences });
const storyText = (s) => [s.title, s.dek, (s.summary || []).join(" "), s.why_it_matters, s.tag, s.source, (s.relevant_lines || []).join(" "), (s.signature_experience_idea || []).map((o) => o.title + " " + o.text).join(" ")].join(" ");
const storyRow = (s) => ({ id: s.id, edition: s.edition, format: s.format, signal_of_the_week: s.signal_of_the_week, tag: s.tag, source: s.source, published: s.published, duration: s.duration, title: s.title, dek: s.dek, why_it_matters: s.why_it_matters, relevant_lines: s.relevant_lines, source_url: s.source_url });
const allStories = (D) => D.cx_time.flatMap((e) => e.stories);

// ---------------- customer stories ----------------
const CS_LINE = { cp: "Corporate", hp: "Hospitality", rp: "Retail", edu: "Education", dev: "Development", est: "Estates", pp: "Project Plus" };
const csText = (c) => [c.title, c.place, c.category, c.line_label, c.story, c.what_made_it_memorable, c.colleagues, c.experience?.name].join(" ");
const csRow = (c) => ({ id: c.id, title: c.title, line: c.line_label, place: c.place, what_made_it_memorable: c.what_made_it_memorable, experience: c.experience ? { id: c.experience.id, name: c.experience.name, link_status: c.experience.link_status } : null });
const csAll = (D) => D.customer_stories || [];
function findCustomerStory(D, id) {
  const n = norm(id), all = csAll(D);
  return all.find((c) => norm(c.id) === n) || all.find((c) => norm(c.title) === n) || all.find((c) => norm(c.title).includes(n));
}

const count = (arr, f) => {
  const o = {};
  for (const x of arr) for (const k of [].concat(f(x) ?? "—")) o[k] = (o[k] || 0) + 1;
  return Object.fromEntries(Object.entries(o).sort((a, b) => b[1] - a[1]));
};

// ---------------- tools ----------------
const LINE_ARG = { type: "string", description: "Business line: Corporate, Hospitality, Retail, Education, Development, Estates or Project Plus (keys cp/hp/rp/edu/dev/est/pp also work)." };
const EXP_FILTERS = {
  line: LINE_ARG,
  stage: { description: "Lifecycle stage, or a list of stages: In Review, In Implementation, Deployed & Live, Audited, Backlog (2027), Discontinued. 'live' and 'backlog' are accepted.", anyOf: [{ type: "string" }, { type: "array", items: { type: "string" } }] },
  defining: { type: "boolean", description: "true = only flagship (defining) experiences; false = only non-defining." },
  pillar: { type: "string", description: "Pillar name or part of it (e.g. 'I Feel Seen', 'belonging')." },
  journey_stage: { type: "string", description: "Journey stage / phase (e.g. 'During Stay', 'Onboarding', 'Move-in')." },
  property: { type: "string", description: "Asset, property, mall, school or asset type in the deployment scope (e.g. 'W Hotel', 'Yas Mall', 'Beach Club')." },
  live_at: { type: "string", description: "Only experiences already live at this asset/property/type." },
  target_from: { type: "string", description: "Earliest target go-live, YYYY-MM (only In Review / In Implementation items have targets)." },
  target_to: { type: "string", description: "Latest target go-live, YYYY-MM." },
  idea_move: { type: "string", description: "Idea Exchange move key or label the experience embodies (e.g. 'greet', 'A named greeting ritual')." },
  query: { type: "string", description: "Free text matched against name, essence, narrative, notes, touchpoints and properties." },
};
const PAGING = { limit: { type: "integer", description: "Max items (1–200, default 25)." }, offset: { type: "integer", description: "Items to skip, for paging." } };

export const TOOLS = [
  {
    name: "get_overview",
    title: "Hub overview",
    description: "Start here. Describes every data category the Aldar Signature Experience Hub holds (signature experiences across 7 business lines, programmes, deployment, benchmarks, CX Times, Idea Exchange, SharePoint asset folders), with live counts, data freshness and which tool answers which question.",
    inputSchema: { type: "object", properties: {} },
    run: (D) => ({
      site: D.site, generated_at: D.generated_at, data_stamps: D.data_stamps, counts: D.counts,
      business_lines: D.programmes.map((p) => ({ key: p.line, name: p.line_label, experiences: p.experience_count, pillars: (p.pillars || []).map((x) => x.name) })),
      categories: {
        signature_experiences: "Every signature experience in every line: stage, flagship flag, pillar, journey stage, target go-live, essence and narrative, latest note and dated history, deployment by asset, audit scores, photo, SharePoint folder, Idea Exchange moves and the benchmarks that informed it. Tools: list_experiences, get_experience, portfolio_breakdown.",
        programmes: "Each line's programme definition: vision, pillars, journeys/phases, properties or assets, segments, tiers, research. Tool: get_programme.",
        deployment: "Which assets each experience is in scope for and live at (hotels, malls, schools, communities, HQ). Tools: list_experiences (property / live_at filters), portfolio_breakdown (group_by property).",
        benchmarks: "208 global CX reference cases (brand, industry, why it works, how it transfers to Aldar lines, which Aldar experiences it informed). Tools: list_benchmarks, get_benchmark.",
        cx_time: "Aldar CX Times editions: curated articles, videos and podcasts with AI summary, why it matters to Aldar and a suggested signature experience. Tools: list_cx_time, get_cx_time_story.",
        idea_exchange: "26 transferable experience moves, what each becomes in every line, and the experiences that embody it. Tool: get_idea_moves.",
        customer_stories: "Customer Stories: short anecdotes, told by the colleagues who delivered them, of how a signature experience was lived by a real customer (title, line, place, the story, what made it memorable, colleagues). Some are linked to the experience they express: confirmed, or proposed and awaiting a line owner's check. Tools: list_customer_stories, get_customer_story; get_experience also returns an experience's stories.",
        search: "Free-text search across all categories at once. Tool: search.",
      },
      notes: [
        "Stages follow the hub: In Review → In Implementation → Deployed & Live → Audited; Backlog (2027) and Discontinued sit outside the flow.",
        "Target go-live is month/quarter granularity; live items read 'Already live'.",
        "Saved boards and audits recorded in a browser are browser-local and are not in this dataset.",
      ],
    }),
  },
  {
    name: "search",
    title: "Search everything",
    description: "Free-text search across signature experiences, customer stories, benchmarks, CX Times stories and Idea Exchange moves. Returns the best matches per category with ids to pass to the get_* tools.",
    inputSchema: { type: "object", required: ["query"], properties: {
      query: { type: "string", description: "What to look for, e.g. 'pet welcome', 'kids check-in', 'survey replacement'." },
      categories: { type: "array", items: { type: "string", enum: ["experiences", "customer_stories", "benchmarks", "cx_time", "idea_moves"] }, description: "Limit to these categories (default all)." },
      line: LINE_ARG, limit: { type: "integer", description: "Max matches per category (default 8, max 50)." },
    } },
    run: (D, a) => {
      if (!a.query) throw new ToolError("query is required");
      const cats = a.categories?.length ? a.categories : ["experiences", "customer_stories", "benchmarks", "cx_time", "idea_moves"];
      const L = Math.min(Number(a.limit) || 8, 50), lk = lineKey(a.line), out = { query: a.query };
      const top = (arr, txt, row) => rank(arr, txt, a.query).slice(0, L).map(([v, x]) => ({ score: Math.round(v * 100) / 100, ...row(x) }));
      if (cats.includes("experiences")) out.experiences = top(D.experiences.filter((x) => !lk || x.line === lk), expText, expRow);
      if (cats.includes("customer_stories")) out.customer_stories = top(csAll(D).filter((c) => !lk || c.line_label === CS_LINE[lk]), csText, csRow);
      if (cats.includes("benchmarks")) out.benchmarks = top(D.benchmarks.filter((b) => !lk || b.line === lk), bmText, bmRow);
      if (cats.includes("cx_time")) out.cx_time = top(allStories(D), storyText, storyRow);
      if (cats.includes("idea_moves")) out.idea_moves = top(D.idea_moves, (m) => [m.label, m.description, Object.values(m.becomes_by_line).join(" ")].join(" "), (m) => ({ key: m.key, label: m.label, journey_bucket: m.journey_bucket, description: m.description }));
      return out;
    },
  },
  {
    name: "list_experiences",
    title: "List signature experiences",
    description: "List and filter signature experiences across all business lines: by line, lifecycle stage, flagship, pillar, journey stage, property/asset in scope or live, target go-live window, Idea Exchange move, or free text. Returns compact rows; use get_experience for the full record.",
    inputSchema: { type: "object", properties: { ...EXP_FILTERS, sort: { type: "string", enum: ["line", "name", "target", "relevance"], description: "Ordering (default line, or relevance when query is set; 'target' = soonest target first)." }, ...PAGING } },
    run: (D, a) => page(filterExperiences(D, a).map(expRow), a.limit, a.offset),
  },
  {
    name: "get_experience",
    title: "Get one signature experience",
    description: "The full record for one signature experience: narrative, stage, target, latest note and dated history, deployment by asset, audit scores, touchpoints, benefits, photo URL, implementation photos, SharePoint asset folder, Idea Exchange moves, the benchmarks that informed it and its customer stories (customer_stories, when it has any). Accepts the id or the name.",
    inputSchema: { type: "object", required: ["id"], properties: { id: { type: "string", description: "Experience id (from list_experiences/search) or its name." } } },
    run: (D, a) => {
      const x = findExperience(D, a.id);
      if (!x) throw new ToolError(`No experience matches "${a.id}". Use search or list_experiences to find the id.`);
      const bm = (x.informed_by_benchmarks || []).map((id) => D.benchmarks.find((b) => b.id === id)).filter(Boolean).map(bmRow);
      return { ...x, informed_by_benchmarks: bm };
    },
  },
  {
    name: "portfolio_breakdown",
    title: "Portfolio breakdown",
    description: "Counts of signature experiences grouped by a dimension (line, stage, pillar, journey stage, property, live property, target month, defining), optionally filtered with the same filters as list_experiences. Use for 'how many', status splits, scorecards and pipeline views.",
    inputSchema: { type: "object", required: ["group_by"], properties: {
      group_by: { type: "string", enum: ["line", "stage", "pillar", "journey_stage", "property", "live_property", "target_month", "defining"] },
      ...EXP_FILTERS, include_ids: { type: "boolean", description: "Also list the experience names in each group." },
    } },
    run: (D, a) => {
      const r = filterExperiences(D, a);
      const by = {
        line: (x) => x.line_label, stage: (x) => x.stage, pillar: (x) => x.pillar, journey_stage: (x) => x.journey_stage,
        property: (x) => (x.deployment?.assets || []).map((p) => p.name), live_property: (x) => (x.deployment?.assets || []).filter((p) => p.live).map((p) => p.name),
        target_month: (x) => x.target_sort || x.target_go_live, defining: (x) => (x.defining ? "Defining" : "Not defining"),
      }[a.group_by];
      if (!by) throw new ToolError("group_by must be one of line, stage, pillar, journey_stage, property, live_property, target_month, defining");
      const out = { group_by: a.group_by, total_experiences: r.length, groups: count(r, by) };
      if (a.include_ids) {
        out.members = {};
        for (const x of r) for (const k of [].concat(by(x) ?? "—")) (out.members[k] = out.members[k] || []).push({ id: x.id, name: x.name, line: x.line_label });
      }
      if (a.group_by === "property" || a.group_by === "live_property") out.note = "An experience can be in scope at several properties, so property totals can exceed the experience count.";
      return out;
    },
  },
  {
    name: "get_programme",
    title: "Get a business line programme",
    description: "A business line's programme definition: name, source and last update, vision, pillars (with descriptions), journeys or phases, properties/assets, segments, school tiers, tracks and research findings.",
    inputSchema: { type: "object", required: ["line"], properties: { line: LINE_ARG } },
    run: (D, a) => {
      const lk = lineKey(a.line);
      if (!lk) throw new ToolError("line is required");
      return D.programmes.find((p) => p.line === lk);
    },
  },
  {
    name: "list_benchmarks",
    title: "List benchmarks",
    description: "Filter the 208 global CX benchmarks by the Aldar line they map to, industry, theme, pillar, brand or free text. Returns compact rows; use get_benchmark for the full case (why it works, how it transfers to each line).",
    inputSchema: { type: "object", properties: {
      line: LINE_ARG, industry: { type: "string", description: "Industry, e.g. Shopping malls, Education, Hospitality, Food & beverage, Beach clubs, Arts & culture, Technology (every value is listed under facets in the result)." }, theme: { type: "string", description: "Theme, e.g. Workplace, Employee Experience, Loyalty, Digital (see facets)." }, pillar: { type: "string" }, brand: { type: "string", description: "Brand or company, e.g. Ritz-Carlton, Disney, Yas Mall." },
      informs_experience: { type: "string", description: "Only benchmarks that informed this experience id." },
      query: { type: "string" }, ...PAGING,
    } },
    run: (D, a) => {
      let r = D.benchmarks; const lk = lineKey(a.line);
      if (lk) r = r.filter((b) => b.line === lk);
      if (a.industry) r = r.filter((b) => has(b.industry, a.industry));
      if (a.theme) r = r.filter((b) => (b.themes || []).some((t) => has(t, a.theme)));
      if (a.pillar) r = r.filter((b) => has(b.pillar, a.pillar));
      if (a.brand) r = r.filter((b) => has(b.brand, a.brand));
      if (a.informs_experience) r = r.filter((b) => (b.informs_experiences || []).some((id) => norm(id) === norm(a.informs_experience)));
      if (a.query) r = rank(r, bmText, a.query).map(([, b]) => b);
      return { ...page(r.map(bmRow), a.limit, a.offset), facets: { industries: count(D.benchmarks, (b) => b.industry), themes: count(D.benchmarks, (b) => b.themes) } };
    },
  },
  {
    name: "get_benchmark",
    title: "Get one benchmark",
    description: "The full benchmark case: brand, industry, lead, why it works, how it transfers to Aldar lines, source, the Aldar experiences it informed and its image URL.",
    inputSchema: { type: "object", required: ["id"], properties: { id: { type: "string", description: "Benchmark id or title." } } },
    run: (D, a) => {
      const n = norm(a.id);
      const b = D.benchmarks.find((x) => norm(x.id) === n) || D.benchmarks.find((x) => norm(x.title) === n) || D.benchmarks.find((x) => norm(x.title).includes(n));
      if (!b) throw new ToolError(`No benchmark matches "${a.id}".`);
      return { ...b, informs_experiences: (b.informs_experiences || []).map((id) => { const x = findExperience(D, id); return x ? { id: x.id, name: x.name, line: x.line_label, stage: x.stage } : { id }; }) };
    },
  },
  {
    name: "list_cx_time",
    title: "List Aldar CX Times stories",
    description: "Aldar CX Times editions and their curated stories (articles, videos, podcasts). Filter by edition number (default: every edition), format (read/watch/listen), tag, relevant Aldar line or free text.",
    inputSchema: { type: "object", properties: {
      edition: { type: "integer", description: "Edition number; omit for all editions." },
      format: { type: "string", enum: ["read", "watch", "listen"] }, tag: { type: "string" },
      line: { type: "string", description: "Aldar line the story is relevant to (e.g. Hospitality, Retail, PM & Leasing)." },
      query: { type: "string" }, ...PAGING,
    } },
    run: (D, a) => {
      let r = allStories(D);
      if (a.edition != null) r = r.filter((s) => s.edition === Number(a.edition));
      if (a.format) r = r.filter((s) => s.format === a.format);
      if (a.tag) r = r.filter((s) => has(s.tag, a.tag));
      if (a.line) r = r.filter((s) => (s.relevant_lines || []).some((l) => has(l, a.line) || has(a.line, l)));
      if (a.query) r = rank(r, storyText, a.query).map(([, s]) => s);
      return { editions: D.cx_time.map((e) => ({ edition: e.edition, date: e.date, stories: e.stories.length })), ...page(r.map(storyRow), a.limit, a.offset) };
    },
  },
  {
    name: "get_cx_time_story",
    title: "Get one CX Times story",
    description: "A full CX Times story: AI summary, key insights, why it matters to Aldar, relevant lines, the suggested signature experience(s), speakers, source and transcript links, image URL.",
    inputSchema: { type: "object", required: ["id"], properties: { id: { type: "string", description: "Story id (e.g. e2-s1) or title." } } },
    run: (D, a) => {
      const n = norm(a.id), all = allStories(D);
      const s = all.find((x) => norm(x.id) === n) || all.find((x) => norm(x.title).includes(n));
      if (!s) throw new ToolError(`No CX Times story matches "${a.id}".`);
      return s;
    },
  },
  {
    name: "get_idea_moves",
    title: "Idea Exchange moves",
    description: "Idea Exchange: the 26 transferable experience moves. Without a key, lists every move with its description and how many experiences embody it. With a key (or label), returns what the move becomes in each business line and the experiences that already embody it.",
    inputSchema: { type: "object", properties: { key: { type: "string", description: "Move key or label (e.g. 'greet', 'A named greeting ritual'). Omit to list all." }, line: LINE_ARG } },
    run: (D, a) => {
      if (!a.key) return { moves: D.idea_moves.map((m) => ({ key: m.key, label: m.label, journey_bucket: m.journey_bucket, description: m.description, experiences: m.experiences.length })) };
      const n = norm(a.key);
      const m = D.idea_moves.find((x) => norm(x.key) === n || norm(x.label) === n) || D.idea_moves.find((x) => norm(x.label).includes(n));
      if (!m) throw new ToolError(`No Idea Exchange move matches "${a.key}".`);
      const lk = lineKey(a.line);
      if (!lk) return m;
      const label = D.programmes.find((p) => p.line === lk).line_label;
      return { ...m, becomes_by_line: { [label]: m.becomes_by_line[label] }, experiences: m.experiences.filter((x) => x.line === label) };
    },
  },
  {
    name: "list_customer_stories",
    title: "List customer stories",
    description: "Customer Stories: moments told by the colleagues who delivered them, each an expression of a signature experience in the field. Filter by business line, linked experience, whether a story is linked to an experience yet, or free text. Returns compact rows plus totals by line; use get_customer_story for the full story.",
    inputSchema: { type: "object", properties: {
      line: LINE_ARG,
      experience: { type: "string", description: "Only stories linked to this experience (id or name)." },
      linked: { type: "boolean", description: "true = only stories linked to a signature experience; false = only stories awaiting a link." },
      query: { type: "string", description: "Free text matched against title, place, story, what made it memorable and colleagues." }, ...PAGING,
    } },
    run: (D, a) => {
      const all = csAll(D); let r = all; const lk = lineKey(a.line);
      if (lk) r = r.filter((c) => c.line_label === CS_LINE[lk]);
      if (a.experience) { const x = findExperience(D, a.experience); if (!x) throw new ToolError(`No experience matches "${a.experience}".`); r = r.filter((c) => c.experience && c.experience.id === x.id); }
      if (a.linked != null) r = r.filter((c) => !!c.experience === !!a.linked);
      if (a.query) r = rank(r, csText, a.query).map(([, c]) => c);
      return { updated: D.customer_stories_updated || null, totals: { stories: all.length, linked_to_an_experience: all.filter((c) => c.experience).length, by_line: count(all, (c) => c.line_label) },
        note: "Links marked 'proposed' were inferred from the story text and still need a line owner's confirmation.", ...page(r.map(csRow), a.limit, a.offset) };
    },
  },
  {
    name: "get_customer_story",
    title: "Get one customer story",
    description: "One customer story in full: title, business line, place, the story, what made it memorable, the colleagues involved, its source, a photo URL when there is one, and the signature experience it expresses (with link status confirmed or proposed). Accepts the id (e.g. cs-01) or the title.",
    inputSchema: { type: "object", required: ["id"], properties: { id: { type: "string", description: "Story id (from list_customer_stories/search) or its title." } } },
    run: (D, a) => {
      const c = findCustomerStory(D, a.id);
      if (!c) throw new ToolError(`No customer story matches "${a.id}". Use list_customer_stories or search to find it.`);
      return c;
    },
  },
  {
    name: "compare_experiences",
    title: "Compare experiences (AI read)",
    description: "Put 2 to 4 signature experiences side by side and get the hub's AI read of the set: what they share and where they differ, through three lenses (the need, the mechanism, the moment), a verdict (sequence them | consolidate | borrow across | keep apart) and a one-sentence takeaway. This is the same read the hub's compare view shows (same prompt, same cached result for the same set). Accepts ids or names.",
    inputSchema: { type: "object", required: ["ids"], properties: { ids: { type: "array", minItems: 2, maxItems: 4, items: { type: "string" }, description: "2 to 4 experience ids (from search / list_experiences) or names." } } },
    run: async (D, a) => {
      try {
        const r = await compareRead(D, a.ids);
        return { experiences: r.experiences, ai_read: r.read, generated_at: r.generated_at, how_to_read: "verdict: what to do with the set. shared / differs: findings, each tagged with its lens (need, mechanism, moment). takeaway: the customer-experience gain from acting on the verdict." };
      } catch (e) { if (e instanceof CompareError) throw new ToolError(e.message); throw e; }
    },
  },
];

// ---- sections hidden from the hub (features.json) are hidden here too ----
const IX_OFF = FEATURES.idea_exchange === false;
if (IX_OFF) {
  const k = TOOLS.findIndex((t) => t.name === "get_idea_moves"); if (k >= 0) TOOLS.splice(k, 1);
  const WORDING = [
    [", CX Times, Idea Exchange, SharePoint", ", CX Times, SharePoint"],
    ["benchmarks, CX Times stories and Idea Exchange moves", "benchmarks and CX Times stories"],
    ["target go-live window, Idea Exchange move, or free text", "target go-live window, or free text"],
    ["SharePoint asset folder, Idea Exchange moves and the benchmarks", "SharePoint asset folder and the benchmarks"],
  ];
  for (const t of TOOLS) {
    for (const [a, b] of WORDING) t.description = t.description.split(a).join(b);
    const p = t.inputSchema?.properties || {};
    delete p.idea_move;
    if (p.categories?.items?.enum) p.categories.items.enum = p.categories.items.enum.filter((c) => c !== "idea_moves");
  }
}
const PP_OFF = FEATURES.project_plus === false;
if (PP_OFF) {
  const W2 = [["across 7 business lines", "across 6 business lines"], ["Development, Estates or Project Plus (keys cp/hp/rp/edu/dev/est/pp also work)", "Development or Estates (keys cp/hp/rp/edu/dev/est also work)"]];
  for (const t of TOOLS) {
    for (const [a, b] of W2) t.description = t.description.split(a).join(b);
    for (const p of Object.values(t.inputSchema?.properties || {})) if (p && typeof p.description === "string") for (const [a, b] of W2) p.description = p.description.split(a).join(b);
  }
}
// the dataset as the hub shows it: without hidden business lines (cached per dataset object)
const _vis = new WeakMap();
function visible(D) {
  if (!PP_OFF || !D) return D;
  if (_vis.has(D)) return _vis.get(D);
  const keep = (x) => x && x.line !== "pp";
  const experiences = D.experiences.filter(keep);
  const ids = new Set(experiences.map((x) => x.id));
  const count = (arr, f) => arr.reduce((o, x) => { const k = f(x) ?? "\u2014"; o[k] = (o[k] || 0) + 1; return o; }, {});
  const V = {
    ...D, experiences,
    programmes: (D.programmes || []).filter(keep),
    benchmarks: (D.benchmarks || []).filter((b) => b.line !== "pp").map((b) => ({ ...b, informs_experiences: (b.informs_experiences || []).filter((i) => ids.has(i)) })),
    idea_moves: (D.idea_moves || []).map((m) => ({ ...m, experiences: (m.experiences || []).filter((x) => ids.has(x.id)) })),
    data_stamps: Object.fromEntries(Object.entries(D.data_stamps || {}).filter(([k]) => k !== "Project Plus")),
    counts: { ...D.counts, experiences: experiences.length, by_line: count(experiences, (x) => x.line_label), by_stage: count(experiences, (x) => x.stage), benchmarks: (D.benchmarks || []).filter((b) => b.line !== "pp").length },
  };
  _vis.set(D, V); return V;
}

// strip hidden sections from every tool result
function scrub(v) {
  if (!IX_OFF || v == null || typeof v !== "object") return typeof v === "string" && IX_OFF ? v.split("SharePoint folder, Idea Exchange moves and the benchmarks").join("SharePoint folder and the benchmarks") : v;
  if (Array.isArray(v)) return v.map(scrub);
  const o = {};
  for (const [k, x] of Object.entries(v)) if (k !== "idea_moves" && k !== "idea_exchange" && k !== "idea_move") o[k] = scrub(x);
  return o;
}

export const SERVER_INFO = { name: "aldar-signature-experience-hub", title: "Aldar Signature Experience Hub", version: "1.0.0" };
export const INSTRUCTIONS = "Read-only access to the Aldar Signature Experience Hub. Call get_overview first to see the data categories and counts. Use search for open questions, list_experiences/portfolio_breakdown for filtered views and counts, and the get_* tools for full records. Quote stages, dates and counts exactly as returned; never invent experiences.";

export function callTool(D, name, args) {
  const t = TOOLS.find((x) => x.name === name);
  if (!t) throw new ToolError(`Unknown tool "${name}".`);
  const a = { ...(args || {}) };
  if (IX_OFF) { delete a.idea_move; if (Array.isArray(a.categories)) a.categories = a.categories.filter((c) => c !== "idea_moves"); if (!a.categories?.length) delete a.categories; }
  const out = t.run(visible(D), a);
  if (out && typeof out.then === "function") return out.then(scrub); // async tools (compare_experiences)
  if (IX_OFF && out && out.idea_moves !== undefined && name === "search") delete out.idea_moves;
  return scrub(out);
}
export const toolList = () => TOOLS.map(({ run, ...t }) => ({ ...t, annotations: { readOnlyHint: true, openWorldHint: false } }));
