"""The edition announcement email (EDM design "4b Sadu Thread", docs/edm/README.md).

write_copy()  drafts the email's words for a proposed edition: preheader, headline, intro and, for
              the three featured stories (the lead, then the next two in edition order), who / kind /
              title / what. The subject is "Edition N · <headline>". Shown on the review page and
              approved with the edition; /subject, /headline, /intro and /pick override it. The email
              deliberately carries no "For Aldar" lines, so readers click through to the edition.
publish_edm() on publish, crops the photographs to JPEG, renders the designed email and writes it to
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

PICK = {"type": "object", "additionalProperties": False, "required": ["id", "who", "kind", "title", "what"],
        "properties": {k: {"type": "string"} for k in ("id", "who", "kind", "title", "what")}}
COPY_SCHEMA = {"type": "object", "additionalProperties": False,
               "required": ["preheader", "headline", "intro", "picks"],
               "properties": {"preheader": {"type": "string"},
                              "headline": {"type": "string"}, "intro": {"type": "string"},
                              "picks": {"type": "array", "items": PICK}}}

TASK = """Write the announcement email for this week's Aldar CX Time edition, sent to Aldar colleagues.
It features the three stories marked FEATURE, in that order. Use only facts in the material below.

- preheader: one line naming the three featured stories concretely; at most 100 characters.
- headline: the edition's idea in 2-5 words, ending with a full stop (e.g. "Worth leaving home for.").
- intro: 30-45 words. Start "This week's edition is about", name the idea, and end with
  "Three stories lead it, and each comes with what it could mean for Aldar."
- picks: one per FEATURE story, same order, with its id and:
  - who: the brand, venue or place at the heart of it, 1-4 words (not the publication).
  - kind: what kind of place or experience it is, 1-2 words (e.g. "Cinema domes", "Museum", "Showroom").
  - title: a fresh, concrete headline, at most 9 words.
  - what: one sentence, at most 25 words, saying what happens. Do not say what it means for Aldar.
Executive, warm, UK spelling, no hype, no exclamation marks, no emoji.

STORIES
"""


def featured(edition, picks=None):
    items = {i["id"]: i for i in edition["items"]}
    lead = next((i for i in edition["items"] if i["lead"]), edition["items"][0])
    rest = [items[p] for p in (picks or []) if p in items and p != lead["id"]]
    rest += [i for i in edition["items"] if i is not lead and i not in rest]
    return [lead] + rest[:2]


def write_copy(edition, conf, picks=None):
    feat = featured(edition, picks)
    ids = {i["id"] for i in feat}
    lines = []
    for i in edition["items"]:
        tag = f"FEATURE {[f['id'] for f in feat].index(i['id']) + 1}" if i["id"] in ids else "other"
        lines.append(json.dumps({"id": i["id"], "role": tag, "title": i["title"], "source": i["source"],
                                 "dek": i["dek"], "why": i["why"]}, ensure_ascii=False))
    out = ask_json(conf["models"]["enrich"], "medium", "You write Aldar Group CX's weekly CX Time email.",
                   TASK + "\n".join(lines), COPY_SCHEMA, max_tokens=6000)
    by = {p["id"]: p for p in out["picks"]}
    out["picks"] = [by.get(i["id"]) or fallback_pick(i) for i in feat]
    out["subject"] = subject_for(edition["n"], out["headline"])
    return out


def subject_for(n, headline):
    return f"Edition {n} · {' '.join(headline.split()).rstrip('.')}"


def fallback_pick(i):
    return {"id": i["id"], "who": i["sourceShort"], "kind": i.get("tag", ""), "title": i["title"], "what": i["dek"]}


def fallback_copy(edition):
    feat = featured(edition)
    return {"subject": subject_for(edition["n"], "This week in CX Time."),
            "preheader": " · ".join(i["title"] for i in feat)[:100],
            "headline": "This week in CX Time.",
            "intro": ("This week's edition is about experiences people choose to come back for. "
                      "Three stories lead it, and each comes with what it could mean for Aldar."),
            "picks": [fallback_pick(i) for i in feat]}


def publish_edm(edition, archive, copy, conf):
    """Render and write the designed email for a published edition. Returns (page URL, subject)."""
    nl = conf.get("newsletter", {})
    base = nl.get("site_url", "https://aldar-cx-time.netlify.app").rstrip("/")
    items = {i["id"]: i for i in edition["items"]}
    picks = [p for p in copy["picks"] if p["id"] in items][:3]
    imgs = archive.get("images", {})
    srcs = [ROOT / imgs[p["id"]].lstrip("/") if imgs.get(p["id"]) else None for p in picks]
    hero_url, thumb_urls = None, [None] * len(picks)
    if any(srcs):
        # the hero is the edition's mood: a photograph from a story the email doesn't feature, so
        # the lead's photo isn't shown twice in a row; the lead's own if there is no other
        picked = {p["id"] for p in picks}
        others = [ROOT / imgs[i["id"]].lstrip("/") for i in edition["items"] if i["id"] not in picked and imgs.get(i["id"])]
        hero_src = others[0] if others else next(s for s in srcs if s)
        hero_url, made = edm.make_images(edition["n"], hero_src, [s or hero_src for s in srcs], base)
        thumb_urls = [u if s else None for u, s in zip(made, srcs)]
    html = edm.render({
        "number": edition["n"], "date": edition["date"], "headline": copy["headline"], "intro": copy["intro"],
        "preheader": copy["preheader"], "editionUrl": base, "heroImage": hero_url, "assetsUrl": f"{base}/email/assets",
        "stories": [dict(p, image=u) for p, u in zip(picks, thumb_urls)],
    })
    out = ROOT / "sites" / "cx-time" / "email" / f"edition-{edition['n']}"
    out.mkdir(parents=True, exist_ok=True)
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
