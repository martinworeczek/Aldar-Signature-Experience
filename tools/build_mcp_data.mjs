// Build the MCP dataset from the live page (index.html).
//
// Every data set the hub renders is embedded in index.html's bundle manifest. This loads
// them exactly as the browser does (a sandboxed `window`), normalises the seven business
// lines into one experience schema using the hub's own status rules, and writes
// netlify/functions/_data/ (dataset, native snapshot, form options) for /mcp and /api/sx. Netlify runs it on every
// deploy (netlify.toml [build] command), so the MCP server always matches the site.
//
// Usage: node tools/build_mcp_data.mjs
import fs from "node:fs";
import zlib from "node:zlib";
import vm from "node:vm";
import path from "node:path";
import { buildDataset, NATIVE_GLOBALS } from "../netlify/functions/_lib/normalise.mjs";
import "../sx/sx-apply.js"; // defines globalThis.SX_APPLY (shared with the hub page)

const SITE = "https://aldar-signature-experience.netlify.app";
const OUT = "netlify/functions/_data/mcp-dataset.json";
const NATIVE_OUT = "netlify/functions/_data/hub-native.json"; // raw data sets, for re-applying approved submissions
const OPTIONS_OUT = "netlify/functions/_data/sx-options.json"; // per-line choices for the submission form
const formOptions = (W) => globalThis.SX_APPLY.options(W);

const html = fs.readFileSync("index.html", "utf8");
const manifest = JSON.parse(html.match(/<script type="__bundler\/manifest">\s*(\{[\s\S]*?\})\s*<\/script>/)[1]);
const asset = (e) => { let b = Buffer.from(e.data, "base64"); if (e.compressed) b = zlib.gunzipSync(b); return b.toString("utf8"); };

// ---- load the data globals in a sandbox ----
const win = {};
const ctx = vm.createContext({
  window: win, console, setTimeout() {}, setInterval() {}, clearInterval() {},
  document: { querySelector: () => null, querySelectorAll: () => [], addEventListener() {}, readyState: "complete" },
  localStorage: { getItem: () => null, setItem() {} }, location: { search: "", hash: "", protocol: "https:" },
  addEventListener() {}, dispatchEvent() {}, CustomEvent: function () {},
});
let benchmarkModule = "";
for (const e of Object.values(manifest)) {
  if (/html/.test(e.mime)) { const t = asset(e); if (/Benchmark Gallery|const DATA = \[\s*\{ id:'jpm-270park'/.test(t)) benchmarkModule = t; continue; }
  if (!/javascript/.test(e.mime)) continue;
  const t = asset(e);
  if (/GENERATED from dc-runtime|@license React|KPR_VIDEO/.test(t.slice(0, 400))) continue;
  try { vm.runInContext(t, ctx, { timeout: 3000 }); } catch { /* loaders that need a real DOM */ }
}
const W = win;
for (const g of ["CP_DATA", "HP_DATA", "RP_DATA", "EDU_DATA", "DEV_DATA", "EST_DATA", "PP_DATA", "AT_DATA", "BM_LINKS", "IX_ENGINE"]) {
  if (!W[g]) throw new Error("missing data set " + g);
}


// ---- benchmarks: the gallery's full records ----
let full = [];
const dm = benchmarkModule.indexOf("const DATA = [");
if (dm >= 0) {
  // the block is a JS literal that ends on its own "];" line
  const i = benchmarkModule.indexOf("[", dm), j = benchmarkModule.indexOf("\n];", i) + 1;
  try { full = vm.runInNewContext("(" + benchmarkModule.slice(i, j + 1) + ")", {}, { timeout: 3000 }); } catch (err) { console.warn("benchmark gallery data not parsed:", String(err).slice(0, 120)); }
}

// ---- snapshot the native data (for /mcp to re-apply submissions) and build the dataset ----
const native = { full };
for (const g of NATIVE_GLOBALS) if (W[g] !== undefined) native[g] = W[g];
const dataset = buildDataset(JSON.parse(JSON.stringify(native)), full, SITE);
fs.mkdirSync(path.dirname(OUT), { recursive: true });
fs.writeFileSync(OUT, JSON.stringify(dataset));
fs.writeFileSync(NATIVE_OUT, JSON.stringify(native));
fs.writeFileSync(OPTIONS_OUT, JSON.stringify(formOptions(W)));
console.log("mcp dataset:", JSON.stringify(dataset.counts), (fs.statSync(OUT).size / 1e6).toFixed(2) + " MB; native", (fs.statSync(NATIVE_OUT).size / 1e6).toFixed(2) + " MB");
