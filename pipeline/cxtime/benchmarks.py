"""Feeding the Benchmark Repository from Aldar CX Time.

Some CX Time stories describe one named organisation doing one concrete thing at one moment
of its customer journey - exactly what a benchmark is. Enrichment drafts a benchmark for those
(in the repository's own shape: brand, industry, line, journey moment, CX pillar, themes,
three "why it works" points, and how it would travel to other Aldar lines). They are shown on
the review page; on /approve they are appended to the repository with the "From Aldar Times"
provenance chip, which links back to the edition and the source.

Like editions, they are append-only: data/benchmarks-from-times.json records every benchmark
added this way, and check() confirms each one is still in the hub.
"""
import base64, gzip, json, re
from collections import Counter
from datetime import datetime
from pathlib import Path

from .store import ROOT, HUB, MANIFEST_RE

REGISTRY = ROOT / "data" / "benchmarks-from-times.json"
MODULE_ID, LINKS_ID, INDEX_ID, IMAGES_ID = "4386a51f", "91ab40fa", "667c05bf", "d6dcdab9"
MARKER = "  // ---- From Aldar CX Time: appended by pipeline/cxtime on /approve; never edited ----\n"

# CX Time business line -> repository line key
LINE_KEY = {"Hospitality": "hp", "Retail": "rp", "Education": "edu", "Development": "dev",
            "Community": "est", "PM & Leasing": "est", "Corporate": "cp"}
LINE_LABEL = {"cp": "Corporate", "dev": "Development", "edu": "Education", "est": "Estates", "hp": "Hospitality", "rp": "Retail"}
LINE_COLOR = {"cp": "#1E7A5A", "dev": "#8A6A2F", "edu": "#5B7F8C", "est": "#742418", "hp": "#C08A5E", "rp": "#B86952"}
PLUS = ["Hospitality Plus", "Retail Plus", "Education Plus", "Corporate Plus", "Estates Plus", "Development Plus"]
ART = {"hp": "sand", "rp": "clay", "edu": "ocean", "cp": "sage", "est": "plum", "dev": "amber"}
MOMENTS = {"pre": "before: discovery, anticipation, choosing, booking, recruitment",
           "onb": "arrival: first contact, the threshold, check-in, handover, day one",
           "emp": "during: the stay, the visit, living there, the school year, employment",
           "exit": "leaving: check-out, departure, moving out",
           "after": "after: staying connected once they have gone"}
STAGES = {"cp": {"pre": "Pre-Hiring & Recruitment", "onb": "Onboarding & Arrival", "emp": "Employment", "exit": "Exit & Post-Employment", "after": "Exit & Post-Employment"},
          "hp": {"pre": "Pre-Arrival & Arrival", "onb": "Pre-Arrival & Arrival", "emp": "During Stay", "exit": "Check-Out & Post-Departure", "after": "Check-Out & Post-Departure"},
          "edu": {"pre": "Explore", "onb": "Enrol", "emp": "Educate", "exit": "Establish", "after": "Establish"},
          "rp": {"pre": "Pre-Shopping", "onb": "During Shopping", "emp": "During Shopping", "exit": "Post-Shopping", "after": "Post-Shopping"},
          "est": {"pre": "Pre-Orientation", "onb": "Handover", "emp": "Living", "exit": "Departure", "after": "Departure"},
          "dev": {"pre": "Lead to Sale", "onb": "Handover", "emp": "Walk In", "exit": "Aftersales", "after": "Aftersales"}}
PILLARS = {"detail": "Pursuing perfection in every detail (frictionless ease)",
           "care": "Anticipating every need with care (feeling truly seen)",
           "relationships": "Valuing relationships over transactions (never having to ask twice)",
           "magic": "Making important moments magical (wowed and delighted)",
           "belonging": "Inviting everyone to feel they belong (connection)"}
THEMES = ["Community", "Digital Experience", "Personalisation", "Magic Moments", "Relationships", "Families",
          "Convenience", "Loyalty", "Attention to Detail", "Innovation", "Belonging", "Anticipation", "Culture",
          "Welcome", "Employee Experience", "Recognition", "Arrival", "Tourism", "Sustainability", "Workplace",
          "Service Recovery"]
INDUSTRIES = ["Arts & culture", "Beach clubs", "Consumer brands", "Education", "Education technology", "Entertainment",
              "Financial services", "Food & beverage", "Golf & leisure", "Healthcare", "Hospitality", "Marinas & yachting",
              "Online marketplace", "Professional services", "Real estate", "Retail", "Shopping malls",
              "Sport & recreation", "Talent & recruitment", "Technology", "Transportation"]

SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["candidate", "whyNot", "brand", "industry", "line", "moment", "pillar", "themes", "title",
                 "short", "lead", "why", "transfer"],
    "properties": {
        "candidate": {"type": "boolean"},
        "whyNot": {"type": "string"},
        "brand": {"type": "string"},
        "industry": {"type": "string", "enum": INDUSTRIES},
        "line": {"type": "string", "enum": list(LINE_LABEL)},
        "moment": {"type": "string", "enum": list(MOMENTS)},
        "pillar": {"type": "string", "enum": list(PILLARS)},
        "themes": {"type": "array", "items": {"type": "string", "enum": THEMES}},
        "title": {"type": "string"},
        "short": {"type": "string"},
        "lead": {"type": "string"},
        "why": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["head", "body"],
                                           "properties": {"head": {"type": "string"}, "body": {"type": "string"}}}},
        "transfer": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["line", "how"],
                                                "properties": {"line": {"type": "string", "enum": PLUS}, "how": {"type": "string"}}}},
    },
}

TASK = """
Also decide whether this story yields a BENCHMARK for Aldar's Benchmark Repository, and fill
`benchmark`. A benchmark is ONE named organisation (never Aldar) doing ONE concrete,
observable practice at ONE moment of its customer's journey, described well enough in the
source to copy. Trend round-ups, surveys, opinion, vendor products and stories about many
brands at once are not benchmarks: set candidate=false with a short whyNot, and fill the other
fields minimally. When candidate=true:
- brand: the organisation as customers know it (add ' · <venue or city>' when the practice is
  site-specific, e.g. 'Rosewood · Hong Kong').
- industry: the closest of the listed industries.
- line: the Aldar line it most informs: hp Hospitality, rp Retail, edu Education, cp Corporate
  (employees), est Estates (residents, communities, property management), dev Development
  (buyers, sales, handover).
- moment: """ + "; ".join(f"{k} = {v}" for k, v in MOMENTS.items()) + """.
- pillar: the Aldar CX pillar it delivers: """ + "; ".join(f"{k} = {v}" for k, v in PILLARS.items()) + """.
- themes: 1-3 from the list.
- title: 3-7 words naming what the practice achieves, in the repository's voice
  (e.g. 'The Building That Sells the Job', 'School Starts Before Term Does').
- short: one factual sentence saying what happens, at most 25 words.
- lead: two sentences on how it works for the customer.
- why: exactly 3 points, each a short head (at most 8 words) and a one-sentence body.
- transfer: 1-3 ways it travels to OTHER Aldar lines ('Estates Plus', 'Retail Plus', ...), each
  one concrete sentence.
Everything must be supported by the source."""


# ---------------------------------------------------------------- hub assets
def _read(man, prefix):
    key = next(k for k in man if k.startswith(prefix))
    e = man[key]
    raw = base64.b64decode(e["data"])
    return key, (gzip.decompress(raw) if e.get("compressed") else raw).decode("utf-8")


def _write(man, key, text):
    e = man[key]
    raw = text.encode("utf-8")
    e["data"] = base64.b64encode(gzip.compress(raw, 9) if e.get("compressed") else raw).decode()


def existing_ids(hub=HUB):
    html = Path(hub).read_text(encoding="utf-8")
    man = json.loads(MANIFEST_RE.search(html).group(2))
    _, mod = _read(man, MODULE_ID)
    return set(re.findall(r"\{\s*\"?id\"?\s*:\s*['\"]([a-z0-9-]+)['\"],\s*\"?title\"?\s*:", mod))


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def make_id(bm, taken):
    base = slug(bm["brand"].split(" · ")[0])[:18].strip("-") + "-" + slug(bm["title"])[:28].strip("-")
    i, out = 2, base
    while out in taken:
        out, i = f"{base}-{i}", i + 1
    return out


def build(bm, item, edition, taken, month):
    """Repository record in the same field order as Group CX's own benchmarks."""
    rid = make_id(bm, taken)
    taken.add(rid)
    return {
        "id": rid, "title": bm["title"], "brand": bm["brand"], "industry": bm["industry"], "moment": bm["moment"],
        "line": bm["line"], "pillar": bm["pillar"], "themes": bm["themes"][:3], "art": ART[bm["line"]],
        "size": "standard", "added": month, "short": bm["short"], "lead": bm["lead"], "why": bm["why"][:3],
        "informed": [], "transfer": [t for t in bm["transfer"] if LINE_LABEL[bm["line"]] + " Plus" != t["line"]][:3],
        "source": f"Aldar CX Time, Edition {edition['n']} · {item['source']}, {item['published']}.",
        "prov": {"kind": "times", "edition": edition["n"], "date": edition["date"], "source": item["source"],
                 "url": item["sourceUrl"], "story": item["id"]},
    }


