// The hub's data as visitors see it: the data sets built from index.html, plus every
// submission the Group CX reviewer has approved (Netlify Blobs). Shared by /mcp and /api/sx,
// so Echo answers from exactly what the hub shows.
import { getStore } from "@netlify/blobs";
import native from "../_data/hub-native.json" with { type: "json" };
import base from "../_data/mcp-dataset.json" with { type: "json" };
import "../../../sx/sx-apply.js";
import { buildDataset } from "./normalise.mjs";

export const STORE = "sx-submissions";
export const store = () => getStore({ name: STORE, consistency: "strong" });

export async function readPublished() {
  const list = await store().get("published", { type: "json" });
  return Array.isArray(list) ? list : [];
}

const TTL = 20_000;
let cache = { at: 0, key: "", dataset: base };

// the dataset with approved submissions applied (cached briefly per function instance)
export async function liveDataset({ fresh = false } = {}) {
  if (!fresh && Date.now() - cache.at < TTL) return cache.dataset;
  let records;
  try { records = await readPublished(); } catch (e) { console.log(JSON.stringify({ sx: "blobs-read-failed", message: String(e?.message || e) })); return cache.dataset; }
  const key = records.map((r) => r.id + "@" + r.approved_at).join("|");
  if (key !== cache.key) {
    let dataset = base;
    if (records.length) {
      const W = structuredClone(native);
      for (const [line, L] of Object.entries(globalThis.SX_APPLY.LINES)) globalThis.SX_APPLY.apply(line, W[L.g], records, W);
      dataset = buildDataset(W, native.full || [], base.site);
      dataset.generated_at = base.generated_at;
      dataset.hub_submissions = { approved_records: records.length, as_of: new Date().toISOString() };
    }
    cache = { at: Date.now(), key, dataset };
  } else cache.at = Date.now();
  return cache.dataset;
}

export function invalidate() { cache.at = 0; }
