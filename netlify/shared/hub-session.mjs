// Hub sign-in session, shared by the edge gate (netlify/edge-functions/hub-gate.js) and the
// sign-in endpoint (netlify/functions/hub-login.mjs). Web Crypto only, so it runs in both.
//
// The cookie is "v1.<expiry>.<signature>", an HMAC-SHA256 keyed on HUB_SESSION_SECRET and the
// current HUB_ACCESS_CODE. Changing the access code in Netlify therefore signs everyone out.

export const COOKIE = "hub_session";
export const MAX_AGE = 30 * 24 * 3600; // 30 days

const enc = new TextEncoder();
const b64url = (buf) => btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");

async function hmac(secret, code, msg) {
  const key = await crypto.subtle.importKey("raw", enc.encode(secret + "|" + code), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return b64url(await crypto.subtle.sign("HMAC", key, enc.encode(msg)));
}

// constant-time string comparison
export function same(a, b) {
  a = String(a ?? ""); b = String(b ?? "");
  let d = a.length ^ b.length;
  for (let i = 0; i < Math.max(a.length, b.length); i++) d |= (a.charCodeAt(i) || 0) ^ (b.charCodeAt(i) || 0);
  return d === 0;
}

export async function issue(secret, code, now = Date.now()) {
  const exp = Math.floor(now / 1000) + MAX_AGE;
  return "v1." + exp + "." + (await hmac(secret, code, "v1." + exp));
}

export async function verify(token, secret, code, now = Date.now()) {
  if (!token || !secret || !code) return false;
  const m = /^v1\.(\d{9,11})\.([A-Za-z0-9_-]{20,})$/.exec(token);
  if (!m || Number(m[1]) * 1000 < now) return false;
  return same(m[2], await hmac(secret, code, "v1." + m[1]));
}

export function readCookie(header, name = COOKIE) {
  for (const part of String(header || "").split(/;\s*/)) {
    const i = part.indexOf("=");
    if (i > 0 && part.slice(0, i) === name) return decodeURIComponent(part.slice(i + 1));
  }
  return "";
}

// only same-site paths, never "//host" or a scheme
export function safeNext(v) {
  const s = String(v || "/");
  return s.startsWith("/") && !s.startsWith("//") && !s.startsWith("/\\") ? s.slice(0, 500) : "/";
}

const esc = (t) => String(t).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

// the sign-in page: Aldar-branded, and it carries the hub's link-preview tags for WhatsApp/Teams
export function loginPage({ next = "/", error = "", notConfigured = false } = {}) {
  const msg = notConfigured ? "Sign-in isn’t set up on this site yet. Contact Group CX."
    : error ? "That access code isn’t right. Try again, or ask Group CX for the current code." : "";
  return `<!doctype html>
<html lang="en-GB"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Aldar Signature Experience Hub · Sign in</title>
<meta name="robots" content="noindex">
<meta name="description" content="Every signature experience across Aldar’s business lines, with global benchmarks, Customer Stories and Aldar CX Times. Curated by Group CX.">
<meta property="og:title" content="Aldar Signature Experience Hub">
<meta property="og:description" content="Every signature experience across Aldar’s business lines, with global benchmarks, Customer Stories and Aldar CX Times. Curated by Group CX.">
<meta property="og:image" content="https://aldar-signature-experience.netlify.app/app/og-hub.jpg">
<meta property="og:type" content="website"><meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/app/favicon-32.png"><link rel="apple-touch-icon" href="/app/apple-touch-icon.png"><link rel="manifest" href="/manifest.webmanifest">
<meta name="theme-color" content="#070c10">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
:root{--bg:#070c10;--panel:#0e171d;--line:rgba(232,185,106,.28);--ink:#f6f3ec;--muted:#9aa5ad;--gold:#e8b96a}
*{box-sizing:border-box}html,body{margin:0;height:100%;background:var(--bg);color:var(--ink);font:15px/1.6 Poppins,system-ui,sans-serif;-webkit-font-smoothing:antialiased}
body{display:flex;align-items:center;justify-content:center;padding:24px 16px;background:radial-gradient(70% 60% at 50% 40%,#16212b,#070c10 75%)}
.card{width:100%;max-width:420px;background:rgba(14,23,29,.92);border:1px solid var(--line);border-radius:20px;padding:36px 32px 30px;box-shadow:0 40px 90px -40px rgba(0,0,0,.9);text-align:center}
.logo{width:72px;height:72px;margin:0 auto 22px;border-radius:12px;background:#05080a url(/app/aldar-logo.png) center/78% no-repeat;border:1px solid rgba(232,185,106,.45)}
.k{font-size:10.5px;font-weight:600;letter-spacing:.24em;text-transform:uppercase;color:var(--gold)}
h1{margin:10px 0 6px;font-size:26px;font-weight:300;line-height:1.2}
p{margin:0 0 22px;color:var(--muted);font-size:13.5px}
form{display:flex;flex-direction:column;gap:12px;text-align:left}
label{font-size:11px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:var(--muted)}
input{width:100%;font:inherit;font-size:16px;color:var(--ink);background:#0a1115;border:1px solid rgba(255,255,255,.16);border-radius:12px;padding:13px 14px;outline:none}
input:focus{border-color:var(--gold)}
button{font:600 13px Poppins,sans-serif;letter-spacing:.04em;color:#0a1014;background:linear-gradient(180deg,#e8c97e,#c9a24a);border:0;border-radius:999px;padding:13px 18px;cursor:pointer;margin-top:4px}
.err{background:rgba(201,138,110,.12);border:1px solid rgba(201,138,110,.4);color:#f0c4b2;border-radius:10px;padding:10px 12px;font-size:13px;text-align:left}
.foot{margin-top:18px;font-size:11px;color:#6c7880}
</style></head>
<body><main class="card">
<div class="logo" role="img" aria-label="Aldar"></div>
<div class="k">Aldar · Group CX</div>
<h1>Signature Experience Hub</h1>
<p>Enter the hub access code to continue.</p>
${msg ? `<div class="err" role="alert">${esc(msg)}</div>` : ""}
<form method="post" action="/api/hub-login">
<input type="hidden" name="next" value="${esc(next)}">
<label for="code">Access code</label>
<input id="code" name="code" type="password" autocomplete="current-password" required autofocus${notConfigured ? " disabled" : ""}>
<button type="submit"${notConfigured ? " disabled" : ""}>Sign in</button>
</form>
<div class="foot">You stay signed in on this device for 30 days.</div>
</main></body></html>`;
}
