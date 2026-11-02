"""The weekly run: propose -> (review commands) -> publish.

State for one run lives in data/cxtime-runs/<date>/state.json: what every source returned, every
screening and gate decision with its reason, the enriched records (no source text), the
reviewer's overrides and the proposed edition. The review page (review.md) is rendered from it.
"""
import json, os, shutil, subprocess, sys, tempfile, tomllib
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from . import store, curate
from .store import ROOT, canon_url

CONFIG = ROOT / "pipeline" / "config.toml"
RUNS = ROOT / "data" / "cxtime-runs"
SEEN = ROOT / "data" / "cxtime-seen.json"
XLSX = ROOT / "data" / "aldar-times.xlsx"


def cfg():
    return tomllib.loads(CONFIG.read_text())


def run_dir(date):
    return RUNS / date


def latest_run():
    runs = sorted(p for p in RUNS.glob("*/state.json")) if RUNS.exists() else []
    if not runs:
        raise SystemExit("no run found in data/cxtime-runs/")
    return runs[-1].parent


def load_state(d):
    return json.loads((d / "state.json").read_text())


def save_state(d, st):
    d.mkdir(parents=True, exist_ok=True)
    (d / "state.json").write_text(json.dumps(st, ensure_ascii=False, indent=1) + "\n")


def load_seen():
    return json.loads(SEEN.read_text()) if SEEN.exists() else {}


def say(*a):
    print(*a, flush=True)


# ---------------------------------------------------------------- presentation fields
def display_published(fmt, iso, episode=""):
    d = datetime.fromisoformat(iso)
    if fmt == "read":
        return d.strftime("%d %b %Y")
    if fmt == "watch":
        return d.strftime("%b %Y")
    return (f"EP {episode} · " if episode else "EP - ") + d.strftime("%d %b %Y")


def display_meta(fmt, raw):
    if fmt == "read":
        words = int(raw or 0)
        return f"{max(1, round(words / 220))} min read" if words else ""
    if fmt == "watch":
        return f"{max(1, round(int(raw) / 60))} min" if (raw or "").isdigit() else ""
    from .harvest import duration_text
    return duration_text(raw)


def to_record(c, rec, flags, conf):
    """Candidate + enrichment -> the record shape the module reads, plus hidden _fields."""
    t = conf["tags"][rec["tag"]]
    opps = rec["opps"]
    lines = rec["lines"]
    return {
        "key": c["key"], "format": c["formatHint"], "tag": rec["tag"], "inkTag": t["ink"], "chipBg": t["chip"],
        "source": c["source"], "sourceShort": c["sourceShort"], "sourceUrl": c["sourceUrl"],
        "published": display_published(c["formatHint"], c["publishedRaw"], c.get("episode", "")),
        "meta": display_meta(c["formatHint"], c.get("durationRaw", "")),
        "thumb": f"linear-gradient(135deg,{t['a']},{t['b']})",
        "title": rec["title"], "dek": rec["dek"], "summary": rec["summary"], "why": rec["why"],
        "excerpt": rec["excerpt"], "oppTitle": opps[0]["title"], "oppText": opps[0]["text"], "opps": opps,
        "lines": lines, "insight": rec["insight"], "relevance": rec["relevance"], "themes": rec["themes"],
        "speakers": rec["speakers"] if c["formatHint"] != "read" else [],
        "transcriptUrl": c.get("transcriptUrl"), "keyInsights": rec["keyInsights"],
        # hidden, run-only
        "experiential": rec["experiential"], "_flags": flags, "_weight": c["_src"]["weight"],
        "_publishedISO": c["publishedRaw"], "_image": c.get("_image"), "_imageCredit": c.get("imageCredit"),
        "_imageNote": c.get("_imageNote"), "_imageNew": c.get("_imageNew", False),
        "_bench": rec["benchmark"] if rec["benchmark"]["candidate"] else None,
        "_benchWhyNot": "" if rec["benchmark"]["candidate"] else rec["benchmark"]["whyNot"],
    }


PUBLIC_ORDER = ["id", "format", "lead", "tag", "inkTag", "chipBg", "source", "sourceShort", "sourceUrl", "published",
                "meta", "thumb", "title", "dek", "summary", "why", "excerpt", "oppTitle", "oppText", "opps", "lines",
                "insight", "relevance", "themes", "speakers", "transcriptUrl", "keyInsights", "related",
                "imageKey", "imageCredit"]


