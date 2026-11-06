"""Restore CX Times editions retired by tools/retire_cxtime_editions.py (the inverse step).

Each edition is moved back from data/aldar-times-retired.json into the live archive exactly as it
was published: its fingerprint must equal the one recorded when it was retired, or nothing is
changed. Its photo refs come back too, and the lock, the hub page (AT_DATA/AT_IMG) and the xlsx
mirror are rewritten. Then rebuild the standalone site (tools/build_cx_time.py) and redeploy both.

Usage: python3 -I tools/restore_cxtime_editions.py 1 2
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))
from cxtime import store  # noqa: E402
from cxtime.pipeline import write_xlsx  # noqa: E402


def main(ns):
    ns = {int(n) for n in ns}
    archive = store.load()
    store.verify_locked(archive)
    retired = json.loads(store.RETIRED.read_text())
    back = [e for e in retired["editions"] if e["n"] in ns]
    if {e["n"] for e in back} != ns:
        sys.exit(f"not in the retired file: {sorted(ns - {e['n'] for e in back})}")
    live_ns = {e["n"] for e in archive["editions"]}
    if ns & live_ns:
        sys.exit(f"already live: {sorted(ns & live_ns)}")
    restored = []
    for e in back:
        e = {k: v for k, v in e.items() if k != "_retiredAt"}
        rec = retired["lock"].get(str(e["n"]))
        if not rec or store.fingerprint(e) != rec["sha256"]:
            sys.exit(f"Edition {e['n']} does not match its published fingerprint; nothing restored")
        restored.append(e)
    ids = {it["id"] for e in restored for it in e["items"]}

    archive["editions"] = sorted(archive["editions"] + restored, key=lambda e: -e["n"])
    archive.setdefault("images", {}).update({k: v for k, v in retired.get("images", {}).items() if k in ids})
    store.save(archive)
    store.save_lock(archive)
    store.verify_locked(archive)
    store.write_hub(archive)
    store.check_hub_matches(archive)
    write_xlsx(archive)

    retired["editions"] = [e for e in retired["editions"] if e["n"] not in ns]
    for n in ns: retired["lock"].pop(str(n), None)
    retired["images"] = {k: v for k, v in retired.get("images", {}).items() if k not in ids}
    store.RETIRED.write_text(json.dumps(retired, ensure_ascii=False, indent=1) + "\n")
    print(f"restored editions {sorted(ns)} ({len(ids)} stories); live: {[e['n'] for e in archive['editions']]}")


if __name__ == "__main__":
    main(sys.argv[1:])
