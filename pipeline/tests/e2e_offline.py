"""End-to-end check of the weekly pipeline with no network and no API key.

Builds a throwaway copy of the repo, serves fake feeds/articles/photos on localhost, runs
propose -> revise -> publish with the mock editor, then proves the archive guarantees:
Editions 1-2 unchanged, Edition 3 appended, hub + standalone + xlsx in step, and a tampered
past edition is refused.

  python3 pipeline/tests/e2e_offline.py [--keep DIR]
"""
import functools, http.server, io, json, os, shutil, subprocess, sys, tempfile, threading
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RUN_DATE = "2026-11-02"


def make_fixtures(web: Path, port: int):
    from PIL import Image
    base = f"http://127.0.0.1:{port}"
    now = datetime.fromisoformat(RUN_DATE).replace(tzinfo=timezone.utc)
    words = ("The arrival sequence was redesigned around a named host, scent, sound and light so that guests "
             "feel recognised within ninety seconds of stepping inside. ") * 12
    def img(name, color):
        Image.new("RGB", (1600, 1000), color).save(web / name, "JPEG", quality=90)
    feeds = {
        "hotels": ("read", ["A Lisbon hotel replaces check-in with a welcome ritual", "Resort spa builds evening wind-down rooms",
                            "Boutique chain names a host for every arriving guest", "Quarterly earnings out of scope"]),
        "retail": ("read", ["Tokyo mall stages weekend community markets", "Department store turns fitting rooms into lounges",
                            "Outlet village hires greeters for families"]),
        "schools": ("read", ["School network redesigns the first day for parents", "Campus tours become student-led stories"]),
        "video": ("watch", ["Inside a theme park's queue storytelling", "How a stadium choreographs match-day arrival",
                            "Museum night openings for local residents"]),
        "pod": ("listen", ["Designing belonging in new neighbourhoods", "The service recovery playbook of a cruise line",
                           "Why hotel lobbies became living rooms"]),
    }
    sources = []
    for name, (fmt, titles) in feeds.items():
        items = []
        for i, t in enumerate(titles):
            slug = f"{name}-{i}"
            img(f"{slug}.jpg", (40 + 30 * i, 80, 120))
            (web / f"{slug}.html").write_text(
                f"<html><head><meta property='og:image' content='{base}/{slug}.jpg'><title>{t}</title></head>"
                f"<body><article><h1>{t}</h1>" + "".join(f"<p>{words}</p>" for _ in range(3)) + "</article></body></html>")
            when = format_datetime(now - timedelta(days=1 + i))
            items.append(f"<item><title>{t}</title><link>{base}/{slug}.html</link><pubDate>{when}</pubDate>"
                         f"<description>{words}</description><itunes:duration>2280</itunes:duration>"
                         f"<itunes:image href='{base}/{slug}.jpg'/></item>")
        # one stale item outside both windows
        items.append(f"<item><title>Old story {name}</title><link>{base}/old-{name}.html</link>"
                     f"<pubDate>{format_datetime(now - timedelta(days=90))}</pubDate><description>x</description></item>")
        (web / f"{name}.xml").write_text(
            "<?xml version='1.0'?><rss version='2.0' xmlns:itunes='http://www.itunes.com/dtds/podcast-1.0.dtd'>"
            f"<channel><title>{name}</title>{''.join(items)}</channel></rss>")
        sources.append(f'''
[[sources]]
name = "Fixture {name}"
short = "{name}"
kind = "rss"
format = "{fmt}"
url = "{base}/{name}.xml"
tag = "Portfolio"
lines = ["All lines"]
weight = 2
''')
    (web / "robots.txt").write_text("User-agent: *\nAllow: /\n")
    return sources


def run(cmd, cwd, env, ok=True):
    print("$", " ".join(cmd))
    r = subprocess.run(cmd, cwd=cwd, env=env, text=True, capture_output=True)
    print(r.stdout[-3000:], r.stderr[-3000:])
    if ok and r.returncode:
        raise SystemExit(f"FAILED: {' '.join(cmd)}")
    return r


