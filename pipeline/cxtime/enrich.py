"""Step 2 - Enrich & Map, plus an independent fact-check.

screen():  cheap first pass on metadata (title + excerpt) -> experiential score per candidate.
enrich():  the full read -> one schema-valid record, or a reasoned drop.
verify():  a second, separate read of the source checks every claim in the record; one
           rewrite is attempted on failure, and anything still unsupported is flagged for review.
"""
import json
from datetime import datetime

from .llm import ask_json, LLMError

LINES = ["Hospitality", "Retail", "Education", "Development", "Community", "PM & Leasing", "Corporate", "All lines"]
INSIGHTS = ["Trend", "Case study", "Benchmark", "Innovation", "Research", "Leadership", ""]

BRIEF = """You are the editor of Aldar CX Time, a weekly briefing curated by Aldar Group CX
(Aldar Properties, Abu Dhabi) for its executives. Each edition carries a handful of the
world's best EXPERIENTIAL customer-experience stories, each with what it means for Aldar.

WHAT COUNTS AS EXPERIENTIAL CX
A story about how people actually experience a moment, place, service or journey, and how an
organisation deliberately designed, staged, changed or measured that experience. People means
guests, shoppers, residents, students and parents, visitors, tenants or employees.
It must contain a concrete, real example: a named brand, venue, place, programme or study of
lived experience. And it must hold an idea Aldar could transfer.

In scope: signature moments; arrival, welcome and departure rituals; sensory and spatial design;
hospitality service rituals; experiential retail and destinations; placemaking and community
life; events and brand activations; personalisation and recognition the customer can feel;
loyalty that feels like belonging; service recovery; wellbeing experiences; student and parent
journeys; workplace experience. Technology and AI only when it changes what a person feels in
the moment, not when it only cuts cost.

Out of scope: earnings, deals, M&A and openings with no experiential detail; executive moves;
vendor and product announcements; contact-centre efficiency or cost stories; CX metrics or
opinion pieces with no concrete experience; advertising campaigns; politics; thin listicles.

The coverage is GLOBAL. Do not favour or require a Gulf or Middle East angle; judge only on
how strong, concrete and transferable the experience is.

ALDAR'S BUSINESS LINES (for mapping and for "why it matters")
- Hospitality: hotels, resorts, F&B and leisure; the guest stay.
- Retail: shopping malls and retail destinations; the shopper and visitor journey.
- Education: schools; the student and parent journey.
- Development: master-planned communities and homes; buying, handover and moving in.
- Community: life in Aldar's neighbourhoods; public realm, amenities, events, belonging.
- PM & Leasing: property and facilities management, resident and tenant services, leasing.
- Corporate: Aldar's own employees and workplace.
- All lines: only when genuinely portfolio-wide.
Never invent facts about Aldar, its assets, projects or numbers. Speak about the line or the
moment, not about named Aldar properties.

HOUSE STYLE
Executive, concise, UK spelling (personalising, programmes, centre). Calm and specific; no hype,
no exclamation marks, no emoji. Faithful to the source: no invented figures, names or quotes.
Original prose: never copy sentences from the source."""

SCREEN_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["items"],
    "properties": {"items": {"type": "array", "items": {
        "type": "object", "additionalProperties": False, "required": ["key", "experiential", "reason"],
        "properties": {"key": {"type": "string"}, "experiential": {"type": "integer"}, "reason": {"type": "string"}}}}},
}

OPP = {"type": "object", "additionalProperties": False, "required": ["line", "title", "text"],
       "properties": {"line": {"type": "string", "enum": LINES[:-1]}, "title": {"type": "string"}, "text": {"type": "string"}}}

