"""The edition email: an intro written for the edition, approved with it, then sent on publish.

write_intro()  drafts a short newsletter introduction for the proposed edition (shown on the
               review page; the reviewer can replace it with /intro <text>).
render()       builds the email (subject + HTML using only tags Outlook keeps: p, b, i, a, ul,
               li, h3, hr, br).
queue()        on publish, adds the email to data/cxtime-outbox.json. A scheduled Claude task
               with the Microsoft 365 connector sends anything unsent from Group CX's mailbox
               and marks it sent, so each edition is emailed exactly once.
"""
import html
import json
from datetime import datetime, timezone

from .store import ROOT
from .llm import ask_json

OUTBOX = ROOT / "data" / "cxtime-outbox.json"

INTRO_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["intro"],
                "properties": {"intro": {"type": "string"}}}

INTRO_TASK = """Write the opening paragraph of this week's Aldar CX Time email to Aldar colleagues.
Start with "This week's edition is about" and name, in a few words, the single idea that connects
the stories. Then mention two or three of them concretely (what happens, where), and close by
saying each comes with what it could mean for Aldar. 50-80 words, one paragraph. Executive, warm,
UK spelling, no hype, no exclamation marks, no emoji, no invented facts: use only the stories below.

STORIES
"""


def write_intro(edition, conf):
    stories = "\n".join(f"- {'[LEAD] ' if i['lead'] else ''}{i['title']} ({i['source']}): {i['dek']}"
                        for i in edition["items"])
    return ask_json(conf["models"]["enrich"], "medium", "You write Aldar Group CX's weekly newsletter.",
                    INTRO_TASK + stories, INTRO_SCHEMA, max_tokens=4000)["intro"].strip()


def _e(s):
    return html.escape(s or "", quote=True)


def render(edition, intro, conf):
    """Short by design: what the edition is about, a link, and the list of stories."""
    nl = conf.get("newsletter", {})
    site, hub = nl.get("site_url", ""), nl.get("hub_url", "")
    subject = f"Aldar CX Time · Edition {edition['n']} · {edition['date']}"
    fmt = {"read": "", "watch": "Video · ", "listen": "Podcast · "}
    items = sorted(edition["items"], key=lambda i: not i["lead"])  # the lead first, no separate section
    H = [f"<p><b>Aldar CX Time</b> · Edition {edition['n']} · {_e(edition['date'])}</p>",
         f"<p>{_e(intro)}</p>"]
    if site:
        H.append(f'<p><a href="{_e(site)}"><b>Read the edition</b></a></p>')
    H.append("<ul>")
    for i in items:
        H.append(f'<li><a href="{_e(i["sourceUrl"])}">{_e(i["title"])}</a> · <i>{fmt[i["format"]]}{_e(i["source"])}</i></li>')
    H.append("</ul>")
    tail = "Group CX"
    if hub:
        tail = f'Also in the <a href="{_e(hub)}">Signature Experience Hub</a>.<br>Group CX'
    H.append(f"<p>{tail}</p>")
    return subject, "\n".join(H)


def load_outbox():
    return json.loads(OUTBOX.read_text()) if OUTBOX.exists() else {"emails": []}


def queue(edition, intro, conf):
    nl = conf.get("newsletter", {})
    to = nl.get("to", [])
    if not to:
        return None
    box = load_outbox()
    if any(m["edition"] == edition["n"] for m in box["emails"]):
        return None  # each edition is emailed once
    subject, body = render(edition, intro, conf)
    box["emails"].append({"edition": edition["n"], "date": edition["date"], "to": to, "cc": nl.get("cc", []),
                          "subject": subject, "html": body, "status": "pending",
                          "queuedAt": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    OUTBOX.write_text(json.dumps(box, ensure_ascii=False, indent=1) + "\n")
    return subject
