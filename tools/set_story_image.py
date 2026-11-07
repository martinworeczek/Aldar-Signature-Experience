"""Set a customer story's photograph (data/customer-stories.js).

Usage: python3 tools/set_story_image.py [--generated] <story-id>=<image file>[@<photo_position>] [...]

The image is converted to WebP (quality 90, max 2400px wide; a WebP up to that width is kept byte for
byte), saved in img/ under a content-hash name and set as the story's `photo`. `photo_position` (the
crop of the card's 16:7 band, CSS background-position) defaults to "center 40%".
--generated marks it as an AI illustration in data/generated-images.json ("stories"), so the hub labels
it; setting a story's image without the flag (a real photograph) takes it off that list.
The old file is deleted when nothing else uses it. Then run tools/apply_features.py and redeploy.
"""
import hashlib, io, json, os, re, subprocess, sys
from PIL import Image

DATA, GEN_PATH, MAX_W = "data/customer-stories.js", "data/generated-images.json", 2400
GEN = "--generated" in sys.argv
pairs = [a.split("=", 1) for a in sys.argv[1:] if a != "--generated"]
assert pairs and all(len(p) == 2 for p in pairs), __doc__

src = open(DATA, encoding="utf-8").read()
m = re.search(r"window\.CS_DATA\s*=\s*(\{.*\})(\s*;?\s*)$", src, re.S)
d = json.loads(m.group(1))
by = {s["id"]: s for s in d["stories"]}
gen = json.load(open(GEN_PATH, encoding="utf-8")) if os.path.exists(GEN_PATH) else {}
retired = []

for sid, spec in pairs:
    path, _, pos = spec.partition("@")
    assert sid in by, f"no story {sid}"
    im = Image.open(path)
    if im.format == "WEBP" and im.width <= MAX_W:
        o = open(path, "rb").read()
    else:
        im = im.convert("RGB")
        if im.width > MAX_W: im = im.resize((MAX_W, round(im.height * MAX_W / im.width)), Image.LANCZOS)
        b = io.BytesIO(); im.save(b, "WEBP", quality=90, method=6); o = b.getvalue()
    name = "/img/" + hashlib.sha256(o).hexdigest()[:16] + ".webp"
    open(name[1:], "wb").write(o)
    s = by[sid]; old = s.get("photo")
    s["photo"] = name; s["photo_position"] = pos or s.get("photo_position") or "center 40%"
    if old and old != name: retired.append(old)
    if GEN: gen.setdefault("stories", {})[sid] = name
    else: gen.setdefault("stories", {}).pop(sid, None)
    print(f"{sid}: {old or '-'} -> {name} ({im.width}x{im.height}, {len(o) // 1024} KB)")

open(DATA, "w", encoding="utf-8").write(src[:m.start(1)] + json.dumps(d, indent=1, ensure_ascii=False) + m.group(2))
json.dump(gen, open(GEN_PATH, "w", encoding="utf-8"), indent=1, sort_keys=True)

# remove replaced files that nothing in the repository uses any more
for old in retired:
    if old.startswith("/img/") and os.path.exists(old[1:]):
        used = subprocess.run(["git", "grep", "-l", old[5:], "--", ".", ":!img"], capture_output=True, text=True).stdout.strip()
        if not used and old[5:] not in open(DATA, encoding="utf-8").read():
            os.remove(old[1:]); print("removed unused", old)
