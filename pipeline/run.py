#!/usr/bin/env python3
"""Aldar CX Time - weekly edition pipeline.

  python3 pipeline/run.py init                  one-off: create data/aldar-times.json from the hub
  python3 pipeline/run.py propose [--date D]    harvest -> screen -> enrich -> fact-check -> curate
  python3 pipeline/run.py revise FILE           apply review commands (/drop /add /lead /rerun /approve)
  python3 pipeline/run.py preview OUTDIR        build the standalone page with the proposed edition
  python3 pipeline/run.py publish [--anyway]    append the edition, update hub + standalone + xlsx
  python3 pipeline/run.py check                 archive locked, hub in step with the archive
  python3 pipeline/run.py review                re-render review.md for the latest run

Nothing is written to the archive or the sites until `publish`, which only runs after /approve.
"""
import argparse, os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # works under `python3 -I` too

from cxtime import pipeline, store  # noqa: E402


def gh_output(**kv):
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as f:
            for k, v in kv.items():
                f.write(f"{k}={v}\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    p = sub.add_parser("propose"); p.add_argument("--date"); p.add_argument("--only", nargs="*", help="limit to these source names (testing)")
    p = sub.add_parser("revise"); p.add_argument("file", help="text file holding the review comment"); p.add_argument("--date")
    p = sub.add_parser("preview"); p.add_argument("out"); p.add_argument("--date")
    p = sub.add_parser("publish"); p.add_argument("--date"); p.add_argument("--anyway", action="store_true")
    p.add_argument("--skip-url-check", action="store_true")
    sub.add_parser("check")
    p = sub.add_parser("review"); p.add_argument("--date")
    a = ap.parse_args()

    try:
        if a.cmd == "init":
            arc = store.init_from_hub()
            pipeline.write_xlsx(arc)
            print(f"archive created with {len(arc['editions'])} editions, all locked")
        elif a.cmd == "propose":
            d = pipeline.propose(a.date, a.only)
            st = pipeline.load_state(d)
            gh_output(run_dir=d.relative_to(store.ROOT), edition=st["proposal"]["edition"]["n"],
                      hold=str(st["proposal"]["hold"]).lower(), items=len(st["proposal"]["edition"]["items"]))
        elif a.cmd == "revise":
            approve, errors = pipeline.revise(Path(a.file).read_text(), a.date)
            gh_output(approve=approve or "", errors=len(errors))
        elif a.cmd == "preview":
            pipeline.preview(a.out, a.date)
        elif a.cmd == "publish":
            pipeline.publish(a.date, force=a.anyway, skip_url_check=a.skip_url_check)
        elif a.cmd == "check":
            arc = store.load()
            store.verify_locked(arc)
            store.check_hub_matches(arc)
            print(f"ok: {len(arc['editions'])} editions, all locked and in step with index.html")
        elif a.cmd == "review":
            d = pipeline.run_dir(a.date) if a.date else pipeline.latest_run()
            pipeline.write_review(d, pipeline.load_state(d), pipeline.cfg())
    except store.ArchiveError as e:
        sys.exit(f"ARCHIVE PROTECTION: {e}")


if __name__ == "__main__":
    main()