def main():
    keep = sys.argv[sys.argv.index("--keep") + 1] if "--keep" in sys.argv else None
    tmp = Path(keep or tempfile.mkdtemp(prefix="cxtime-e2e-"))
    if tmp.exists() and keep:
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    repo = tmp / "repo"
    repo.mkdir()
    for p in ("index.html", "netlify.toml"):
        shutil.copy(REPO / p, repo / p)
    for p in ("pipeline", "tools", "data"):
        shutil.copytree(REPO / p, repo / p, ignore=shutil.ignore_patterns("cxtime-runs", "__pycache__"))
    (repo / "data" / "cxtime-seen.json").unlink(missing_ok=True)
    subprocess.run(["cp", "-al", str(REPO / "img"), str(repo / "img")], check=True)  # hard links: cheap
    (repo / "sites").mkdir()

    web = tmp / "web"
    web.mkdir()
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(web))
    handler.log_message = lambda *a: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    srcs = make_fixtures(web, port)
    cfg = (REPO / "pipeline" / "config.toml").read_text()
    cfg = cfg[: cfg.index("[[sources]]")] + "".join(srcs)
    cfg = cfg.replace("delay_seconds = 1.5", "delay_seconds = 0")
    (repo / "pipeline" / "config.toml").write_text(cfg)

    env = {**os.environ, "CXTIME_MOCK_LLM": "1", "NO_PROXY": "127.0.0.1,localhost", "no_proxy": "127.0.0.1,localhost"}
    py = [sys.executable, "pipeline/run.py"]
    before = json.loads((repo / "data" / "aldar-times.json").read_text())
    N = max(e["n"] for e in before["editions"]) + 1  # the edition this test proposes

    run(py + ["propose", "--date", RUN_DATE], repo, env)
    rd = repo / "data" / "cxtime-runs" / RUN_DATE
    st = json.loads((rd / "state.json").read_text())
    ed = st["proposal"]["edition"]
    print("proposed:", [(i["id"], i["title"][:40], i["lead"]) for i in ed["items"]])
    assert ed["n"] == N and ed["items"], "next edition proposed"
    assert sum(i["lead"] for i in ed["items"]) == 1
    assert all(i["format"] in ("read", "watch", "listen") for i in ed["items"])
    assert sum(i["format"] == "read" for i in ed["items"]) <= 6
    assert not any("Old story" in i["title"] for i in ed["items"]), "stale items excluded"
    assert not any("earnings" in i["title"].lower() for i in ed["items"]), "gate drops out-of-scope"
    assert len(ed["items"]) >= 8, "a full edition from strong supply"
    from collections import Counter
    assert max(Counter(i["source"] for i in ed["items"]).values()) <= 2, "max 2 per source"
    assert "sourceText" not in (rd / "state.json").read_text(), "no source text persisted"
    assert (rd / "review.md").exists()

    # reviewer: drop one, choose another lead, then approve
    drop_id = ed["items"][1]["id"]
    lead_id = next(i["id"] for i in ed["items"] if i["format"] == "watch")
    assert st["proposal"]["benchmarks"] == [], "benchmarks are opt-in: none selected by default"
    drafts = [i for i in st["proposal"]["benchDrafts"] if i != drop_id]
    bench_on, bench_off = drafts[0], (drafts[1] if len(drafts) > 1 else None)
    (tmp / "c1.txt").write_text(f"Looks good.\n/drop {drop_id}\n/lead {lead_id}\n/bench {bench_on}\n"
                                + (f"/bench {bench_off}\n/nobench {bench_off}\n" if bench_off else ""))
    run(py + ["revise", str(tmp / "c1.txt")], repo, env)
    st2 = json.loads((rd / "state.json").read_text())
    ed2 = st2["proposal"]["edition"]
    dropped_key = st["proposal"]["keys"][drop_id]
    assert dropped_key not in st2["proposal"]["keys"].values(), "drop applied"
    lead = next(i for i in ed2["items"] if i["lead"])
    assert st2["proposal"]["keys"][lead["id"]] == st["proposal"]["keys"][lead_id], "lead applied"

    run(py + ["preview", str(tmp / "preview")], repo, env)
    assert (tmp / "preview" / "index.html").exists()

    run(py + ["publish", "--skip-url-check"], repo, env)
    after = json.loads((repo / "data" / "aldar-times.json").read_text())
    assert [e["n"] for e in after["editions"]] == [N] + [e["n"] for e in before["editions"]]
    assert after["editions"][1:] == before["editions"], "earlier editions untouched"
    r = run(py + ["check"], repo, env)
    assert (repo / "data" / "aldar-times.xlsx").exists()
    reg = json.loads((repo / "data" / "benchmarks-from-times.json").read_text())["benchmarks"]
    page = repo / "sites" / "cx-time" / "email" / f"edition-{N}" / "index.html"
    em = page.read_text() if page.exists() else ""
    ed_n = after["editions"][0]
    assert "Read the edition" in em and "</span>&nbsp;Times" in em and em.count("&#9679;") == min(5, len(ed_n["items"])), "EDM built (5a, top five)"
    assert "Signal of the week" in em and "Why it matters for Aldar" in em, "lead board and the curated why"
    lead = next(i for i in ed_n["items"] if i["lead"])
    assert f'href="{lead["sourceUrl"]}"' in em, "Read the story links to the source"
    assert 'max-width:800px' in em, "EDM is fluid: fits the reading window"
    from PIL import Image as _I
    assert _I.open(page.parent / "top5-01.jpg").size == (1600, 1000), "board photos cut to the widest panel"
    assert (page.parents[1] / "assets" / "pat-sadu-mini-clear.png").exists(), "Sadu patterns written"
    box = json.loads((repo / "data" / "cxtime-outbox.json").read_text())["emails"]
    assert len([m for m in box if m["edition"] == N]) == 1
    assert len(reg) == 1 and reg[0]["edition"] == N, "only the /bench-selected draft is added, with provenance"
    assert all(b["story"] != bench_off for b in reg), "/nobench withdraws a /bench"
    sys.path.insert(0, str(repo / "pipeline"))
    from cxtime import benchmarks as B
    ids = B.existing_ids(repo / "index.html")
    assert all(b["id"] in ids for b in reg)
    from openpyxl import load_workbook
    rows = list(load_workbook(repo / "data" / "aldar-times.xlsx")["Records"].values)
    assert len(rows) - 1 == sum(len(e["items"]) for e in after["editions"]), "xlsx mirrors whole archive"
    for it in after["editions"][0]["items"]:
        if it.get("imageKey"):
            assert (repo / after["images"][it["id"]].lstrip("/")).exists()
    stand = (repo / "sites" / "cx-time" / "index.html").read_text()
    assert len(stand) > 100000

    # a second publish of the same run must be refused (edition number already used)
    r = run(py + ["publish", "--skip-url-check"], repo, env, ok=False)
    assert r.returncode != 0, "re-publish refused"

    # tamper with a past edition: everything must refuse to proceed
    bad = json.loads((repo / "data" / "aldar-times.json").read_text())
    bad["editions"][2]["items"][0]["title"] = "Rewritten history"
    (repo / "data" / "aldar-times.json").write_text(json.dumps(bad))
    r = run(py + ["check"], repo, env, ok=False)
    assert r.returncode != 0 and "ARCHIVE PROTECTION" in (r.stdout + r.stderr), "tampering detected"
    print(f"\nALL CHECKS PASSED  (work dir: {tmp})")
    srv.shutdown()


if __name__ == "__main__":
    main()