def build_edition(st, conf, archive):
    """Curate the run's records into the proposed edition (ids, lead, related assigned)."""
    titles = store.seen_titles(archive)
    shelves, lead, bench, notes = curate.select(st["records"], titles, conf, st["overrides"])
    n = max(e["n"] for e in archive["editions"]) + 1
    items = []
    for f in curate.FORMATS:
        for i, r in enumerate(shelves[f], 1):
            it = {k: v for k, v in r.items() if not k.startswith("_") and k not in ("key", "experiential")}
            it["id"] = f"e{n}-{curate.PREFIX[f]}{i}"
            it["lead"] = r is lead
            if r.get("_image"):
                it["imageKey"] = it["id"]
                it["imageCredit"] = r["_imageCredit"]
            it["_key"] = r["key"]
            items.append(it)
    rel = curate.related(items)
    for it in items:
        it["related"] = rel[it["id"]]
    d = datetime.fromisoformat(st["date"])
    edition = {"n": n, "date": f"{d.day} {d:%B %Y}", "dateShort": f"{d.day} {d:%b %Y}",
               "items": [{k: it[k] for k in PUBLIC_ORDER if k in it} for it in items]}
    keymap = {it["id"]: it["_key"] for it in items}
    by_key = {r["key"]: r for r in st["records"]}
    nob = set(st["overrides"].setdefault("nobench", []))
    bench_ids = [it["id"] for it in items if by_key[it["_key"]].get("_bench") and it["_key"] not in nob]
    st["proposal"] = {"edition": edition, "keys": keymap, "notes": notes,
                      "bench": [b["key"] for b in bench],
                      "benchReasons": {b["key"]: b.get("_benchReason", "") for b in bench},
                      "hold": any(n.startswith("HOLD") for n in notes),
                      "benchmarks": bench_ids}
    return st


# ---------------------------------------------------------------- propose
def propose(date=None, only_sources=None):
    from . import harvest, enrich, images
    from .llm import LLMError

    conf = cfg()
    archive = store.load()
    store.verify_locked(archive)
    run_date = datetime.fromisoformat(date).replace(tzinfo=timezone.utc) if date else datetime.now(timezone.utc)
    date = run_date.date().isoformat()
    d = run_dir(date)
    seen = load_seen()
    seen_set = set(seen) | store.seen_urls(archive)
    f = harvest.Fetcher(conf["fetch"])
    ledger, statuses, cands = [], [], []

    say(f"== Harvest ({date}, window {conf['edition']['window_days']} days)")
    for src in conf["sources"]:
        if only_sources and src["name"] not in only_sources:
            continue
        got, status = harvest.collect_metadata(src, f, run_date, conf["edition"], seen_set, ledger)
        statuses.append(status)
        say(f"  {src['name']:<34} {src['format']:<6} " + (f"{status['new']} new" if status["ok"] else "FAILED " + status.get("error", "")))
        for c in got:
            if canon_url(c["sourceUrl"]) not in {canon_url(x["sourceUrl"]) for x in cands}:
                cands.append(c)

    say(f"== Screen {len(cands)} candidates on metadata")
    scores = enrich.screen(cands, conf) if cands else {}
    for c in cands:
        s, why = scores.get(c["key"], (1, "not scored"))
        c["_screen"], c["_screenReason"] = s, why
    shortlist = []
    for fmt in curate.FORMATS:
        pool = sorted((c for c in cands if c["formatHint"] == fmt and c["_screen"] >= 3),
                      key=lambda c: (c["_screen"], c["_src"]["weight"], c["publishedRaw"]), reverse=True)
        keep = pool[: conf["edition"]["shortlist"][fmt]]
        shortlist += keep
    short_keys = {c["key"] for c in shortlist}
    for c in cands:
        if c["key"] not in short_keys:
            ledger.append({"key": c["key"], "url": c["sourceUrl"], "title": c["titleRaw"], "source": c["source"],
                           "stage": "screen", "decision": "drop", "score": c["_screen"],
                           "reason": c["_screenReason"] if c["_screen"] < 3 else "below the shortlist cut"})

    say(f"== Deep read + enrich {len(shortlist)} shortlisted")
    records = []
    for c in shortlist:
        entry = {"key": c["key"], "url": c["sourceUrl"], "title": c["titleRaw"], "source": c["source"], "score": c["_screen"]}
        try:
            harvest.deep_fetch(c, f, conf["fetch"])
        except Exception as e:
            ledger.append({**entry, "stage": "fetch", "decision": "drop", "reason": str(e)[:200]})
            say(f"  - {c['titleRaw'][:70]}  (fetch: {e})")
            continue
        try:
            rec, flags, why = enrich.enrich_and_check(c, conf)
        except LLMError as e:
            ledger.append({**entry, "stage": "enrich", "decision": "error", "reason": str(e)})
            say(f"  ! {c['titleRaw'][:70]}  ({e})")
            continue
        finally:
            c.pop("sourceText", None)  # source text never leaves memory
        if not rec:
            ledger.append({**entry, "stage": "gate", "decision": "drop", "reason": why})
            say(f"  - {c['titleRaw'][:70]}  ({why})")
            continue
        attach_image(c, f, conf)
        r = to_record(c, rec, flags, conf)
        records.append(r)
        ledger.append({**entry, "stage": "gate", "decision": "keep", "reason": f"relevance {r['relevance']}, experiential {r['experiential']}"
                       + (f"; {len(flags)} fact-check flag(s)" if flags else "")})
        say(f"  + {r['title'][:70]}  (rel {r['relevance']}, exp {r['experiential']}{', FLAGGED' if flags else ''})")

    st = {"date": date, "created": datetime.now(timezone.utc).isoformat(timespec="seconds"), "sources": statuses,
          "ledger": ledger, "records": records, "candidates": {c["key"]: _cand_meta(c) for c in cands},
          "overrides": {"drop": [], "add": [], "lead": None, "nobench": []}, "history": []}
    build_edition(st, conf, archive)
    for c in cands:  # remember everything screened, so it is never re-offered
        seen.setdefault(canon_url(c["sourceUrl"]), {"first": date, "title": c["titleRaw"][:120]})
    SEEN.write_text(json.dumps(seen, ensure_ascii=False, indent=0, sort_keys=True) + "\n")
    save_state(d, st)
    write_review(d, st, conf)
    say(f"== Proposal written to {d.relative_to(ROOT)}/review.md")
    return d


