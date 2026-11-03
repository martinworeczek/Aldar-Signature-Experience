"""The edition announcement email (EDM design "5a Top Five", docs/edm/README.md).

top_five()    the stories the email carries: the lead first, then the highest relevance in edition
              order (an editor's /pick takes precedence), up to five.
write_copy()  drafts the email's only editorial line, the preheader, and sets the subject
              "Aldar CX Times · Edition N — the top five". Shown on the review page and approved
              with the edition; /subject, /preheader and /pick override it. Everything else in the
              email is the edition's own data: title, dek and the curated "why", verbatim.
publish_edm() on publish, cuts the board photographs, renders the designed email and writes it to
              sites/cx-time/email/edition-N/index.html, so it is hosted with the CX Time site. The
              file is then dropped into OneDrive "CX Times/Outbox", where a Power Automate flow sends
              it as the email body (the pipeline's own mail connector strips images and styling).
"""
import json
from datetime import datetime, timezone

from . import edm
from .llm import ask_json
from .store import ROOT

LOG = ROOT / "data" / "cxtime-outbox.json"
SHOW = 5

COPY_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["preheader"],
               "properties": {"preheader": {"type": "string"}}}

TASK = """Write the hidden preview line (preheader) for this week's Aldar CX Times announcement email,
sent to Aldar colleagues. The email carries the stories below, in this order.
One line, at most 100 characters: name the first two stories concretely by what happens in them,
then end with "and {more} more stories for Aldar." Use only facts in the material below.
Executive, warm, UK spelling, no hype, no exclamation marks, no emoji.
Example: "Oura's survey-free CX score, wellness inside everyday purchases, and three more stories for Aldar."

STORIES
"""

WORDS = {1: "one", 2: "two", 3: "three", 4: "four"}


def top_five(edition, picks=None):
    items = edition["items"]
    lead = next((i for i in items if i.get("lead")), items[0])
    by = {i["id"]: i for i in items}
    chosen = [lead] + [by[p] for p in (picks or []) if p in by and p != lead["id"]]
    order = {i["id"]: k for k, i in enumerate(items)}
    rest = sorted((i for i in items if i not in chosen), key=lambda i: (-(i.get("relevance") or 0), order[i["id"]]))
    chosen = (chosen + rest)[:SHOW]
    return [lead] + sorted(chosen[1:], key=lambda i: order[i["id"]])


def subject_for(n):
    return f"Aldar CX Times · Edition {n} — the top five"


def write_copy(edition, conf, picks=None):
    feat = top_five(edition, picks)
    more = WORDS.get(len(feat) - 2, str(len(feat) - 2))
    lines = [json.dumps({"title": i["title"], "dek": i["dek"]}, ensure_ascii=False) for i in feat]
    out = ask_json(conf["models"]["enrich"], "low", "You write Aldar Group CX's weekly CX Times email.",
                   TASK.replace("{more}", more) + "\n".join(lines), COPY_SCHEMA, max_tokens=1000)
    return {"subject": subject_for(edition["n"]), "preheader": out["preheader"][:140],
            "picks": [i["id"] for i in feat]}


def fallback_copy(edition):
    feat = top_five(edition)
    return {"subject": subject_for(edition["n"]),
            "preheader": " · ".join(i["title"] for i in feat[:2])[:100],
            "picks": [i["id"] for i in feat]}


def publish_edm(edition, archive, copy, conf):
    """Render and write the designed email for a published edition. Returns (page URL, subject)."""
    nl = conf.get("newsletter", {})
    base = nl.get("site_url", "https://aldar-cx-time.netlify.app").rstrip("/")
    by = {i["id"]: i for i in edition["items"]}
    stories = [by[p] for p in copy.get("picks", []) if p in by] or top_five(edition)
    imgs = archive.get("images", {})
    srcs = [ROOT / imgs[s["id"]].lstrip("/") if imgs.get(s["id"]) else None for s in stories]
    urls = edm.make_images(edition["n"], srcs, base)
    credits = []
    for s, u in zip(stories, urls):
        c = (s.get("imageCredit") or "").strip()
        if u and c and c not in credits:
            credits.append(c)
    html = edm.render({
        "number": edition["n"], "date": edition["date"], "preheader": copy["preheader"],
        "editionUrl": base, "assetsUrl": f"{base}/email/assets", "total": len(edition["items"]),
        "credits": credits, "stories": [dict(s, image=u) for s, u in zip(stories, urls)],
    })
    out = ROOT / "sites" / "cx-time" / "email" / f"edition-{edition['n']}"
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.jpg"):  # earlier designs' crops
        if not old.name.startswith("top5-"):
            old.unlink()
    (out / "index.html").write_text(html, encoding="utf-8")
    url = f"{base}/email/edition-{edition['n']}/"
    log = json.loads(LOG.read_text()) if LOG.exists() else {"emails": []}
    if not any(m["edition"] == edition["n"] for m in log["emails"]):
        log["emails"].append({"edition": edition["n"], "date": edition["date"], "subject": copy["subject"],
                              "to": nl.get("to", []), "page": url, "file": f"sites/cx-time/email/edition-{edition['n']}/index.html",
                              "status": "ready: drop into OneDrive CX Times/Outbox to send",
                              "builtAt": datetime.now(timezone.utc).isoformat(timespec="seconds")})
        LOG.write_text(json.dumps(log, ensure_ascii=False, indent=1) + "\n")
    return url, copy["subject"]
