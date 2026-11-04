// Hub sign-in gate: runs before every request to the site.
// Without a valid hub_session cookie, pages get the sign-in page and APIs get 401.
// Left open: /mcp (it has its own key, MCP_API_KEY), the sign-in endpoint, the photos in /img/
// (content-hash names; Teams loads them when CX Martin answers with pictures) and the icons and
// link-preview image that the sign-in page and WhatsApp/Teams previews need.
import { COOKIE, readCookie, verify, loginPage, safeNext } from "../shared/hub-session.mjs";

const OPEN = [
  /^\/mcp\/?$/, /^\/api\/hub-login\/?$/, /^\/img\//,
  /^\/app\/(aldar-logo\.png|og-hub\.jpg|og-submit\.jpg|favicon-\d+\.png|apple-touch-icon\.png|icon-[\w-]+\.png)$/,
  /^\/manifest\.webmanifest$/, /^\/robots\.txt$/,
];

export default async (req, context) => {
  const url = new URL(req.url);
  if (OPEN.some((r) => r.test(url.pathname))) return context.next();

  const secret = Netlify.env.get("HUB_SESSION_SECRET"), code = Netlify.env.get("HUB_ACCESS_CODE");
  if (await verify(readCookie(req.headers.get("cookie"), COOKIE), secret, code)) return context.next();

  const isPage = req.method === "GET" && !url.pathname.startsWith("/api/") && /text\/html|\*\/\*/.test(req.headers.get("accept") || "*/*");
  if (!isPage) {
    return new Response(JSON.stringify({ error: "Sign in to the hub first." }), { status: 401, headers: { "content-type": "application/json", "cache-control": "no-store" } });
  }
  const html = loginPage({ next: safeNext(url.pathname + url.search), error: url.searchParams.get("signin") === "failed", notConfigured: !secret || !code });
  return new Response(html, { status: 200, headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store", "x-robots-tag": "noindex" } });
};

export const config = { path: "/*" };