ENRICH_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["keep", "dropReason", "experiential", "relevance", "tag", "lines", "insight", "themes",
                 "title", "dek", "summary", "why", "excerpt", "opps", "keyInsights", "speakers"],
    "properties": {
        "keep": {"type": "boolean"},
        "dropReason": {"type": "string"},
        "experiential": {"type": "integer"},
        "relevance": {"type": "integer"},
        "tag": {"type": "string", "enum": ["Hospitality", "Retail", "Education", "Development", "Workplace",
                                           "AI & Tech", "Design", "Foresight", "Portfolio"]},
        "lines": {"type": "array", "items": {"type": "string", "enum": LINES}},
        "insight": {"type": "string", "enum": INSIGHTS},
        "themes": {"type": "array", "items": {"type": "string"}},
        "title": {"type": "string"},
        "dek": {"type": "string"},
        "summary": {"type": "array", "items": {"type": "string"}},
        "why": {"type": "string"},
        "excerpt": {"type": "string"},
        "opps": {"type": "array", "items": OPP},
        "keyInsights": {"type": "array", "items": {"type": "string"}},
        "speakers": {"type": "array", "items": {"type": "string"}},
    },
}

VERIFY_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["issues"],
    "properties": {"issues": {"type": "array", "items": {
        "type": "object", "additionalProperties": False, "required": ["field", "claim", "problem"],
        "properties": {"field": {"type": "string"}, "claim": {"type": "string"}, "problem": {"type": "string"}}}}},
}


def screen(cands, cfg):
    """Metadata-only screen. Returns {key: (score 1-5, reason)}."""
    out = {}
    for i in range(0, len(cands), 40):
        batch = cands[i:i + 40]
        lines = [json.dumps({"key": c["key"], "format": c["formatHint"], "source": c["source"],
                             "title": c["titleRaw"], "excerpt": c["excerpt"][:400],
                             "categories": c["categories"]}, ensure_ascii=False) for c in batch]
        user = ("Screen these candidates on their metadata only. For each, score `experiential` 1-5: "
                "5 = a vivid, concrete experiential story with a clear transferable idea; 3 = possibly "
                "experiential but unclear from the metadata; 1 = out of scope. Give a reason of at most "
                "12 words. Return every key.\n\n" + "\n".join(lines))
        res = ask_json(cfg["models"]["screen"], cfg["models"]["screen_effort"], BRIEF, user, SCREEN_SCHEMA)
        for r in res["items"]:
            out[r["key"]] = (max(1, min(5, int(r["experiential"]))), r["reason"])
    return out


def _source_block(c):
    head = {"format": c["formatHint"], "source": c["source"], "url": c["sourceUrl"], "title": c["titleRaw"],
            "published": c["publishedRaw"][:10], "author": c.get("author") or "",
            "credited speakers": c.get("speakersRaw") or []}
    kind = {"read": "ARTICLE TEXT", "watch": "VIDEO DESCRIPTION", "listen": "EPISODE NOTES"}[c["formatHint"]]
    return json.dumps(head, ensure_ascii=False) + f"\n\n<{kind}>\n{c['sourceText']}\n</{kind}>"


ENRICH_TASK = """Read the source below and decide whether it belongs in Aldar CX Time.

Score `experiential` 1-5 (how squarely it is about a lived, designed experience with a concrete
example) and `relevance` 1-5 (strategic value to Aldar: breadth of lines it informs x strength
and buildability of the idea x timeliness). Set keep=false with a one-line dropReason when it is
out of scope, too thin, or not genuinely experiential; still fill the other fields briefly.

When keep=true, write:
- title: the story's own headline lightly tidied to sentence case, faithful to the source.
- dek: one standfirst sentence, at most 30 words.
- summary: exactly 3 original sentences, the executive summary. Characterise; do not quote.
- why: "why it matters to Aldar", 1-2 sentences naming a specific line and a specific moment
  (arrival, handover, first day of school, a mall visit, move-in...). Never generic.
- excerpt: a short pull-quote. Prefer paraphrase. A verbatim quote must be under 25 words,
  in quotation marks and attributed ("... " - Name).
- lines: the Aldar lines that would act on it (1-3; 'All lines' only if truly portfolio-wide).
- opps: one Signature Experience to explore for EACH specific line in `lines` (for 'All lines',
  pick the 2-3 lines it fits best). title = a 2-5 word name; text = one concrete, buildable
  sentence describing what a customer would experience.
- tag: the subject (Hospitality, Retail, Education, Development, Workplace, AI & Tech, Design,
  Foresight, Portfolio). insight: Trend, Case study, Benchmark, Innovation, Research or
  Leadership, or '' if none fits.
- themes: 2-4 lowercase keywords. keyInsights: 2-4 transferable takeaway sentences.
- speakers: for video and podcast, hosts and guests as credited in the source; [] otherwise.
  Never guess a name.
"""


