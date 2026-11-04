// POST /api/martin-token -> a short-lived Direct Line token for CX Martin (Copilot Studio).
// The hub's branded chat (app/martin.html) calls this; the Web channel security secret stays
// server-side in CX_MARTIN_DIRECTLINE_SECRET (Netlify env, functions scope) and is never sent
// to the browser. Each token is valid for about an hour and for one anonymous visitor id.
import { randomUUID } from "node:crypto";

const DL = "https://directline.botframework.com/v3/directline/tokens/generate";

export default async (req) => {
  if (req.method !== "POST") return Response.json({ error: "Use POST." }, { status: 405 });
  const secret = process.env.CX_MARTIN_DIRECTLINE_SECRET;
  if (!secret) return Response.json({ error: "CX Martin is not connected on this site." }, { status: 503 });
  const userId = "dl_" + randomUUID();
  try {
    const r = await fetch(DL, {
      method: "POST",
      headers: { authorization: "Bearer " + secret, "content-type": "application/json" },
      body: JSON.stringify({ user: { id: userId } }),
    });
    if (!r.ok) {
      console.log(JSON.stringify({ martin: "token-failed", status: r.status }));
      return Response.json({ error: "CX Martin is unavailable right now." }, { status: 502 });
    }
    const j = await r.json();
    return new Response(JSON.stringify({ token: j.token, conversationId: j.conversationId, expires_in: j.expires_in, userId }), {
      headers: { "content-type": "application/json", "cache-control": "no-store" },
    });
  } catch (e) {
    console.log(JSON.stringify({ martin: "token-error", message: String(e?.message || e) }));
    return Response.json({ error: "CX Martin is unavailable right now." }, { status: 502 });
  }
};

export const config = { path: "/api/martin-token", method: ["POST"], rateLimit: { windowLimit: 30, windowSize: 60, aggregateBy: ["ip", "domain"] } };
