"""Retire CX Time editions from the live archive, keeping them in data/aldar-times-retired.json.

The archive (data/aldar-times.json) is append-only and every published edition is fingerprinted in
data/aldar-times.lock.json. Retiring is the one sanctioned way to take editions off the sites. It
must be asked for by Group CX, and it takes three steps:
  1. The editions, their photo refs and their lock records are moved, byte for byte, into the
     retired file. They are not deleted, and nothing in img/ is removed.
  2. The live archive, its lock, the hub page (AT_DATA/AT_IMG) and the xlsx mirror are rewritten
     without them.
  3. The retired stories' URLs and titles still count as "already published", so the weekly
     pipeline can't pick them up again (store.seen_urls/seen_titles read the retired file).
Then rebuild the standalone site (tools/build_cx_time.py) and redeploy both sites.

Usage: python3 -I tools/retire_cxtime_editions.py 1 2
"""
import json, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))
from cxtime import store  # noqa: E402
from cxtime.pipeline import write_xlsx  # noqa: E402


def main(ns):
    ns = {int(n) for n in ns}
    archive = store.load()
    store.verify_locked(archive)          # retire only from an intact archive
    store.check_hub_matches(archive)
    gone = [e for e in archive["editions"] if e["n"] in ns]
    if {e["n"] for e in gone} != ns:
        sys.exit(f"not in the archive: {sorted(ns - {e['n'] for e in gone})}")
    keep = [e for e in archive["editions"] if e["n"] not in ns]
    if not keep:
        sys.exit("refusing to retire every edition")
    gone_ids = {it["id"] for e in gone for it in e["items"]}
    lock = store.load_lock()

    retired = json.loads(store.RETIRED.read_text()) if store.RETIRED.exists() else {"editions": [], "images": {}, "lock": {}}
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for e in gone:
        retired["editions"].append(dict(e, _retiredAt=stamp))
        retired["lock"][str(e["n"])] = lock.get(str(e["n"]))
    retired["editions"].sort(key=lambda e: -e["n"])
    retired["images"].update({k: v for k, v in archive.get("images", {}).items() if k in gone_ids})
    store.RETIRED.write_text(json.dumps(retired, ensure_ascii=False, indent=1) + "\n")

    archive["editions"] = keep
    archive["images"] = {k: v for k, v in archive.get("images", {}).items() if k not in gone_ids}
    store.save(archive)
    store.save_lock(archive)              # the lock now covers exactly the live editions
    store.verify_locked(archive)
    store.write_hub(archive)
    store.check_hub_matches(archive)
    write_xlsx(archive)
    print(f"retired editions {sorted(ns)} ({len(gone_ids)} stories) to {store.RETIRED.relative_to(ROOT)}; "
          f"live: {[e['n'] for e in keep]}")


if __name__ == "__main__":
    main(sys.argv[1:])