def enrich(c, cfg, feedback=None):
    user = ENRICH_TASK + "\n\nSOURCE\n" + _source_block(c)
    if feedback:
        user += ("\n\nA fact-check of your previous draft found these problems. Rewrite so that every "
                 "statement is supported by the source, or remove it:\n" + json.dumps(feedback, ensure_ascii=False))
    rec = ask_json(cfg["models"]["enrich"], cfg["models"]["enrich_effort"], BRIEF, user, ENRICH_SCHEMA)
    rec["experiential"] = max(1, min(5, int(rec["experiential"])))
    rec["relevance"] = max(1, min(5, int(rec["relevance"])))
    return rec


VERIFY_TASK = """You are the fact-checker. Compare the DRAFT with the SOURCE.
List every statement in title, dek, summary, why, excerpt, opps and keyInsights that states a
fact (a number, name, date, claim about what happened, or a quote) not supported by the source,
and any quote that is verbatim but over 25 words or unattributed. Recommendations and opinions
about what Aldar could do are fine and are not issues. Return an empty list if all is supported."""


def verify(c, rec, cfg):
    draft = {k: rec[k] for k in ("title", "dek", "summary", "why", "excerpt", "opps", "keyInsights", "speakers")}
    user = VERIFY_TASK + "\n\nDRAFT\n" + json.dumps(draft, ensure_ascii=False, indent=1) + "\n\nSOURCE\n" + _source_block(c)
    return ask_json(cfg["models"]["verify"], cfg["models"]["verify_effort"],
                    "You check editorial drafts against their sources, strictly and briefly.", user, VERIFY_SCHEMA)["issues"]


def validate(rec):
    """House rules the schema cannot express. Returns a list of problems (empty = valid)."""
    p = []
    if len(rec["summary"]) != 3:
        p.append(f"summary has {len(rec['summary'])} sentences, not 3")
    if len(rec["dek"].split()) > 34:
        p.append("dek longer than 30 words")
    if not rec["lines"]:
        p.append("no business line")
    if not (2 <= len(rec["themes"]) <= 4):
        p.append("themes must be 2-4")
    if not (2 <= len(rec["keyInsights"]) <= 4):
        p.append("keyInsights must be 2-4")
    if not rec["opps"]:
        p.append("no Signature Experience")
    q = rec["excerpt"]
    if '"' in q or "“" in q:
        quoted = q.split('"')[1] if q.count('"') >= 2 else q
        if len(quoted.split()) >= 25:
            p.append("quoted excerpt is 25 words or more")
    for f in ("title", "dek", "why", "excerpt"):
        if not rec[f].strip():
            p.append(f"empty {f}")
    return p


def enrich_and_check(c, cfg):
    """Full B step for one candidate. Returns (record or None, flags, drop_reason)."""
    rec = enrich(c, cfg)
    if not rec["keep"]:
        return None, [], rec["dropReason"] or "not experiential enough"
    issues = verify(c, rec, cfg)
    if issues:
        rec = enrich(c, cfg, feedback=issues)
        if not rec["keep"]:
            return None, [], rec["dropReason"] or "dropped on rewrite"
        issues = verify(c, rec, cfg)
    flags = [f"fact-check: {i['field']}: {i['claim']} ({i['problem']})" for i in issues]
    problems = validate(rec)
    if problems:
        return None, [], "invalid record: " + "; ".join(problems)
    return rec, flags, None