def _cand_meta(c):
    return {k: v for k, v in c.items() if not k.startswith("_") and k not in ("sourceText", "excerpt")}


def attach_image(c, f, conf):
    from . import images
    urls = [c.get("rawImageUrl")]
    if c.get("videoId"):
        urls.append(f"https://i.ytimg.com/vi/{c['videoId']}/sddefault.jpg")
    for u in [u for u in urls if u]:
        try:
            c["_image"], c["_imageNew"] = images.fetch_and_store(u, f, conf["images"])
            return
        except Exception as e:
            c["_imageNote"] = str(e)[:160]
    c["_image"] = None


# ---------------------------------------------------------------- review commands
HELP = """Reply on this pull request with one command per line:

| Command | What it does |
|---|---|
| `/approve` | Publish this edition: append it to the archive, update both sites, merge. |
| `/approve anyway` | Publish even though the edition is marked HOLD (below the minimum). |
| `/drop e3-s4` | Take a story out (it moves to the bench). |
| `/add k:ab12cd34` | Bring a bench story into the edition (key shown in the bench table). |
| `/lead e3-w1` | Make this story the Signal of the Week. |
| `/rerun e3-l2 focus on the arrival ritual` | Rewrite one story; the note is passed to the editor. |
| `/nobench e3-s2` | Publish the story but do not add its benchmark to the Benchmark Repository. |
| `/bench e3-s2` | Put a benchmark you removed back. |
"""


def resolve(st, ref):
    ref = ref.strip().removeprefix("k:")
    keys = st["proposal"]["keys"]
    if ref in keys:
        return keys[ref]
    if any(r["key"] == ref for r in st["records"]):
        return ref
    raise ValueError(f"unknown story '{ref}'")


