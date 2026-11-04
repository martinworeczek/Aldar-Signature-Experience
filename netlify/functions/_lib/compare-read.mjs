// The "AI read" for 2–4 signature experiences compared side by side.
//
// One implementation, used by both surfaces so they always agree:
//   - the hub's compare view (POST /api/compare-read, netlify/functions/compare.mjs)
//   - CX Martin / any MCP client (the compare_experiences tool in mcp-core.mjs)
// The prompt is the hub's own (moved here from the page). Reads are cached in Netlify Blobs per
// set of experiences AND the facts the read was based on, so the same set gives the same read
// until one of those experiences changes.
import Anthropic from "@anthropic-ai/sdk";
import { getStore } from "@netlify/blobs";
import { createHash } from "node:crypto";

const MODEL = "claude-sonnet-5-5";
const store = () => getStore({ name: "compare-reads", consistency: "strong" });
export class CompareError extends Error {}

const norm = (s) => String(s ?? "").toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, "").trim();
function find(D, id) {
  const n = norm(id);
  return D.experiences.find((x) => norm(x.id) === n) || D.experiences.find((x) => norm(x.name) === n) || D.experiences.find((x) => norm(x.name).includes(n));
}
const cut = (s, n) => String(s || "").slice(0, n);

// the same facts the hub sends (name, line, essence, narrative, pillar, moment, benefits, touchpoints, benchmarks)
function record(D, x) {
  const bm = (x.informed_by_benchmarks || []).map((id) => (D.benchmarks || []).find((b) => b.id === id)).filter(Boolean).slice(0, 2)
    .map((b) => b.title + " (" + String(b.brand || "").split(" · ")[0] + ")");
  const live = x.deployment && x.deployment.in_scope ? " · " + x.deployment.live + " of " + x.deployment.in_scope + " assets live" : "";
  const r = {
    name: x.name, line: x.line_label, essence: x.essence,
    narrative: cut(x.narrative, 460), pillar: x.pillar || "", moment: x.moment_of_truth || x.journey_stage || "",
    customerBenefit: cut(x.customer_benefit, 260), aldarBenefit: cut(x.aldar_benefit, 260),
    touchpoints: (x.touchpoints || []).slice(0, 6), informedByBenchmarks: bm,
    flagshipForItsLine: !!x.defining, deliveryContextOnly: x.stage + live,
  };
  for (const k of Object.keys(r)) if (r[k] === "" || r[k] == null || (Array.isArray(r[k]) && !r[k].length)) delete r[k];
  return r;
}

const SYSTEM = (n) => "You are a CX strategist at Aldar, an Abu Dhabi property group. A colleague has put " + n +
  " of Aldar’s own signature customer experiences side by side. Your job is to help the team see the VALUE in these experiences — compare the experiences themselves, never their delivery status.\n\n" +
  "Read them through exactly three lenses, and label every point with the lens it comes from:\n" +
  "1. NEED — what customer tension or anxiety does each one resolve? Is it the same underlying need answered twice, or different needs?\n" +
  "2. MECHANISM — HOW is the feeling actually produced: a trained person, a ritual, a gift or keepsake, a system, a physical space, a piece of information given early? The mechanism is the part another business line could adopt, so name it precisely.\n" +
  "3. MOMENT — where in the customer journey each one lands, and whether they compound (a chain worth designing deliberately) or crowd the same moment.\n\n" +
  'Reply with ONLY this JSON and no prose around it: {"verdict":"sequence them|consolidate|borrow across|keep apart","shared":[{"lens":"need|mechanism|moment","head":"3-6 words","body":"one sentence"}],"differs":[{"lens":"need|mechanism|moment","head":"3-6 words","body":"one sentence"}],"takeaway":"one sentence"}\n\n' +
  'Rules. 2 to 3 items in "shared" and 2 to 3 in "differs", each from a different lens where possible. ' +
  'FORBIDDEN as findings: lifecycle stage, deployment counts, target dates, audit status, business-line membership, or anything about feasibility, cost, effort or delivery risk — the field "deliveryContextOnly" is background for your judgement and must never be quoted or described. ' +
  "Also forbidden: restating that they belong to the same business line, or that both are signature experiences. " +
  'The "verdict" must be one of the four given values: sequence them (they form a chain across the journey), consolidate (two versions of one idea), borrow across (one’s mechanism would strengthen the other), keep apart (different needs, no shared work). ' +
  "The takeaway is one sentence naming the customer-experience gain from acting on that verdict — what a family, guest, resident or colleague would feel differently. Never a project action, never a date. " +
  "Every claim must be grounded in the data given — never invent figures, schools, properties or outcomes. Name the experiences by title. Plain British English, no marketing language, no bullet symbols.";

