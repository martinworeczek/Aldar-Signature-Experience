// Ask Echo (and the page's other AI reads) POST here via window.SIG_AI_ENDPOINT.
// Contract set by the page's AI transport:
//   request  {system, messages:[{role,content}], max_tokens, model}
//   response {text}
// Credentials come from Netlify AI Gateway, injected at runtime — no key in this repo.
import Anthropic from "@anthropic-ai/sdk";

const MODEL = "claude-sonnet-5-5";
const MIN_TOKENS = 2048; // Echo asks for 900, which can cut a structured JSON answer mid-object
const MAX_TOKENS = 4096;
const WANTS_JSON = /respond with only a raw json object/i;

// The page parses the first "{" to the last "}" as JSON; check the reply will survive that.
const parsesAsJson = (text) => {
  const a = text.indexOf("{"), b = text.lastIndexOf("}");
  if (a < 0 || b <= a) return false;
  try { JSON.parse(text.slice(a, b + 1)); return true; } catch { return false; }
};

export default async (req) => {
  if (!process.env.ANTHROPIC_BASE_URL) {
    return Response.json({ error: { message: "AI Gateway is not active for this site." } }, { status: 503 });
  }

  let body;
  try {
    body = await req.json();
  } catch {
    return Response.json({ error: { message: "Request body must be JSON." } }, { status: 400 });
  }

  const messages = (Array.isArray(body.messages) ? body.messages : [])
    .map((m) => ({ role: m.role === "assistant" ? "assistant" : "user", content: String(m.content ?? "") }))
    .filter((m) => m.content.trim() !== "");
  if (!messages.length) {
    return Response.json({ error: { message: "No messages supplied." } }, { status: 400 });
  }

  const system = body.system ? String(body.system) : "";
  const wantsJson = WANTS_JSON.test(system);
  const maxTokens = Math.min(Math.max(Number(body.max_tokens) || 1024, MIN_TOKENS), MAX_TOKENS);
  const client = new Anthropic();

  const ask = async (msgs) => {
    const t0 = Date.now();
    const msg = await client.messages.create({
      model: MODEL,
      max_tokens: maxTokens,
      // Echo resends ~25k tokens of repository data every turn; cache it between turns.
      ...(system ? { system: [{ type: "text", text: system, cache_control: { type: "ephemeral" } }] } : {}),
      messages: msgs,
    });
    const text = msg.content.filter((p) => p.type === "text").map((p) => p.text).join("").trim();
    const ok = !wantsJson || parsesAsJson(text);
    console.log(JSON.stringify({
      ai: "reply", ms: Date.now() - t0, stop: msg.stop_reason, json: wantsJson ? ok : null,
      in: msg.usage?.input_tokens, cached: msg.usage?.cache_read_input_tokens, out: msg.usage?.output_tokens,
      head: text.slice(0, 160),
    }));
    return { text, ok, stop: msg.stop_reason };
  };

  try {
    let r = await ask(messages);
    if (wantsJson && !r.ok) {
      // one corrective retry: same conversation, with the reply that broke the contract shown back
      r = await ask(messages.concat(
        { role: "assistant", content: r.text || "(empty)" },
        { role: "user", content: "That reply was not a single valid JSON object. Reply again with ONLY the raw JSON object in the required shape: no prose, no markdown fences, and keep every string short." }
      ));
    }
    return Response.json({ text: r.text });
  } catch (e) {
    const status = e?.status && e.status >= 400 ? e.status : 502;
    console.log(JSON.stringify({ ai: "error", status, message: String(e?.message || e).slice(0, 300) }));
    return Response.json({ error: { message: e?.message || "AI request failed." } }, { status });
  }
};

export const config = {
  path: "/api/ai",
  method: "POST",
  // The page is public; cap requests per visitor so nobody can run up AI credits.
  rateLimit: { windowLimit: 20, windowSize: 60, aggregateBy: ["ip", "domain"] },
};