def revise(text, date=None):
    """Apply reviewer commands. Returns 'approve', 'approve-anyway' or None."""
    from . import harvest, enrich
    conf = cfg()
    d = run_dir(date) if date else latest_run()
    st = load_state(d)
    archive = store.load()
    ov = st["overrides"]
    approve, applied, errors = None, [], []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("/"):
            continue
        cmd, _, rest = line.partition(" ")
        args = rest.strip()
        try:
            if cmd == "/approve":
                approve = "approve-anyway" if args.lower().startswith("anyway") else "approve"
            elif cmd == "/drop":
                k = resolve(st, args.split()[0]); ov["drop"] = sorted(set(ov["drop"]) | {k})
                ov["add"] = [x for x in ov["add"] if x != k]
                if ov["lead"] == k:
                    ov["lead"] = None
            elif cmd == "/add":
                k = resolve(st, args.split()[0]); ov["add"] = sorted(set(ov["add"]) | {k})
                ov["drop"] = [x for x in ov["drop"] if x != k]
            elif cmd == "/lead":
                k = resolve(st, args.split()[0]); ov["lead"] = k
                ov["drop"] = [x for x in ov["drop"] if x != k]
            elif cmd == "/nobench":
                k = resolve(st, args.split()[0])
                ov["nobench"] = sorted(set(ov.get("nobench", [])) | {k})
            elif cmd == "/bench":
                k = resolve(st, args.split()[0])
                if not next(r for r in st["records"] if r["key"] == k).get("_bench"):
                    raise ValueError("this story has no benchmark draft")
                ov["nobench"] = [x for x in ov.get("nobench", []) if x != k]
            elif cmd == "/rerun":
                ref, _, note = args.partition(" ")
                rerun(st, resolve(st, ref), note.strip(), conf)
            else:
                raise ValueError(f"unknown command {cmd}")
            applied.append(line)
        except Exception as e:
            errors.append(f"`{line}`: {e}")
    st["history"].append({"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "applied": applied, "errors": errors})
    build_edition(st, conf, archive)
    save_state(d, st)
    write_review(d, st, conf)
    say("applied:", applied or "nothing", "| errors:", errors or "none")
    return approve, errors


def rerun(st, key, note, conf):
    """Re-read one story from its source and rewrite it, with the reviewer's note."""
    from . import harvest, enrich
    c = dict(st["candidates"][key])
    src = next(s for s in conf["sources"] if s["name"] == c["source"] and s["format"] == c["formatHint"])
    c["_src"] = src
    f = harvest.Fetcher(conf["fetch"])
    if c["formatHint"] != "read":  # episode notes / descriptions come from the feed
        got, _ = harvest.collect_metadata(src, f, datetime.fromisoformat(st["date"]).replace(tzinfo=timezone.utc),
                                          {**conf["edition"], "window_days": 60, "fallback_max_age_days": 60}, set(), [])
        match = next((g for g in got if g["key"] == key), None)
        if not match:
            raise ValueError("the item is no longer in its source's feed")
        c["_body"] = match["_body"]
    harvest.deep_fetch(c, f, conf["fetch"])
    fb = [{"field": "all", "claim": "", "problem": "Reviewer note: " + note}] if note else None
    rec = enrich.enrich(c, conf, feedback=fb)
    issues = enrich.verify(c, rec, conf)
    c.pop("sourceText", None)
    problems = enrich.validate(rec)
    if problems:
        raise ValueError("rewrite was invalid: " + "; ".join(problems))
    from . import benchmarks
    if rec["benchmark"]["candidate"] and (benchmarks.validate(rec["benchmark"]) or any(i["field"].startswith("benchmark") for i in issues)):
        rec["benchmark"]["candidate"], rec["benchmark"]["whyNot"] = False, "benchmark draft failed checks"
    issues = [i for i in issues if not i["field"].startswith("benchmark")]
    old = next(r for r in st["records"] if r["key"] == key)
    c["_image"], c["imageCredit"] = old.get("_image"), old.get("_imageCredit")
    c["_imageNote"], c["_imageNew"] = old.get("_imageNote"), old.get("_imageNew", False)
    new = to_record(c, rec, [f"fact-check: {i['field']}: {i['claim']} ({i['problem']})" for i in issues], conf)
    st["records"] = [new if r["key"] == key else r for r in st["records"]]
    if key not in st["overrides"]["add"]:
        st["overrides"]["add"].append(key)  # a story the reviewer asked to rewrite stays in


# ---------------------------------------------------------------- review page
def write_review(d, st, conf):
    p = st["proposal"]
    ed = p["edition"]
    base = os.environ.get("CXTIME_IMG_BASE", "")
    recs = {r["key"]: r for r in st["records"]}
    L = []
    hold = " · HOLD" if p["hold"] else ""
    L.append(f"# Aldar CX Time · Edition {ed['n']} · {ed['date']}{hold}\n")
    counts = Counter(i["format"] for i in ed["items"])
    L.append(f"**{len(ed['items'])} stories** · {counts['read']} read · {counts['watch']} watch · {counts['listen']} listen. "
             f"Caps {conf['edition']['caps']['read']}/{conf['edition']['caps']['watch']}/{conf['edition']['caps']['listen']}; "
             f"bar: relevance ≥ {conf['edition']['min_relevance']}, experiential ≥ {conf['edition']['min_experiential']}.\n")
    if os.environ.get("CXTIME_PREVIEW_URL"):
        L.append(f"**Preview the page:** {os.environ['CXTIME_PREVIEW_URL']}\n")
    for n in p["notes"]:
        L.append(f"> {'⚠️ ' if n.startswith('HOLD') else ''}{n}")
    if p["notes"]:
        L.append("")

    lines_cov = Counter(l for i in ed["items"] for l in i["lines"])
    L.append("**Business lines covered:** " + (", ".join(f"{l} {n}" for l, n in lines_cov.most_common()) or "none"))
    silent = [l for l in ("Hospitality", "Retail", "Education", "Development", "Community", "PM & Leasing", "Corporate")
              if l not in lines_cov and "All lines" not in lines_cov]
    if silent:
        L.append(f"  \n**No story this week for:** {', '.join(silent)}")
    L.append("")

    for shelf, title in (("read", "01 · Articles"), ("watch", "02 · Videos"), ("listen", "03 · Podcasts")):
        items = [i for i in ed["items"] if i["format"] == shelf]
        L.append(f"## {title} ({len(items)})\n")
        if not items:
            L.append("_Nothing met the bar this week._\n")
        for it in items:
            r = recs[p["keys"][it["id"]]]
            star = "★ SIGNAL OF THE WEEK · " if it["lead"] else ""
            L.append(f"### {star}`{it['id']}` {it['title']}")
            L.append(f"{it['source']} · {it['published']}{' · ' + it['meta'] if it['meta'] else ''} · "
                     f"[source]({it['sourceUrl']}) · tag **{it['tag']}**{' · ' + it['insight'] if it['insight'] else ''} · "
                     f"relevance {it['relevance']} · experiential {r['experiential']} · key `{r['key']}`  ")
            L.append(f"**Lines:** {', '.join(it['lines'])}" + (f" · **Speakers:** {', '.join(it['speakers'])}" if it["speakers"] else ""))
            if it.get("imageKey") and base:
                L.append(f"\n<img src=\"{base}{r['_image']}?raw=true\" width=\"360\" alt=\"\"> <sub>Image · {it['imageCredit']}</sub>\n")
            elif not it.get("imageKey"):
                L.append(f"\n_No photo (gradient shown): {r.get('_imageNote') or 'none offered'}_\n")
            L.append(f"*{it['dek']}*\n")
            for s in it["summary"]:
                L.append(f"- {s}")
            L.append(f"\n**Why it matters to Aldar.** {it['why']}\n")
            L.append("**Signature Experiences to explore:** " + " · ".join(f"*{o['line']}:* **{o['title']}**: {o['text']}" for o in it["opps"]))
            L.append(f"\n**Pull-quote:** {it['excerpt']}  \n**Related:** {', '.join(it['related'])}")
            for fl in r["_flags"]:
                L.append(f"\n> ⚠️ {fl}")
            L.append("")

    bms = [(i, recs[p["keys"][i["id"]]]["_bench"]) for i in ed["items"] if i["id"] in p.get("benchmarks", [])]
    L.append(f"## For the Benchmark Repository ({len(bms)})\n")
    if not bms:
        L.append("_No story this week describes a single organisation's practice clearly enough to benchmark._\n")
    else:
        L.append("On `/approve` these join the Benchmark Repository on the Signature Experience hub, marked "
                 "**✦ From Aldar Times** with a link back to the edition and source. `/nobench <id>` keeps one out.\n")
    from .benchmarks import STAGES, LINE_LABEL, PILLARS
    for it, bm in bms:
        L.append(f"#### from `{it['id']}` · **{bm['title']}** · {bm['brand']}")
        L.append(f"{bm['industry']} · {LINE_LABEL[bm['line']]} Plus · {STAGES[bm['line']][bm['moment']]} · "
                 f"pillar: {PILLARS[bm['pillar']].split(' (')[0]} · {', '.join(bm['themes'])}  ")
        L.append(f"*{bm['short']}* {bm['lead']}\n")
        for w in bm["why"]:
            L.append(f"- **{w['head']}** {w['body']}")
        L.append("\n**Travels to:** " + " · ".join(f"*{t['line']}:* {t['how']}" for t in bm["transfer"]) + "\n")
    skipped = [(i["id"], recs[p["keys"][i["id"]]]) for i in ed["items"] if i["id"] not in p.get("benchmarks", [])]
    if skipped:
        L.append("<sub>Not benchmarked: " + "; ".join(
            f"`{i}` {('removed by reviewer' if r.get('_bench') else (r.get('_benchWhyNot') or 'not a single-organisation practice'))}"
            for i, r in skipped) + "</sub>\n")

    bench = [recs[k] for k in p["bench"] if k in recs]
    if bench:
        L.append("## Bench: enriched but not selected\n")
        L.append("| key | format | title | source | rel | exp | why not in |")
        L.append("|---|---|---|---|---|---|---|")
        for r in bench:
            why = p["benchReasons"].get(r["key"]) or ("fact-check flag" if r["_flags"] else "below the bar" if r["relevance"] < conf["edition"]["min_relevance"] or r["experiential"] < conf["edition"]["min_experiential"] else "ranked lower")
            L.append(f"| `k:{r['key']}` | {r['format']} | [{r['title'][:70]}]({r['sourceUrl']}) | {r['source']} | {r['relevance']} | {r['experiential']} | {why} |")
        L.append("")

    gate = [x for x in st["ledger"] if x["stage"] in ("gate", "fetch", "enrich") and x["decision"] != "keep"]
    if gate:
        L.append("<details><summary><b>Dropped after the full read (" + str(len(gate)) + ")</b></summary>\n")
        L.append("| title | source | stage | reason |\n|---|---|---|---|")
        for x in gate:
            L.append(f"| [{x['title'][:70]}]({x['url']}) | {x['source']} | {x['stage']} | {x['reason'][:140]} |")
        L.append("\n</details>\n")
    scr = [x for x in st["ledger"] if x["stage"] == "screen"]
    if scr:
        L.append(f"<details><summary><b>Screened out on metadata ({len(scr)})</b></summary>\n")
        L.append("| title | source | score | reason |\n|---|---|---|---|")
        for x in sorted(scr, key=lambda x: -x.get("score", 0)):
            L.append(f"| {x['title'][:80]} | {x['source']} | {x.get('score', '')} | {x['reason'][:100]} |")
        L.append("\n</details>\n")
    L.append("<details><summary><b>Sources this week</b></summary>\n")
    L.append("| source | format | status | in window | new |\n|---|---|---|---|---|")
    for s in st["sources"]:
        stt = "ok" + (" (fallback: newest items)" if s.get("fallback") else "") if s["ok"] else "⚠️ " + s.get("error", "failed")[:90]
        L.append(f"| {s['source']} | {s['format']} | {stt} | {s.get('inWindow', '')} | {s.get('new', '')} |")
    L.append("\n</details>\n")
    if st["history"]:
        last = st["history"][-1]
        L.append(f"_Last revision {last['at']}: applied {len(last['applied'])} command(s)._" +
                 ("".join(f"\n> ⚠️ {e}" for e in last["errors"])))
    L.append("\n---\n" + HELP)
    full = "\n".join(L) + "\n"
    (d / "review.md").write_text(full)
    # GitHub caps a PR description at 65,536 characters: drop the long tables first if needed
    body = full
    for marker in ("<details><summary><b>Screened out", "<details><summary><b>Dropped after", "## Bench"):
        if len(body) <= 60000:
            break
        i = body.find(marker)
        if i >= 0:
            if marker == "## Bench":
                j = min(x for x in (body.find("<details>", i), body.find("\n---\n", i), len(body)) if x >= 0)
            else:
                j = body.find("</details>", i) + len("</details>")
            body = body[:i] + "_(table trimmed for length; see review.md in this branch)_\n" + body[j:]
    (d / "pr-body.md").write_text(body[:65000])


# ---------------------------------------------------------------- publish
def _apply(archive, st):
    ed = json.loads(json.dumps(st["proposal"]["edition"]))
    recs = {r["key"]: r for r in st["records"]}
    imgs = dict(archive.get("images", {}))
    for it in ed["items"]:
        if it.get("imageKey"):
            imgs[it["id"]] = recs[st["proposal"]["keys"][it["id"]]]["_image"]
    return {"editions": [ed] + archive["editions"], "stamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "images": imgs}


def preflight(st, archive, conf, force=False):
    p = st["proposal"]
    ed = p["edition"]
    errs = []
    if not ed["items"]:
        errs.append("the edition is empty")
    if p["hold"] and not force:
        errs.append("the edition is on HOLD (below the minimum); reply `/approve anyway` to publish it regardless")
    if ed["n"] != max(e["n"] for e in archive["editions"]) + 1:
        errs.append(f"Edition {ed['n']} is not the next number")
    if sum(i["lead"] for i in ed["items"]) != 1:
        errs.append("there must be exactly one lead")
    caps = conf["edition"]["caps"]
    for f in curate.FORMATS:
        if sum(i["format"] == f for i in ed["items"]) > caps[f]:
            errs.append(f"too many {f} items")
    ids = {i["id"] for i in ed["items"]}
    for i in ed["items"]:
        if any(r not in ids for r in i["related"]):
            errs.append(f"{i['id']} has related stories outside the edition")
        if len(i["summary"]) != 3:
            errs.append(f"{i['id']} summary is not 3 sentences")
        if i.get("imageKey"):
            ref = st["records"][[r["key"] for r in st["records"]].index(p["keys"][i["id"]])]["_image"]
            if not (ROOT / ref.lstrip("/")).exists():
                errs.append(f"{i['id']} photo file {ref} is missing")
    old = store.seen_urls(archive)
    for i in ed["items"]:
        if canon_url(i["sourceUrl"]) in old:
            errs.append(f"{i['id']} was already published in an earlier edition")
    return errs


def check_urls(items, conf):
    """Every sourceUrl must still answer. 404/410 blocks; other refusals (403 to bots) are reported."""
    import requests
    s = requests.Session()
    s.headers["User-Agent"] = conf["fetch"]["user_agent"]
    hard, soft = [], []
    for i in items:
        try:
            r = s.get(i["sourceUrl"], timeout=conf["fetch"]["timeout"], allow_redirects=True, stream=True)
            r.close()
            if r.status_code in (404, 410):
                hard.append(f"{i['id']}: {r.status_code} {i['sourceUrl']}")
            elif r.status_code >= 400:
                soft.append(f"{i['id']}: {r.status_code} (site refuses bots; check by hand) {i['sourceUrl']}")
        except Exception as e:
            soft.append(f"{i['id']}: could not connect ({type(e).__name__}) {i['sourceUrl']}")
    return hard, soft


def publish(date=None, force=False, skip_url_check=False):
    conf = cfg()
    d = run_dir(date) if date else latest_run()
    st = load_state(d)
    archive = store.load()
    store.verify_locked(archive)
    errs = preflight(st, archive, conf, force)
    if errs:
        raise SystemExit("Not published:\n- " + "\n- ".join(errs))
    soft = []
    if not skip_url_check:
        hard, soft = check_urls(st["proposal"]["edition"]["items"], conf)
        if hard:
            raise SystemExit("Not published, dead source links:\n- " + "\n- ".join(hard))

    new = _apply(archive, st)
    store.save(new)
    store.verify_locked(new)        # every earlier edition still byte-identical
    store.save_lock(new)            # and now the new one is locked too
    store.write_hub(new)
    store.check_hub_matches(new)
    write_xlsx(new)
    n_bm = publish_benchmarks(st, new)
    subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "build_cx_time.py")], cwd=ROOT, check=True)

    # tidy: photos staged this run but not used in the edition
    used = set(new["images"].values())
    for r in st["records"]:
        ref = r.get("_image")
        if ref and r.get("_imageNew") and ref not in used:  # only files this run created
            (ROOT / ref.lstrip("/")).unlink(missing_ok=True)

    hub_mb = (ROOT / "index.html").stat().st_size / 2**20
    if hub_mb >= 30:
        raise SystemExit(f"hub page is {hub_mb:.1f} MiB, over the 30 MiB budget")
    ed = st["proposal"]["edition"]
    st["published"] = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "n": ed["n"], "warnings": soft}
    save_state(d, st)
    report = (f"Published Edition {ed['n']} · {ed['date']}: {len(ed['items'])} stories; "
              f"{n_bm} added to the Benchmark Repository. "
              f"Archive now holds {len(new['editions'])} editions; hub page {hub_mb:.1f} MiB.")
    if soft:
        report += "\nLinks to check by hand:\n- " + "\n- ".join(soft)
    (d / "published.md").write_text(report + "\n")
    say(report)
    return report


