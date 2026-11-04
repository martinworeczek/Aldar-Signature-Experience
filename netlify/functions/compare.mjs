// POST /api/compare-read  {ids:[2-4 experience ids]}  ->  the AI read as JSON
// {verdict, shared[], differs[], takeaway}, the same object CX Martin's compare_experiences returns.
import { liveDataset } from "./_lib/live-data.mjs";
import { compareRead, CompareError } from "./_lib/compare-read.mjs";

export default async (req) => {
  if (req.method !== "POST") return Response.json({ error: "Use POST." }, { status: 405 });
  let body; try { body = await req.json(); } catch { return Response.json({ error: "Body must be JSON." }, { status: 400 }); }
  try {
    const out = await compareRead(await liveDataset(), body.ids, { refresh: !!body.refresh });
    return new Response(JSON.stringify(out.read), { headers: { "content-type": "application/json", "cache-control": "no-store" } });
  } catch (e) {
    const msg = e instanceof CompareError ? e.message : "The reader is unavailable right now.";
    if (!(e instanceof CompareError)) console.log(JSON.stringify({ compare: "error", message: String(e?.stack || e) }));
    return Response.json({ error: msg }, { status: e instanceof CompareError ? 422 : 502 });
  }
};

export const config = { path: "/api/compare-read", method: ["POST"], rateLimit: { windowLimit: 30, windowSize: 60, aggregateBy: ["ip", "domain"] } };
