// Signature experience submissions: business-line leads submit, Group CX reviews, approved
// records publish to the hub (index.html applies them as it loads) and to /mcp.
//
// Access: one code per business-line lead (kept in Blobs, managed from the review page) and
// a reviewer code (SX_REVIEWER_CODE env var). Codes are sent as the x-sx-code header.
// Storage: Netlify Blobs store "sx-submissions" (sub/<id>, published, leads, settings) and
// "sx-photos" (uploaded photos). Notifications: a Microsoft Teams Workflows webhook set on
// the review page; the same payload carries the email fields for the workflow's email step.
import { getStore } from "@netlify/blobs";
import { purgeCache } from "@netlify/functions";
import { randomUUID, randomBytes, timingSafeEqual } from "node:crypto";
import options from "./_data/sx-options.json" with { type: "json" };
import FEATURES from "../../features.json" with { type: "json" };
import { store, readPublished, liveDataset, invalidate } from "./_lib/live-data.mjs";
import "../../sx/sx-apply.js";

const SX = globalThis.SX_APPLY;
const LINES = Object.keys(SX.LINES).filter((l) => !(l === "pp" && FEATURES.project_plus === false)); // hidden lines take no submissions
const photos = () => getStore({ name: "sx-photos", consistency: "strong" });
const TAG = "sx-published";

class HttpError extends Error { constructor(status, message) { super(message); this.status = status; } }
const json = (body, status = 200, headers = {}) => new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json", "cache-control": "no-store", ...headers } });
const now = () => new Date().toISOString();
const str = (v, max = 4000) => (v == null ? "" : String(v)).trim().slice(0, max);
const same = (a, b) => { const x = Buffer.from(String(a)), y = Buffer.from(String(b)); return x.length === y.length && timingSafeEqual(x, y); };
const newCode = (line) => line.toUpperCase() + "-" + randomBytes(9).toString("base64url").toUpperCase().replace(/[^A-Z0-9]/g, "X").match(/.{1,4}/g).join("-");

// ---------- leads, settings, access ----------
async function getLeads() {
  const s = store();
  let leads = await s.get("leads", { type: "json" });
  if (!leads) { // first use: a code for every line
    leads = Object.fromEntries(LINES.map((l) => [l, { name: "", email: "", code: newCode(l), updated_at: now() }]));
    await s.setJSON("leads", leads);
  }
  return leads;
}
const getSettings = async () => (await store().get("settings", { type: "json" })) || { teams_webhook: "", reviewer_email: "", reviewer_name: "Group CX" };

async function who(req) {
  const code = str(req.headers.get("x-sx-code"), 100);
  if (!code) throw new HttpError(401, "Enter your access code.");
  const rev = process.env.SX_REVIEWER_CODE;
  if (rev && same(code, rev)) return { role: "reviewer", name: (await getSettings()).reviewer_name || "Group CX" };
  const leads = await getLeads();
  for (const [line, l] of Object.entries(leads)) if (l.code && LINES.includes(line) && same(code, l.code)) return { role: "lead", line, name: l.name || SX.LINES[line].short + " lead" };
  throw new HttpError(401, "That access code isn't recognised.");
}
const needReviewer = (u) => { if (u.role !== "reviewer") throw new HttpError(403, "Only the Group CX reviewer can do that."); };

// ---------- submissions ----------
const subKey = (id) => "sub/" + id;
async function getSub(id) { const s = await store().get(subKey(id), { type: "json" }); if (!s) throw new HttpError(404, "Submission not found."); return s; }
const putSub = (s) => store().setJSON(subKey(s.id), s);
async function allSubs() {
  const st = store(); const { blobs } = await st.list({ prefix: "sub/" });
  const out = await Promise.all(blobs.map((b) => st.get(b.key, { type: "json" })));
  return out.filter(Boolean).sort((a, b) => String(b.updated_at).localeCompare(String(a.updated_at)));
}

