// Ask Echo (and the page's other AI reads) POST here via window.SIG_AI_ENDPOINT.
// Contract set by the page's AI transport:
//   request  {system, messages:[{role,content}], max_tokens, model}
//   response {text}
// Credentials come from Netlify AI Gateway, injected at runtime — no key in this repo.
import Anthropic from "@anthropic-ai/sdk";

const MODEL = "claude-sonnet-5-5";
const MAX_TOKENS = 4096;

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

  try {
    const msg = await new Anthropic().messages.create({
      model: MODEL,
      max_tokens: Math.min(Number(body.max_tokens) || 1024, MAX_TOKENS),
      ...(body.system ? { system: String(body.system) } : {}),
      messages,
    });
    const text = msg.content.filter((p) => p.type === "text").map((p) => p.text).join("").trim();
    return Response.json({ text });
  } catch (e) {
    const status = e?.status && e.status >= 400 ? e.status : 502;
    return Response.json({ error: { message: e?.message || "AI request failed." } }, { status });
  }
};

export const config = {
  path: "/api/ai",
  method: "POST",
  // The page is public; cap requests per visitor so nobody can run up AI credits.
  rateLimit: { windowLimit: 20, windowSize: 60, aggregateBy: ["ip", "domain"] },
};