def publish_benchmarks(st, archive):
    """Append the approved benchmark drafts to the hub's Benchmark Repository (append-only)."""
    from . import benchmarks
    p = st["proposal"]
    ids = p.get("benchmarks", [])
    if not ids:
        return 0
    benchmarks.check()
    edition = archive["editions"][0]
    items = {i["id"]: i for i in edition["items"]}
    recs = {r["key"]: r for r in st["records"]}
    taken = benchmarks.existing_ids()
    month = datetime.fromisoformat(st["date"]).strftime("%Y-%m")
    out, imgs = [], {}
    for sid in ids:
        r = recs[p["keys"][sid]]
        b = benchmarks.build(r["_bench"], items[sid], edition, taken, month)
        out.append(b)
        if archive["images"].get(sid):
            imgs[b["id"]] = archive["images"][sid]
    benchmarks.append_to_hub(out, imgs)
    reg = benchmarks.load_registry()
    reg["benchmarks"] += [{"id": b["id"], "edition": edition["n"], "story": b["prov"]["story"], "title": b["title"],
                           "brand": b["brand"], "added": b["added"]} for b in out]
    benchmarks.save_registry(reg)
    benchmarks.check()
    return len(out)


def preview(out, date=None):
    """Build the standalone CX Time page with the proposed edition, without touching the repo's data."""
    d = run_dir(date) if date else latest_run()
    st = load_state(d)
    archive = store.load()
    new = _apply(archive, st)
    out = Path(out).resolve()
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        shutil.copy(ROOT / "index.html", tmp / "index.html")
        (tmp / "img").symlink_to(ROOT / "img")
        (tmp / "sites").mkdir()
        store.write_hub(new, tmp / "index.html")
        subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "build_cx_time.py")], cwd=tmp, check=True)
        if out.exists():
            shutil.rmtree(out)
        shutil.copytree(tmp / "sites" / "cx-time", out)
    say(f"preview built in {out}")