// clean and check the fields a lead (or the reviewer, when editing) sends
async function cleanFields(kind, line, exp_id, f = {}) {
  const O = options[line]; if (!O) throw new HttpError(400, "Unknown business line.");
  const errs = [];
  const out = {};
  const pick = (k, max) => { const v = str(f[k], max); if (v) out[k] = v; };
  const oneOf = (k, list) => { const v = str(f[k], 200); if (v && list.includes(v)) out[k] = v; else if (v) errs.push(`"${v}" is not a valid ${k.replace("_", " ")}.`); };
  const stageKeys = O.stages.map((s) => s.key);
  if (kind === "new") {
    pick("name", 90); pick("essence", 260); pick("narrative", 2000); pick("note", 1200); pick("photo", 300); pick("folder_url", 600);
    pick("moment", 300); pick("customer_benefit", 600); pick("aldar_benefit", 600);
    out.defining = !!f.defining;
    oneOf("stage", stageKeys); if (!out.stage) out.stage = stageKeys[0];
    if (O.pillars.length) oneOf("pillar", O.pillars.map((p) => p.id));
    if (O.journeys) oneOf("journey", O.journeys.map((j) => j.id));
    if (O.types) oneOf("type", O.types.map((t) => t.id));
    if (O.groups) pick("group", 120);
    if (O.cadence) pick("cadence", 60);
    if (O.capex) { pick("capex", 20); pick("evp", 40); }
    if (O.tiers) out.tiers = (Array.isArray(f.tiers) ? f.tiers : []).map((t) => str(t, 40)).filter((t) => O.tiers.includes(t));
    if (O.verticals) out.verticals = (Array.isArray(f.verticals) ? f.verticals : []).map((t) => str(t, 20)).filter((t) => O.verticals.some((v) => v.id === t));
    if (O.segment_multi) out.segment = (Array.isArray(f.segment) ? f.segment : [f.segment]).map((t) => str(t, 80)).filter(Boolean);
    else pick("segment", 120);
    out.touchpoints = (Array.isArray(f.touchpoints) ? f.touchpoints : String(f.touchpoints || "").split("\n")).map((t) => str(t, 200)).filter(Boolean).slice(0, 12);
    if (!out.name) errs.push("Name is required.");
    if (!out.essence) errs.push("Essence (one line) is required.");
    if (!out.narrative) errs.push("Narrative is required.");
    if (O.pillars.length && !out.pillar) errs.push("Choose a pillar.");
    if (!out.photo) errs.push("Add a photo.");
    if (O.has.target && f.target) { if (/^\d{4}-\d{2}$/.test(str(f.target))) out.target = str(f.target); else errs.push("Target go-live must be a month."); }
    if (out.name) {
      const D = await liveDataset();
      const dup = D.experiences.find((e) => e.line === line && e.name.toLowerCase() === out.name.toLowerCase());
      if (dup) errs.push(`"${dup.name}" already exists in ${SX.LINES[line].short}. Submit an update to it instead.`);
    }
  } else {
    const D = await liveDataset();
    const cur = D.experiences.find((e) => e.line === line && e.id === exp_id);
    if (!cur) throw new HttpError(400, "Choose one of your line's experiences to update.");
    pick("note", 1200); pick("essence", 260); pick("narrative", 2000); pick("photo", 300);
    if (f.stage) oneOf("stage", stageKeys);
    if (O.has.target && f.target !== undefined && f.target !== null && f.target !== "") { if (/^\d{4}-\d{2}$/.test(str(f.target))) out.target = str(f.target); else errs.push("Target go-live must be a month."); }
    if (Array.isArray(f.impl_photos)) {
      out.impl_photos = f.impl_photos.map((x) => ({ src: str(x && x.src, 300), asset: str(x && x.asset, 120), caption: str(x && x.caption, 200) }))
        .filter((x) => /^\/api\/sx\/photo\/[a-f0-9]{32}$/.test(x.src)).slice(0, 24);
      if (!out.impl_photos.length) delete out.impl_photos;
    }
    if (!out.note && out.impl_photos) out.note = out.impl_photos.length + (out.impl_photos.length === 1 ? " photo" : " photos") + " from the live experience.";
    if (!out.note) errs.push("Add an update note: what changed?");
  }
  if (O.has.assets && Array.isArray(f.assets)) {
    const known = new Set(O.assets.map((a) => a.name));
    out.assets = f.assets.map((a) => ({ name: str(a && a.name, 120), live: !!(a && a.live) })).filter((a) => a.name && (known.has(a.name) || kind === "update")).slice(0, 60);
  }
  if (errs.length) throw new HttpError(422, errs.join(" "));
  return out;
}

function summaryOf(s) {
  const f = s.fields || {};
  return s.kind === "new" ? f.name : (s.exp_name || s.exp_id);
}

