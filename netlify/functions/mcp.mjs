// MCP server for the Aldar Signature Experience Hub (Streamable HTTP, stateless, read-only).
// Microsoft Copilot Studio and other MCP clients connect to https://<site>/mcp.
// The dataset is generated from index.html on every deploy (tools/build_mcp_data.mjs), plus
// submissions approved through /sx/ (read live from Netlify Blobs).
// Open and public: no authentication. Read-only, rate limited per client.
import { liveDataset } from "./_lib/live-data.mjs";
import { callTool, toolList, ToolError, SERVER_INFO, INSTRUCTIONS } from "./_lib/mcp-core.mjs";

const PROTOCOLS = ["2025-06-18", "2025-03-26", "2024-11-05"];
const CORS = {
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET, POST, DELETE, OPTIONS",
  "access-control-allow-headers": "content-type, accept, mcp-protocol-version, mcp-session-id, authorization",
  "access-control-expose-headers": "mcp-session-id",
};
const json = (body, status = 200, extra = {}) =>
  new Response(body == null ? null : JSON.stringify(body), { status, headers: { "content-type": "application/json", ...CORS, ...extra } });
const empty = (status) => new Response(null, { status, headers: CORS });
const rpcError = (id, code, message) => ({ jsonrpc: "2.0", id: id ?? null, error: { code, message } });

async function handle(msg, dataset) {
  if (!msg || msg.jsonrpc !== "2.0" || typeof msg.method !== "string") return rpcError(msg?.id, -32600, "Invalid request");
  const { id, method, params = {} } = msg;
  const isNotification = id === undefined || id === null;
  switch (method) {
    case "initialize": {
      const v = PROTOCOLS.includes(params.protocolVersion) ? params.protocolVersion : PROTOCOLS[0];
      return { jsonrpc: "2.0", id, result: { protocolVersion: v, capabilities: { tools: { listChanged: false } }, serverInfo: SERVER_INFO, instructions: INSTRUCTIONS } };
    }
    case "ping":
      return { jsonrpc: "2.0", id, result: {} };
    case "tools/list":
      return { jsonrpc: "2.0", id, result: { tools: toolList() } };
    case "tools/call": {
      try {
        const out = await callTool(dataset, params.name, params.arguments);
        console.log(JSON.stringify({ mcp: "call", tool: params.name, args: params.arguments || {} }));
        return { jsonrpc: "2.0", id, result: { content: [{ type: "text", text: JSON.stringify(out) }], structuredContent: out, isError: false } };
      } catch (e) {
        const message = e instanceof ToolError ? e.message : "Tool failed: " + String(e?.message || e);
        console.log(JSON.stringify({ mcp: "error", tool: params.name, message }));
        return { jsonrpc: "2.0", id, result: { content: [{ type: "text", text: message }], isError: true } };
      }
    }
    default:
      if (isNotification || method.startsWith("notifications/")) return null; // e.g. notifications/initialized
      return rpcError(id, -32601, "Method not found: " + method);
  }
}

export default async (req) => {
  if (req.method === "OPTIONS") return empty(204);
  if (req.method === "GET") return json({ error: "This MCP endpoint accepts POST (Streamable HTTP, no SSE stream)." }, 405, { allow: "POST" });
  if (req.method === "DELETE") return empty(204);
  if (req.method !== "POST") return json({ error: "Method not allowed" }, 405, { allow: "POST" });
  let body;
  try { body = await req.json(); } catch { return json(rpcError(null, -32700, "Parse error"), 400); }
  if (Array.isArray(body)) {
    const dataset = await liveDataset();
    const out = (await Promise.all(body.map((m) => handle(m, dataset)))).filter(Boolean);
    return out.length ? json(out) : empty(202);
  }
  const out = await handle(body, body && body.method === "tools/call" ? await liveDataset() : null);
  return out ? json(out) : empty(202);
};

export const config = {
  path: "/mcp",
  method: ["GET", "POST", "DELETE", "OPTIONS"],
  rateLimit: { windowLimit: 120, windowSize: 60, aggregateBy: ["ip", "domain"] },
};