# ---------------------------------------------------------------- spreadsheet mirror
XLSX_COLS = ["edition", "editionDate", "id", "format", "lead", "tag", "source", "sourceShort", "sourceUrl", "published",
             "meta", "title", "dek", "summary", "why", "excerpt", "oppTitle", "oppText", "opps", "lines", "insight",
             "speakers", "transcriptUrl", "keyInsights", "image", "imageCredit", "thumb", "relevance", "themes", "related"]


def write_xlsx(archive, path=XLSX):
    """Regenerated wholesale from the JSON on every publish; never edited by hand."""
    from openpyxl import Workbook
    from openpyxl.styles import Font
    wb = Workbook()
    ws = wb.active
    ws.title = "Records"
    ws.append(XLSX_COLS)
    for c in ws[1]:
        c.font = Font(bold=True)
    ws.freeze_panes = "A2"
    imgs = archive.get("images", {})
    for e in archive["editions"]:
        for it in e["items"]:
            row = []
            for col in XLSX_COLS:
                v = {"edition": e["n"], "editionDate": e["date"], "image": imgs.get(it["id"])}.get(col, it.get(col))
                if col == "opps":
                    v = " | ".join(f"{o['line']}: {o['title']} - {o['text']}" for o in (v or []))
                elif isinstance(v, list):
                    v = " | ".join(str(x) for x in v)
                elif isinstance(v, bool):
                    v = "TRUE" if v else "FALSE"
                row.append(v)
            ws.append(row)
    es = wb.create_sheet("Editions")
    es.append(["edition", "date", "stories", "read", "watch", "listen", "lines covered"])
    for c in es[1]:
        c.font = Font(bold=True)
    for e in archive["editions"]:
        fm = Counter(i["format"] for i in e["items"])
        lines = Counter(l for i in e["items"] for l in i["lines"])
        es.append([e["n"], e["date"], len(e["items"]), fm["read"], fm["watch"], fm["listen"],
                   ", ".join(f"{l} {n}" for l, n in lines.most_common())])
    wb.save(path)
