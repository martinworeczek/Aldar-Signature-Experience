"""Replace benchmark photographs in the hub (index.html's BM_IMAGES_A..D modules).

Usage: python3 tools/set_benchmark_image.py <benchmark-id>=<image file> [...]

Each image is converted to WebP (max 1800px wide), saved in img/ under a content-hash name (img/ is
served as immutable, so a new photo always gets a new name), and the benchmark's entry is pointed at it.
The old file is deleted when nothing else in index.html uses it. Then redeploy (Netlify rebuilds /mcp).
"""
import base64, gzip, hashlib, io, json, os, re, sys
from PIL import Image

PATH = "index.html"
pairs = [a.split("=", 1) for a in sys.argv[1:]]
assert pairs and all(len(p) == 2 for p in pairs), __doc__

html = open(PATH, encoding="utf-8").read()
mm = re.search(r'(<script type="__bundler/manifest">\s*)(\{.*?\})(\s*</script>)', html, re.S)
man = json.loads(mm.group(2))
mods = {}
for k, e in man.items():
    if "javascript" not in e.get("mime", ""): continue
    raw = base64.b64decode(e["data"]); s = (gzip.decompress(raw) if e.get("compressed") else raw).decode("utf-8")
    if re.match(r"\s*window\.BM_IMAGES_[A-D]\s*=", s): mods[k] = s

def everything():
    out = []
    for k, e in man.items():
        try:
            raw = base64.b64decode(e["data"]); out.append((gzip.decompress(raw) if e.get("compressed") else raw).decode("utf-8", "ignore"))
        except Exception: pass
    return "\n".join(out) + html[:mm.start(2)] + html[mm.end(2):]

retired = []
for bid, src in pairs:
    im = Image.open(src).convert("RGB")
    if im.width > 1800: im = im.resize((1800, round(im.height * 1800 / im.width)), Image.LANCZOS)
    o = io.BytesIO(); im.save(o, "WEBP", quality=86, method=6); o = o.getvalue()
    name = "/img/" + hashlib.sha256(o).hexdigest()[:16] + ".webp"
    open(name[1:], "wb").write(o)
    pat = re.compile(r'("' + re.escape(bid) + r'"\s*:\s*")([^"]+)(")')
    hit = [k for k, s in mods.items() if pat.search(s)]
    assert len(hit) == 1, f"{bid}: found in {len(hit)} image modules"
    k = hit[0]; old = pat.search(mods[k]).group(2)
    mods[k] = pat.sub(lambda m: m.group(1) + name + m.group(3), mods[k], count=1)
    if old != name: retired.append(old)
    print(f"{bid}: {old} -> {name} ({im.width}x{im.height}, {len(o) // 1024} KB)")

for k, s in mods.items():
    e = man[k]; b = s.encode("utf-8")
    if e.get("compressed"): b = gzip.compress(b, 9, mtime=0)
    e["data"] = base64.b64encode(b).decode()
html = html[:mm.start(2)] + json.dumps(man, separators=(",", ":")) + html[mm.end(2):]
open(PATH, "w", encoding="utf-8").write(html)

rest = everything()
for old in retired:
    if old.startswith("/img/") and old[1:] and os.path.exists(old[1:]) and old[5:] not in rest:
        os.remove(old[1:]); print("removed unused", old)
