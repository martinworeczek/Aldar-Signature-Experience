// MCP server for the Aldar Signature Experience Hub (Streamable HTTP, stateless, read-only).
// Microsoft Copilot Studio and other MCP clients connect to https://<site>/mcp.
// The dataset is generated from index.html on every deploy (tools/build_mcp_data.mjs).
// If MCP_API_KEY is set on the site, requests must send it as `x-api-key` or `Authorization: Bearer`.
import dataset from "./_data/mcp-dataset.json" with { type: "json" };
import { callTool, toolList, ToolError, SERVER_INFO, INSTRUCTIONS } from "./_lib/mcp-core.mjs";

const PROTOCOLS = ["2025-06-18", "2025-03-26", "2024-11-05"];
const json = (body, status = 200, extra = {}) =>
  new Response(body == null ? null : JSON.stringify(body), { status, headers: { "content-type": "application/json", ...extra } });
const rpcError = (id, code, message) => ({ jsonrpc: "2.0", id: id ?? null, error: { code, message } });

function authorised(req) {
  const key = process.env.MCP_API_KEY;
  if (!key) return true;
  const bearer = (req.headers.get("authorization") || "").replace(/^Bearer\s+/i, "");
  return req.headers.get("x-api-key") === key || bearer === key;
}

function handle(msg) {
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
        const out = callTool(dataset, params.name, params.arguments);
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
  if (req.method === "GET") return json({ error: "This MCP endpoint accepts POST (Streamable HTTP, no SSE stream)." }, 405, { allow: "POST" });
  if (req.method === "DELETE") return new Response(null, { status: 204 });
  if (req.method !== "POST") return json({ error: "Method not allowed" }, 405, { allow: "POST" });
  if (!authorised(req)) return json(rpcError(null, -32001, "Unauthorised: send the API key as x-api-key or Authorization: Bearer."), 401);
  let body;
  try { body = await req.json(); } catch { return json(rpcError(null, -32700, "Parse error"), 400); }
  if (Array.isArray(body)) {
    const out = body.map(handle).filter(Boolean);
    return out.length ? json(out) : new Response(null, { status: 202 });
  }
  const out = handle(body);
  return out ? json(out) : new Response(null, { status: 202 });
};

export const config = {
  path: "/mcp",
  method: ["GET", "POST", "DELETE"],
  rateLimit: { windowLimit: 120, windowSize: 60, aggregateBy: ["ip", "domain"] },
};