const VERDICTS = ["sequence them", "consolidate", "borrow across", "keep apart"];
function clean(o) {
  if (!o || (!o.shared && !o.differs)) return null;
  const items = (a) => (Array.isArray(a) ? a : []).slice(0, 3).map((x) => ({ lens: ["need", "mechanism", "moment"].includes(String(x && x.lens).toLowerCase()) ? String(x.lens).toLowerCase() : "", head: String((x && x.head) || ""), body: String((x && x.body) || "") })).filter((x) => x.head || x.body);
  const v = String(o.verdict || "").toLowerCase().trim();
  return { verdict: VERDICTS.includes(v) ? v : "", shared: items(o.shared), differs: items(o.differs), takeaway: String(o.takeaway || "") };
}

// ids: 2–4 experience ids or names. Returns { experiences, read, generated_at, cached }.
export async function compareRead(D, ids, { refresh = false } = {}) {
  const list = [...new Set((Array.isArray(ids) ? ids : []).map(String).filter(Boolean))];
  if (list.length < 2 || list.length > 4) throw new CompareError("Compare 2 to 4 experiences.");
  const xs = list.map((id) => { const x = find(D, id); if (!x) throw new CompareError(`No experience matches "${id}".`); return x; });
  if (new Set(xs.map((x) => x.id)).size < 2) throw new CompareError("Pick at least two different experiences.");
  const recs = xs.map((x) => record(D, x));
  const key = xs.map((x) => x.id).sort().join("+").slice(0, 400) + "@" + createHash("sha1").update(JSON.stringify(recs)).digest("hex").slice(0, 12);
  const experiences = xs.map((x) => ({ id: x.id, name: x.name, line: x.line_label, stage: x.stage, essence: x.essence, image_url: x.image_url }));

  if (!refresh) {
    try { const hit = await store().get(key, { type: "json" }); if (hit && hit.read) return { experiences, ...hit, cached: true }; } catch (e) { /* regenerate */ }
  }
  if (!process.env.ANTHROPIC_BASE_URL) throw new CompareError("The AI reader is not available on this site right now.");
  const client = new Anthropic();
  let read = null;
  for (let attempt = 0; attempt < 2 && !read; attempt++) {
    const msg = await client.messages.create({ model: MODEL, max_tokens: 1400, system: SYSTEM(recs.length), messages: [{ role: "user", content: JSON.stringify(recs, null, 1) }] });
    const text = msg.content.filter((p) => p.type === "text").map((p) => p.text).join("");
    try { const m = text.match(/\{[\s\S]*\}/); read = clean(JSON.parse(m ? m[0] : text)); } catch { read = null; }
  }
  if (!read) throw new CompareError("The reader could not summarise this set. Try again.");
  const rec = { ids: xs.map((x) => x.id), read, generated_at: new Date().toISOString() };
  try { await store().setJSON(key, rec); } catch (e) { console.log(JSON.stringify({ compare: "cache-write-failed", message: String(e?.message || e) })); }
  console.log(JSON.stringify({ compare: "generated", ids: rec.ids }));
  return { experiences, ...rec, cached: false };
}