// ---------- notifications (Teams Workflows webhook; the workflow also sends the email) ----------
async function notify(event, sub, extra = {}) {
  try {
    const settings = await getSettings();
    if (!settings.teams_webhook) return { sent: false, reason: "No Teams webhook set." };
    const leads = await getLeads();
    const lead = leads[sub.line] || {};
    const site = process.env.URL || "https://aldar-signature-experience.netlify.app";
    const link = site + "/sx/" + (event === "submitted" || event === "resubmitted" ? "#review/" : "#mine/") + sub.id;
    const lineLabel = SX.LINES[sub.line].label;
    const what = sub.kind === "new" ? "new experience" : "update";
    const titles = {
      submitted: `New ${what} to review: ${summaryOf(sub)}`,
      resubmitted: `Resubmitted for review: ${summaryOf(sub)}`,
      approved: `Approved and published: ${summaryOf(sub)}`,
      returned: `Sent back for changes: ${summaryOf(sub)}`,
      rejected: `Not approved: ${summaryOf(sub)}`,
      test: "Test notification from the Signature Experience Hub",
    };
    const toReviewer = event === "submitted" || event === "resubmitted" || event === "test";
    const title = titles[event] || event;
    const f = sub.fields || {};
    const facts = [
      { title: "Business line", value: lineLabel },
      { title: "Type", value: sub.kind === "new" ? "New experience" : "Update to an existing experience" },
      { title: "From", value: sub.lead || lead.name || "Line lead" },
      ...(f.stage ? [{ title: "Stage", value: SX.STAGE_LABEL[f.stage] || f.stage }] : []),
      ...(f.target ? [{ title: "Target go-live", value: f.target }] : []),
    ];
    const text = extra.comment ? `Comment: ${extra.comment}` : (sub.kind === "new" ? f.essence || "" : f.note || "");
    const html = `<p><b>${esc(title)}</b></p>${facts.map((x) => `<p>${esc(x.title)}: ${esc(x.value)}</p>`).join("")}${text ? `<p>${esc(text)}</p>` : ""}<p><a href="${link}">Open in the hub</a></p>`;
    const payload = {
      type: "message",
      attachments: [{
        contentType: "application/vnd.microsoft.card.adaptive", contentUrl: null,
        content: {
          $schema: "http://adaptivecards.io/schemas/adaptive-card.json", type: "AdaptiveCard", version: "1.4",
          body: [
            { type: "TextBlock", text: "Signature Experience Hub", size: "Small", isSubtle: true },
            { type: "TextBlock", text: title, weight: "Bolder", size: "Medium", wrap: true },
            ...(text ? [{ type: "TextBlock", text, wrap: true }] : []),
            { type: "FactSet", facts },
          ],
          actions: [{ type: "Action.OpenUrl", title: toReviewer ? "Review it" : "Open in the hub", url: link }],
        },
      }],
      // for the workflow's "Send an email" step
      event, subject: title, html, text, link,
      email_to: toReviewer ? (settings.reviewer_email || "") : (lead.email || settings.reviewer_email || ""),
      line: lineLabel,
    };
    const r = await fetch(settings.teams_webhook, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(payload) });
    console.log(JSON.stringify({ sx: "notify", event, id: sub.id, status: r.status }));
    return { sent: r.ok, status: r.status };
  } catch (e) {
    console.log(JSON.stringify({ sx: "notify-failed", event, message: String(e?.message || e) }));
    return { sent: false, reason: String(e?.message || e) };
  }
}
const esc = (s) => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

async function publishList(mutator) {
  const list = await readPublished();
  const next = mutator(list);
  await store().setJSON("published", next);
  invalidate();
  try { await purgeCache({ tags: [TAG] }); } catch (e) { console.log(JSON.stringify({ sx: "purge-failed", message: String(e?.message || e) })); }
  return next;
}

