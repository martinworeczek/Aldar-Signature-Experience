"""Offline stand-in for Claude, used by the tests (CXTIME_MOCK_LLM=1). Deterministic answers
shaped like the real schemas, so the whole pipeline can run without network or API key."""
import hashlib, json, re


def _h(s, n):
    return int(hashlib.sha1(s.encode()).hexdigest(), 16) % n


def answer(system, user, schema):
    props = schema["properties"]
    if "issues" in props:
        return {"issues": []}
    if "picks" in props:
        ids = re.findall(r'"id": "(e\d+-[swl]\d+)", "role": "FEATURE', user)
        return {"subject": "New in CX Time: mock", "preheader": "Mock preheader", "headline": "Mock headline.",
                "intro": "This week's edition is about a mock idea. Three stories lead it, and each comes with what it could mean for Aldar.",
                "picks": [{"id": i, "who": "Mock Brand", "title": "Mock title", "what": "Mock what.", "forAldar": "Mock for Aldar."} for i in ids]}
    if "items" in props and "keep" not in props:
        keys = re.findall(r'"key": "([0-9a-f]{8})"', user)
        return {"items": [{"key": k, "experiential": 3 + _h(k, 3), "reason": "mock screen"} for k in keys]}
    title = re.search(r'"title": "(.*?)"', user).group(1)
    fmt = re.search(r'"format": "(\w+)"', user).group(1)
    k = _h(title, 1000)
    lines = [["Hospitality"], ["Retail", "Community"], ["Education"], ["Development", "Community"], ["Corporate"]][k % 5]
    keep = "out of scope" not in title.lower()
    return {
        "keep": keep, "dropReason": "" if keep else "not experiential",
        "experiential": 4 + (k % 2), "relevance": 4 + (k % 3 == 0),
        "tag": ["Hospitality", "Retail", "Education", "Development", "Workplace"][k % 5],
        "lines": lines, "insight": "Case study", "themes": ["arrival", "ritual"],
        "title": title, "dek": "A mock standfirst for testing the pipeline end to end.",
        "summary": ["First mock sentence.", "Second mock sentence.", "Third mock sentence."],
        "why": f"Mock reason naming {lines[0]} and the arrival moment.",
        "excerpt": "A paraphrased pull-quote.",
        "opps": [{"line": l, "title": f"{l} Ritual", "text": f"A concrete {l.lower()} moment to build."} for l in lines],
        "keyInsights": ["Mock insight one.", "Mock insight two."],
        "speakers": ["Host Name"] if fmt != "read" else [],
        "benchmark": {
            "candidate": k % 2 == 0, "whyNot": "" if k % 2 == 0 else "a trend round-up, not one practice",
            "brand": "Mock Brand · Lisbon", "industry": "Hospitality",
            "line": ["hp", "rp", "edu", "est", "cp"][k % 5], "moment": "onb", "pillar": "care",
            "themes": ["Arrival", "Welcome"], "title": "The Welcome Before the Desk",
            "short": "Guests are met by a named host before they reach the desk.",
            "lead": "Arrival starts at the kerb. The host already knows the guest's requests.",
            "why": [{"head": "The queue disappears", "body": "No one waits."},
                    {"head": "Recognition is immediate", "body": "Names are used from the first second."},
                    {"head": "Requests arrive first", "body": "The room is ready."}],
            "transfer": [{"line": "Estates Plus", "how": "Move-in day met by a named community host."}],
        },
    }
