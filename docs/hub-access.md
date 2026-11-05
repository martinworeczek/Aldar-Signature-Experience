# Hub access: sign-in gate and MCP key

The hub (aldar-signature-experience.netlify.app) is behind a shared access code, and the MCP
server behind an API key. The standalone CX Times site stays public.

## How it works
- `netlify/edge-functions/hub-gate.js` runs before every request. Without a valid session cookie,
  pages show the sign-in page and APIs answer 401. This covers the hub, Submit & review (`/sx/`),
  Ask Echo (`/app/martin.html`, `/api/martin-token`) and the AI services (`/api/ai`,
  `/api/compare-read`, `/api/sx/*`).
- Left open on purpose:
  - `/mcp`, which has its own key;
  - `/api/hub-login`, the sign-in endpoint;
  - `/img/*`: photos with content-hash names, which Teams loads when Echo answers with pictures;
  - the icons and link-preview image, so WhatsApp and Teams previews keep working.
- `netlify/functions/hub-login.mjs` checks the code (10 tries a minute per IP) and sets an HttpOnly,
  Secure cookie valid for 30 days. Sign out: `/api/hub-login?signout=1`.
- The cookie is signed with `HUB_SESSION_SECRET` and the current access code, so **changing
  `HUB_ACCESS_CODE` signs everyone out**.
- `/mcp` accepts the key as the `x-api-key` header (or `Authorization: Bearer`). While
  `MCP_KEY_REQUIRED` is not `true`, calls without the key are still answered, and each call is
  logged as `{"mcp":"auth","key":"valid|wrong|none"}`.

## Netlify settings (Site configuration → Environment variables), scope: Functions
| Key | Value |
|---|---|
| `HUB_ACCESS_CODE` | the code people type, e.g. a short phrase plus digits |
| `HUB_SESSION_SECRET` | a long random string (40+ characters); never shared |
| `MCP_API_KEY` | a long random string; pasted into Copilot Studio only |
| `MCP_KEY_REQUIRED` | `false` during the switch-over, then `true` |

Mark the first three as secret. Redeploy after changing any of them.

Until both `HUB_ACCESS_CODE` and `HUB_SESSION_SECRET` exist, the gate is off (the hub stays open, and the
log says `gate-off`). If only one of them exists, the gate stays closed and the sign-in page says it isn't set up.

## Copilot Studio (Echo → Tools → the hub MCP tool)
Authentication: **API key** · type **Header** · header name **`x-api-key`** · value: `MCP_API_KEY`.
Then publish. Once the function log shows `"key":"valid"`, set `MCP_KEY_REQUIRED` to `true`.

## Moving to Microsoft sign-in later
Only the gate changes: swap the access-code check for an Entra ID (OIDC) sign-in. That needs an app
registration in Aldar's tenant. Everything else (open paths, cookie, MCP key) stays.