// ---------- routes ----------
export default async (req, context) => {
  const url = new URL(req.url);
  const parts = url.pathname.replace(/^\/api\/sx\/?/, "").split("/").filter(Boolean);
  const [a, b, c] = parts;
  try {
    // public: what the hub and /mcp apply
    if (req.method === "GET" && a === "published") {
      const records = await readPublished();
      return new Response(JSON.stringify({ records, at: now() }), {
        headers: { "content-type": "application/json", "cache-control": "public, max-age=0, must-revalidate", "netlify-cdn-cache-control": "public, durable, s-maxage=300, stale-while-revalidate=60", "netlify-cache-tag": TAG },
      });
    }
    // public: uploaded photos (unguessable keys)
    if (req.method === "GET" && a === "photo" && b) {
      const r = await photos().getWithMetadata(b, { type: "arrayBuffer" });
      if (!r) return new Response("Not found", { status: 404 });
      return new Response(r.data, { headers: { "content-type": r.metadata?.type || "image/jpeg", "cache-control": "public, max-age=31536000, immutable" } });
    }

    const u = await who(req);

    if (req.method === "POST" && a === "session") {
      const D = await liveDataset({ fresh: true });
      const lines = u.role === "reviewer" ? LINES : [u.line];
      const experiences = D.experiences.filter((e) => lines.includes(e.line)).map((e) => ({
        id: e.id, line: e.line, name: e.name, stage: e.stage, stage_key: e.stage_key, target: e.target_go_live, target_sort: e.target_sort, essence: e.essence, image_url: e.image_url,
        assets: (e.deployment?.assets || []).map((x) => ({ name: x.name, live: !!x.live })),
      }));
      const out = { role: u.role, line: u.line || null, name: u.name, options: Object.fromEntries(lines.map((l) => [l, options[l]])), experiences };
      if (u.role === "reviewer") { out.settings = await getSettings(); const L = await getLeads(); out.leads = Object.fromEntries(Object.entries(L).filter(([l]) => LINES.includes(l))); }
      return json(out);
    }

    if (req.method === "POST" && a === "photo") {
      const type = (req.headers.get("content-type") || "").split(";")[0];
      if (!/^image\/(jpeg|png|webp)$/.test(type)) throw new HttpError(415, "Photos must be JPEG, PNG or WebP.");
      const buf = await req.arrayBuffer();
      if (buf.byteLength > 4 * 1024 * 1024) throw new HttpError(413, "That photo is over 4 MB.");
      const key = randomUUID().replace(/-/g, "");
      await photos().set(key, buf, { metadata: { type, by: u.role === "lead" ? u.line : "reviewer", at: now() } });
      return json({ url: "/api/sx/photo/" + key });
    }

    if (a === "submissions" && !b && req.method === "GET") {
      let subs = await allSubs();
      if (u.role === "lead") subs = subs.filter((s) => s.line === u.line);
      return json({ submissions: subs });
    }

    if (a === "submissions" && !b && req.method === "POST") {
      const body = await req.json();
      const line = u.role === "lead" ? u.line : str(body.line, 10);
      if (!LINES.includes(line)) throw new HttpError(400, "Unknown business line.");
      const kind = body.kind === "update" ? "update" : "new";
      const fields = await cleanFields(kind, line, str(body.exp_id, 120), body.fields);
      const D = await liveDataset();
      let exp_id, exp_name;
      if (kind === "new") {
        const slug = SX.slug(fields.name);
        exp_id = "sx-" + slug + "-" + randomBytes(2).toString("hex");
      } else { exp_id = str(body.exp_id, 120); exp_name = D.experiences.find((e) => e.id === exp_id)?.name; }
      const sub = {
        id: randomUUID(), kind, line, exp_id, exp_name, status: "pending", fields, lead: u.name, by_role: u.role,
        created_at: now(), updated_at: now(), history: [{ at: now(), by: u.name, action: "submitted" }],
      };
      await putSub(sub);
      const n = await notify("submitted", sub);
      return json({ submission: sub, notified: n.sent });
    }

    if (a === "submissions" && b && req.method === "POST") {
      const sub = await getSub(b);
      if (u.role === "lead" && sub.line !== u.line) throw new HttpError(403, "That submission belongs to another line.");
      const body = await req.json().catch(() => ({}));
      if (c === "withdraw") {
        if (!["pending", "returned"].includes(sub.status)) throw new HttpError(409, "Only pending or returned submissions can be withdrawn.");
        sub.status = "withdrawn"; sub.updated_at = now(); sub.history.push({ at: now(), by: u.name, action: "withdrawn" });
        await putSub(sub); return json({ submission: sub });
      }
      // resubmit with changes
      if (!["pending", "returned"].includes(sub.status)) throw new HttpError(409, "This submission has already been decided.");
      sub.fields = await cleanFields(sub.kind, sub.line, sub.exp_id, body.fields);
      const was = sub.status;
      sub.status = "pending"; sub.updated_at = now(); sub.history.push({ at: now(), by: u.name, action: was === "returned" ? "resubmitted" : "edited" });
      await putSub(sub);
      if (was === "returned") await notify("resubmitted", sub);
      return json({ submission: sub });
    }

    if (a === "review" && b && req.method === "POST") {
      needReviewer(u);
      const sub = await getSub(b);
      const body = await req.json();
      const action = str(body.action, 20), comment = str(body.comment, 1500);
      if (action === "unpublish") {
        if (sub.status !== "approved") throw new HttpError(409, "Only published submissions can be unpublished.");
        await publishList((list) => list.filter((r) => r.id !== sub.id));
        sub.status = "unpublished"; sub.updated_at = now(); sub.history.push({ at: now(), by: u.name, action: "unpublished", comment });
        await putSub(sub); return json({ submission: sub });
      }
      if (!["pending"].includes(sub.status)) throw new HttpError(409, "Only pending submissions can be reviewed.");
      if (action === "approve") {
        if (body.fields) { sub.original_fields = sub.original_fields || sub.fields; sub.fields = await cleanFields(sub.kind, sub.line, sub.exp_id, body.fields); }
        const rec = { id: sub.id, kind: sub.kind, line: sub.line, exp_id: sub.exp_id, fields: sub.fields, lead: sub.lead, approved_at: now(), approved_by: u.name };
        await publishList((list) => list.filter((r) => r.id !== sub.id).concat([rec]));
        sub.status = "approved"; sub.approved_at = rec.approved_at;
      } else if (action === "return") {
        if (!comment) throw new HttpError(422, "Add a comment so the lead knows what to change.");
        sub.status = "returned";
      } else if (action === "reject") {
        sub.status = "rejected";
      } else throw new HttpError(400, "Unknown action.");
      sub.reviewer_comment = comment || sub.reviewer_comment || ""; sub.updated_at = now();
      sub.history.push({ at: now(), by: u.name, action: { approve: "approved", return: "returned", reject: "rejected" }[action], comment });
      await putSub(sub);
      const n = await notify({ approve: "approved", return: "returned", reject: "rejected" }[action], sub, { comment });
      return json({ submission: sub, notified: n.sent });
    }

    if (a === "leads" && req.method === "POST") {
      needReviewer(u);
      const body = await req.json();
      const line = str(body.line, 10); if (!LINES.includes(line)) throw new HttpError(400, "Unknown business line.");
      const leads = await getLeads();
      const l = leads[line] || {};
      if (body.name !== undefined) l.name = str(body.name, 80);
      if (body.email !== undefined) l.email = str(body.email, 120);
      if (body.regenerate) l.code = newCode(line);
      l.updated_at = now(); leads[line] = l;
      await store().setJSON("leads", leads);
      return json({ leads });
    }

    if (a === "settings" && req.method === "POST") {
      needReviewer(u);
      const body = await req.json();
      const s = await getSettings();
      if (body.teams_webhook !== undefined) {
        const w = str(body.teams_webhook, 2000);
        if (w && !/^https:\/\//.test(w)) throw new HttpError(422, "The webhook must be an https:// URL.");
        s.teams_webhook = w;
      }
      if (body.reviewer_email !== undefined) s.reviewer_email = str(body.reviewer_email, 120);
      if (body.reviewer_name !== undefined) s.reviewer_name = str(body.reviewer_name, 80) || "Group CX";
      await store().setJSON("settings", s);
      if (body.test) {
        const n = await notify("test", { id: "test", kind: "new", line: "hp", lead: "Test", fields: { name: "Test notification", essence: "If you can read this, notifications work." } });
        return json({ settings: s, test: n });
      }
      return json({ settings: s });
    }

    throw new HttpError(404, "Not found.");
  } catch (e) {
    if (e instanceof HttpError) return json({ error: e.message }, e.status);
    console.log(JSON.stringify({ sx: "error", path: url.pathname, message: String(e?.stack || e) }));
    return json({ error: "Something went wrong. Please try again." }, 500);
  }
};

export const config = {
  path: "/api/sx/*",
  rateLimit: { windowLimit: 600, windowSize: 60, aggregateBy: ["ip", "domain"] }, // generous: offices share one IP
};
