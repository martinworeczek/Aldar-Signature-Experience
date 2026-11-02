"""Step 3 - Curate. Pure rules, no AI: the same records always give the same edition.

Order of priorities: relevance -> experiential strength -> transferability (lines) ->
source credibility -> freshness -> variety -> no duplication.
"""
import re
from collections import Counter
from datetime import datetime

FORMATS = ("read", "watch", "listen")
PREFIX = {"read": "s", "watch": "w", "listen": "l"}


def _words(t):
    return {w for w in re.findall(r"[a-z0-9]+", t.lower()) if len(w) > 3}


def similar(a, b):
    wa, wb = _words(a), _words(b)
    return len(wa & wb) / max(1, len(wa | wb))


def rank_key(r):
    return (r["relevance"], r["experiential"], len([l for l in r["lines"] if l != "All lines"]) or 2,
            r["_weight"], r["_publishedISO"])


def select(records, archive_titles, cfg, overrides=None):
    """records: enriched + validated (with hidden _fields). Returns (edition_items, bench, notes).
    overrides: {"drop": set(keys), "lead": key or None, "add": set(keys)} from the reviewer."""
    ed = cfg["edition"]
    ov = overrides or {}
    drop, force_add, force_lead = set(ov.get("drop", ())), set(ov.get("add", ())), ov.get("lead")
    notes, bench = [], []

    pool = []
    for r in records:
        if r["key"] in drop:
            continue
        dupe = next((t for t in archive_titles if similar(r["title"], t) >= 0.6), None)
        if dupe:
            notes.append(f"{r['key']} looks like a story already published ('{dupe}'), left out")
            continue
        good = (r["relevance"] >= ed["min_relevance"] and r["experiential"] >= ed["min_experiential"]
                and not r["_flags"])
        if good or r["key"] in force_add:
            pool.append(r)
        else:
            bench.append(r)

    # the same story from two sources: keep the stronger one
    pool.sort(key=rank_key, reverse=True)
    unique = []
    for r in pool:
        twin = next((u for u in unique if similar(r["title"], u["title"]) >= 0.5), None)
        if twin and r["key"] not in force_add:
            notes.append(f"{r['key']} covers the same story as {twin['key']}, kept the stronger one")
            bench.append(r)
        else:
            unique.append(r)

    chosen, per_source, per_line, n_ai = [], Counter(), Counter(), 0
    shelves = {f: [] for f in FORMATS}
    remaining = list(unique)
    while remaining:
        # variety: an item whose lines are already well covered gives way to one that adds a line
        def score(r):
            spread = sum(per_line[l] for l in r["lines"]) / max(1, len(r["lines"]))
            return rank_key(r)[:2] + (-spread,) + rank_key(r)[2:]
        remaining.sort(key=score, reverse=True)
        r = remaining.pop(0)
        f = r["format"]
        forced = r["key"] in force_add or r["key"] == force_lead
        reason = None
        if len(shelves[f]) >= ed["caps"][f]:
            reason = f"{f} shelf full"
        elif per_source[r["source"]] >= ed["max_per_source"] and not forced:
            reason = f"already {ed['max_per_source']} from {r['source']}"
        elif r["tag"] == "AI & Tech" and n_ai >= ed["max_ai_tech"] and not forced:
            reason = "AI quota reached"
        if reason:
            r["_benchReason"] = reason
            bench.append(r)
            continue
        shelves[f].append(r)
        chosen.append(r)
        per_source[r["source"]] += 1
        n_ai += r["tag"] == "AI & Tech"
        for l in r["lines"]:
            per_line[l] += 1

    # lead: reviewer's choice, else the strongest relevance-5 story (an image helps the hero)
    lead = None
    if force_lead:
        lead = next((r for r in chosen if r["key"] == force_lead), None)
        if not lead:
            notes.append(f"lead {force_lead} is not in the edition; ignored")
    if not lead and chosen:
        cands = sorted(chosen, key=lambda r: (r["relevance"], r["experiential"], bool(r.get("_image")), r["_publishedISO"]), reverse=True)
        lead = cands[0]
        if lead["relevance"] < ed["lead_min_relevance"]:
            notes.append(f"no story reached relevance {ed['lead_min_relevance']}; the lead is the best available")
    for f in FORMATS:
        shelves[f].sort(key=lambda r: (r is lead, r["relevance"], r["experiential"], r["_publishedISO"]), reverse=True)
    if len(chosen) < ed["min_items"]:
        notes.append(f"HOLD: only {len(chosen)} stories meet the bar (minimum {ed['min_items']})")
    return shelves, lead, bench, notes


def related(items):
    """3 per item, same edition only: shared lines > shared themes > shared tag, with a nudge
    towards other formats so the reader moves between Read, Watch and Listen."""
    out = {}
    for a in items:
        def s(b):
            return (3 * len(set(a["lines"]) & set(b["lines"])) + 2 * len(set(a["themes"]) & set(b["themes"]))
                    + (a["tag"] == b["tag"]) + (1.5 if a["format"] != b["format"] else 0) + b["relevance"] / 10)
        others = sorted((b for b in items if b is not a), key=s, reverse=True)
        out[a["id"]] = [b["id"] for b in others[:3]]
    return out
