"""Apply a Hospitality Plus tracker update to HP_DATA inside index.html.

Each row maps a tracker line to a record id and the change it implies. Status codes in
HP_DATA: 'impl' = Deployed & Live, 'prog' = In Implementation, 'rev' = In Review,
'dep' = Backlog (2027). The tracker's own wording becomes the record's latest note and a
dated log entry; the earlier note is kept after it. "Awaiting update" rows are skipped.
Usage: python3 -I tools/update_hp_tracker.py
"""
import base64, gzip, json, re

PAGE = "index.html"
WHEN, STAMP, LABEL = "2 Nov 2026", "2026-11-02T00:00:00.000Z", "2 November 2026"
SOURCE = "Hospitality Plus Tracker 02.11.26"

# id, tracker status (verbatim), change
ROWS = [
    ("kids-only-check-in-counter",   "On track – 26 Oct",                                         dict(status="prog", release="oct2026")),
    ("kids-welcome-packs-backpacks", "On track – 3rd week of Oct",                                dict(status="prog", release="oct2026")),
    ("mission-card",                 "On track – 26 Oct",                                         dict(status="prog", release="oct2026")),
    ("cyan-beach-enhancement",       "On track – 29 Oct",                                         dict(status="prog", release="oct2026")),
    ("the-sundown-ceremony",         "In progress to Q4 2026. Team working on Sundown Ceremony",  dict(status="prog", release="q4-2026", add_scope=["YPH"])),
    ("story-of-their-stay",          "Deferred to 2027 – will explore a way to monetise it through paid services", dict(status="dep", release=None)),
    ("in-room-games",                "Ahead of schedule – 26 Oct",                                dict(status="prog", release="oct2026")),
    ("the-w-paws-arrival",           "Launched – merchandise enhancements pending",               dict(status="impl", live=["WHT"])),
    ("the-rotating-table",           "On track – November",                                       dict(status="prog", release="nov2026")),
    ("recovery-lounge-wellness-bar", "At risk – Dec or 2027; Ummi trial underway",                dict(status="prog", release="dec2026")),
    ("fitness-studio-programming",   "On track – late Oct / Nov",                                 dict(status="prog", release="nov2026")),
    ("marhaba-el-saa-welcome-box",   "Deferred to 2027 – operational constraints",                dict(status="dep", release=None)),
    ("kids-in-room-treasure-hunt",   "Partially launched – expanded activity under consideration for Nov", dict(status="impl", live=["RIX"])),
    ("hikayat-farewell-kit",         "Deferred to 2027 – cost constraints; revised timing TBC",   dict(status="dep", release=None)),
    ("golden-hour-beach-gathering",  "In development – Nov / Dec",                                dict(status="prog", release="dec2026")),
    ("the-ice-cream-lab",            "Deferred to 2027",                                          dict(status="dep", release=None)),
    ("themed-bus",                   "Not started – December delivery at risk",                   dict(status="prog", release="dec2026")),
]
AWAITING = ["mission-begins-at-check-in", "welcome-before-the-door", "the-open-kitchen", "the-concierge-who-already-knows"]
NAMES = {"YPH": "Yas Plaza", "WHT": "W Hotel", "RIX": "Rixos"}

def main():
    html = open(PAGE, encoding="utf-8").read()
    mm = re.search(r'(<script type="__bundler/manifest">\s*)(\{.*?\})(\s*</script>)', html, re.S)
    man = json.loads(mm.group(2))
    key = next(k for k, e in man.items() if "javascript" in e["mime"] and b"window.HP_DATA" in
               (gzip.decompress(base64.b64decode(e["data"])) if e["compressed"] else base64.b64decode(e["data"])))
    e = man[key]
    raw = base64.b64decode(e["data"]); js = (gzip.decompress(raw) if e["compressed"] else raw).decode("utf-8")
    start = js.index("{", js.index("window.HP_DATA"))
    data, end = json.JSONDecoder().raw_decode(js[start:])
    byid = {x["id"]: x for x in data["experiences"]}
    assert all(r[0] in byid for r in ROWS) and all(a in byid for a in AWAITING)

    for rid, said, ch in ROWS:
        x = byid[rid]
        line = said + " (" + SOURCE + ")."
        if any(l.get("when") == WHEN and SOURCE in l.get("text", "") for l in x.get("log") or []):
            continue  # already applied
        old = (x.get("note") or "").strip()
        same_road = (x.get("roadmapNote") or "").strip() == old
        x["note"] = line + ((" " + old) if old else "")
        if same_road or not x.get("roadmapNote"):
            x["roadmapNote"] = x["note"]
        x["status"] = ch["status"]
        if "release" in ch:
            x["release"] = ch["release"]
        cells = x.setdefault("cells", {})
        for code in ch.get("add_scope", []):
            cells.setdefault(code, "prog")
        for code in ch.get("live", []):
            cells[code] = "impl"
        if ch["status"] == "dep":
            pass  # scope kept as recorded; the lifecycle shows Backlog (2027)
        # keep deployedAssets in step with the cells
        da = {d["name"]: d for d in x.get("deployedAssets") or []}
        for code, v in cells.items():
            n = NAMES.get(code) or next((a["name"] for a in data["assetTable"] if a["code"] == code), code)
            da.setdefault(n, {"name": n, "live": False})["live"] = (v == "impl")
        x["deployedAssets"] = list(da.values())
        x.setdefault("log", []).append({"when": WHEN, "author": "Group CX", "text": "Status update from the " + SOURCE + ": " + said + "."})

    data.setdefault("relLabels", {})["q4-2026"] = "Q4 2026"
    data["dataStamp"] = STAMP
    data["programme"]["updated"] = LABEL
    js = js[:start] + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + js[start + end:]
    raw = js.encode("utf-8")
    e["data"] = base64.b64encode(gzip.compress(raw, 9) if e["compressed"] else raw).decode()
    html = html[:mm.start(2)] + json.dumps(man, separators=(",", ":")) + html[mm.end(2):]
    open(PAGE, "w", encoding="utf-8").write(html)
    print("updated", len(ROWS), "records; skipped (awaiting update):", ", ".join(AWAITING))

if __name__ == "__main__":
    main()
