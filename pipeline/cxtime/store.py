"""The editions archive and the bundled page it feeds.

data/aldar-times.json is the master copy: {"editions": [...newest first], "stamp": ..., "images": {id: "/img/..."}}.
data/aldar-times.lock.json holds a fingerprint of every published edition. Publishing checks
that every earlier fingerprint still matches, so a past edition can never be rewritten or lost,
even by accident. index.html (the hub) carries the same data as window.AT_DATA / window.AT_IMG;
the publish step writes it there, and check() confirms the two agree.
"""
import base64, gzip, hashlib, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "data" / "aldar-times.json"
LOCK = ROOT / "data" / "aldar-times.lock.json"
HUB = ROOT / "index.html"
AT_DATA_ID, AT_IMG_ID = "9b89dde2", "87c04e48"
MANIFEST_RE = re.compile(r'(<script type="__bundler/manifest">\s*)(\{.*?\})(\s*</script>)', re.S)


class ArchiveError(RuntimeError):
    pass


def fingerprint(edition):
    """Stable hash of one edition: key order and whitespace do not matter, content does."""
    return hashlib.sha256(json.dumps(edition, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode()).hexdigest()


# ---------- the hub bundle ----------
def _asset_text(entry):
    raw = base64.b64decode(entry["data"])
    return (gzip.decompress(raw) if entry.get("compressed") else raw).decode("utf-8")


def _set_asset_text(entry, text):
    raw = text.encode("utf-8")
    entry["data"] = base64.b64encode(gzip.compress(raw, 9) if entry.get("compressed") else raw).decode()


def read_hub(hub=HUB):
    html = Path(hub).read_text(encoding="utf-8")
    m = MANIFEST_RE.search(html)
    man = json.loads(m.group(2))
    keys = {p: next(k for k in man if k.startswith(p)) for p in (AT_DATA_ID, AT_IMG_ID)}
    def parse(js, var):
        start = js.index("{", js.index(var))
        return json.JSONDecoder().raw_decode(js[start:])[0]
    data = parse(_asset_text(man[keys[AT_DATA_ID]]), "window.AT_DATA")
    imgs = parse(_asset_text(man[keys[AT_IMG_ID]]), "window.AT_IMG")
    return data, imgs


def write_hub(archive, hub=HUB):
    """Replace window.AT_DATA and window.AT_IMG in the bundled hub page; nothing else changes."""
    html = Path(hub).read_text(encoding="utf-8")
    m = MANIFEST_RE.search(html)
    man = json.loads(m.group(2))
    data = {"editions": archive["editions"], "stamp": archive.get("stamp")}
    for prefix, js in ((AT_DATA_ID, "window.AT_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n"),
                       (AT_IMG_ID, "window.AT_IMG = " + json.dumps(archive.get("images", {}), ensure_ascii=False) + ";\n")):
        key = next(k for k in man if k.startswith(prefix))
        _set_asset_text(man[key], js)
    html = html[:m.start(2)] + json.dumps(man, separators=(",", ":")) + html[m.end(2):]
    Path(hub).write_text(html, encoding="utf-8")


# ---------- the archive ----------
def load():
    if not ARCHIVE.exists():
        raise ArchiveError("data/aldar-times.json is missing. Run: python3 pipeline/run.py init")
    return json.loads(ARCHIVE.read_text(encoding="utf-8"))


def save(archive):
    ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    ARCHIVE.write_text(json.dumps(archive, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def load_lock():
    return json.loads(LOCK.read_text()) if LOCK.exists() else {}


def save_lock(archive):
    lock = {str(e["n"]): {"date": e["date"], "items": len(e["items"]), "sha256": fingerprint(e)}
            for e in archive["editions"]}
    LOCK.write_text(json.dumps(lock, indent=1) + "\n")


def init_from_hub():
    """One-off: take the archive exactly as it ships in the hub today and lock every edition."""
    if ARCHIVE.exists():
        raise ArchiveError("data/aldar-times.json already exists; init never overwrites it")
    data, imgs = read_hub()
    archive = {"editions": data["editions"], "stamp": data.get("stamp"), "images": imgs}
    save(archive)
    save_lock(archive)
    return archive


def verify_locked(archive):
    """Every edition in the lock must still be present and byte-for-byte the same."""
    lock = load_lock()
    by_n = {str(e["n"]): e for e in archive["editions"]}
    problems = []
    for n, rec in lock.items():
        if n not in by_n:
            problems.append(f"Edition {n} ({rec['date']}) is missing from the archive")
        elif fingerprint(by_n[n]) != rec["sha256"]:
            problems.append(f"Edition {n} ({rec['date']}) has been changed since it was published")
    ns = [e["n"] for e in archive["editions"]]
    if ns != sorted(ns, reverse=True):
        problems.append(f"Editions are not newest-first: {ns}")
    if len(set(ns)) != len(ns):
        problems.append(f"Duplicate edition numbers: {ns}")
    ids = [it["id"] for e in archive["editions"] for it in e["items"]]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        problems.append(f"Story ids are not unique across the archive: {dup}")
    if problems:
        raise ArchiveError("; ".join(problems))


def check_hub_matches(archive, hub=HUB):
    data, imgs = read_hub(hub)
    if data["editions"] != archive["editions"]:
        raise ArchiveError("index.html editions differ from data/aldar-times.json")
    if imgs != archive.get("images", {}):
        raise ArchiveError("index.html photo list differs from data/aldar-times.json")


def seen_urls(archive):
    return {canon_url(it["sourceUrl"]) for e in archive["editions"] for it in e["items"] if it.get("sourceUrl")}


def seen_titles(archive):
    return [it["title"] for e in archive["editions"] for it in e["items"]]


def canon_url(u):
    u = (u or "").strip()
    u = re.sub(r"^http://", "https://", u)
    u = re.sub(r"[?#].*$", "", u) if "podcasts.apple.com" not in u and "youtube.com/watch" not in u else re.sub(r"#.*$", "", u)
    u = re.sub(r"(\?|&)(utm_[^=&]+|ref|source)=[^&]*", "", u)
    u = u.replace("://www.", "://")
    return u.rstrip("/").lower()
