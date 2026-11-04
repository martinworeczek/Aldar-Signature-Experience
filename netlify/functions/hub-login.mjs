// POST /api/hub-login  (form: code, next) -> sets the hub_session cookie and returns to the page.
// GET  /api/hub-login?signout=1          -> clears it.
// The access code lives only in Netlify env (HUB_ACCESS_CODE); rate limited per IP.
import { COOKIE, MAX_AGE, issue, same, safeNext } from "../shared/hub-session.mjs";

const go = (to, cookie) => new Response(null, { status: 303, headers: { location: to, "cache-control": "no-store", ...(cookie ? { "set-cookie": cookie } : {}) } });

export default async (req) => {
  const url = new URL(req.url);
  if (req.method === "GET" && url.searchParams.has("signout")) {
    return go("/", COOKIE + "=; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=0");
  }
  if (req.method !== "POST") return go("/");
  const secret = process.env.HUB_SESSION_SECRET, code = process.env.HUB_ACCESS_CODE;
  let form;
  try { form = await req.formData(); } catch { return go("/?signin=failed"); }
  const next = safeNext(form.get("next"));
  const given = String(form.get("code") || "").trim();
  if (!secret || !code || !same(given, code)) {
    console.log(JSON.stringify({ hub: "signin-failed" }));
    return go(next + (next.includes("?") ? "&" : "?") + "signin=failed");
  }
  const token = await issue(secret, code);
  console.log(JSON.stringify({ hub: "signin" }));
  return go(next.replace(/([?&])signin=failed&?/, "$1").replace(/[?&]$/, ""),
    `${COOKIE}=${token}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${MAX_AGE}`);
};

export const config = { path: "/api/hub-login", method: ["GET", "POST"], rateLimit: { windowLimit: 10, windowSize: 60, aggregateBy: ["ip", "domain"] } };