def append_to_hub(records, images, hub=HUB):
    """Append records to the repository DATA, its link index, headline index and photo shard."""
    if not records:
        return
    html = Path(hub).read_text(encoding="utf-8")
    m = MANIFEST_RE.search(html)
    man = json.loads(m.group(2))

    key, mod = _read(man, MODULE_ID)
    start = mod.index("const DATA = [")
    end = mod.index("\n];", start)
    block = "".join("  " + json.dumps(r, ensure_ascii=False) + ",\n" for r in records)
    if MARKER not in mod[start:end]:
        block = "\n" + MARKER + block
    mod = mod[:end + 1] + block + mod[end + 1:]
    _write(man, key, mod)

    key, js = _read(man, LINKS_ID)
    head, arr = js.split("window.BM_LINKS = ", 1)
    links = json.loads(arr.strip().rstrip(";"))
    links += [{"id": r["id"], "t": r["title"], "br": r["brand"], "ind": r["industry"], "ln": r["line"],
               "pil": r["pillar"], "th": r["themes"], "s": r["short"], "inf": []} for r in records]
    _write(man, key, head + "window.BM_LINKS = " + json.dumps(links, ensure_ascii=False) + ";\n")

    key, js = _read(man, INDEX_ID)
    idx = json.loads(js.split("=", 1)[1].strip().rstrip(";"))
    known_brands = {l["br"].split(" · ")[0] for l in links[:-len(records)]}
    known_ind = {l["ind"] for l in links[:-len(records)]}
    idx["count"] += len(records)
    idx["brands"] += len({r["brand"].split(" · ")[0] for r in records} - known_brands)
    idx["industries"] += len({r["industry"] for r in records} - known_ind)
    month = records[0]["added"]
    label = datetime.strptime(month, "%Y-%m").strftime("%B %Y")
    if idx.get("latestLabel") == label:
        idx["latestCount"] += len(records)
    else:
        idx["latestLabel"], idx["latestCount"] = label, len(records)
    lines = {l["key"]: l for l in idx["lines"]}
    for r in records:
        lines.setdefault(r["line"], {"key": r["line"], "label": LINE_LABEL[r["line"]], "color": LINE_COLOR[r["line"]], "n": 0})["n"] += 1
    idx["lines"] = sorted(lines.values(), key=lambda l: -l["n"])
    for p in idx.get("pillars", []):
        p["n"] += sum(r["pillar"] == p["key"] for r in records)
    tt = {t["label"]: t["n"] for t in idx.get("topThemes", [])}
    for r in records:
        for t in r["themes"]:
            if t in tt:
                tt[t] += 1
    idx["topThemes"] = [{"label": k, "n": v} for k, v in sorted(tt.items(), key=lambda x: -x[1])]
    idx["all"] = idx.get("all", []) + [{"id": r["id"], "t": r["title"], "b": r["brand"].split(" · ")[0],
                                        "l": LINE_LABEL[r["line"]], "c": LINE_COLOR[r["line"]],
                                        "s": STAGES[r["line"]][r["moment"]], "i": r["industry"]} for r in records]
    _write(man, key, "window.BM_INDEX = " + json.dumps(idx, ensure_ascii=False) + ";\n")

    key, js = _read(man, IMAGES_ID)
    imgs = json.loads(js.split("=", 1)[1].strip().rstrip(";"))
    imgs.update({r["id"]: images[r["id"]] for r in records if images.get(r["id"])})
    _write(man, key, "window.BM_IMAGES_D = " + json.dumps(imgs, ensure_ascii=False) + ";\n")

    html = html[:m.start(2)] + json.dumps(man, separators=(",", ":")) + html[m.end(2):]
    Path(hub).write_text(html, encoding="utf-8")


def load_registry():
    return json.loads(REGISTRY.read_text()) if REGISTRY.exists() else {"benchmarks": []}


def save_registry(reg):
    REGISTRY.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n")


def check(hub=HUB):
    """Every benchmark CX Time ever added must still be in the hub's repository."""
    reg = load_registry()
    have = existing_ids(hub)
    missing = [b["id"] for b in reg["benchmarks"] if b["id"] not in have]
    if missing:
        from .store import ArchiveError
        raise ArchiveError(f"benchmarks added from CX Time are missing from the hub: {missing}")
    return len(reg["benchmarks"])


def validate(bm):
    p = []
    if not bm["brand"].strip() or bm["brand"].lower().startswith("aldar"):
        p.append("no named organisation")
    if len(bm["why"]) != 3:
        p.append("why must have 3 points")
    if not bm["transfer"]:
        p.append("no transfer to another line")
    if not (1 <= len(bm["themes"]) <= 3):
        p.append("themes must be 1-3")
    if len(bm["short"].split()) > 32:
        p.append("short is too long")
    return p
