"""Swap images embedded in index.html for higher-resolution originals.

Usage: python3 -I tools/replace_images.py [--apply] IMAGE [IMAGE ...]

Each new image is matched to the embedded image(s) it replaces by visual similarity
(not filename), so originals can be supplied under any name. Without --apply it only
reports matches. Images live either as manifest entries, as data: URIs inside gzip'd
script assets, or (after tools/externalize_images.py) as /img/<hash> files referenced
from those assets; all three are rewritten in place.
"""
import base64, gzip, hashlib, io, json, os, re, sys
from PIL import Image

PAGE = "index.html"
MATCH_MAX = 12.0   # mean abs diff (0-255) on a 24x24 grey thumbnail; above this = no match
ASPECT_TOL = 0.04

def sig(img):
    img = img.convert("L").resize((24, 24), Image.BILINEAR)
    return list(img.get_flattened_data()) if hasattr(img, "get_flattened_data") else list(img.getdata())

def diff(a, b):
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)

def load(b):
    im = Image.open(io.BytesIO(b)); im.load(); return im

def main(argv):
    apply = "--apply" in argv
    files = [a for a in argv if a != "--apply"]
    html = open(PAGE, encoding="utf-8").read()
    m = re.search(r'(<script type="__bundler/manifest">\s*)(\{.*?\})(\s*</script>)', html, re.S)
    manifest = json.loads(m.group(2))

    # Collect every embedded image: (where, key, mime/subtype, bytes)
    found = []
    assets = {}
    for uid, e in manifest.items():
        raw = base64.b64decode(e["data"])
        if e["mime"].startswith("image/") and e["mime"] != "image/svg+xml":
            found.append(("manifest", uid, None, raw))
        elif "javascript" in e["mime"] or "html" in e["mime"]:
            text = (gzip.decompress(raw) if e["compressed"] else raw).decode("utf-8")
            if "data:image/" in text:
                assets[uid] = text
                for d in set(re.findall(r'data:image/(?:webp|jpeg|png);base64,[A-Za-z0-9+/=]{200,}', text)):
                    found.append(("asset", uid, d, base64.b64decode(d.split(",", 1)[1])))
            for ref in set(re.findall(r'/img/[0-9a-f]{16}\.(?:webp|jpg|png|gif)', text)):
                assets[uid] = text
                found.append(("asset", uid, ref, open(ref[1:], "rb").read()))

    index = []
    for where, uid, uri, b in found:
        try:
            im = load(b)
        except Exception:
            continue
        index.append((where, uid, uri, im.size, sig(im)))

    replacements = []
    for f in files:
        new = open(f, "rb").read()
        im = load(new)
        ar, s = im.width / im.height, sig(im)
        cands = sorted(
            (diff(s, x[4]), x) for x in index
            if abs((x[3][0] / x[3][1]) - ar) / ar < ASPECT_TOL)
        hits = [c for c in cands if c[0] <= MATCH_MAX]
        if not hits:
            best = f"{cands[0][0]:.1f}" if cands else "n/a"
            print(f"NO MATCH  {f} {im.size} (closest diff {best})")
            continue
        best = hits[0][0]
        hits = [h for h in hits if h[0] <= best + 3]   # same picture used in several places
        for d, (where, uid, uri, size, _) in hits:
            if size[0] >= im.width:
                print(f"SKIP      {f} {im.size} -> {uid[:8]} already {size}")
                continue
            print(f"MATCH     {f} {im.size} -> {where}:{uid[:8]} was {size} (diff {d:.1f})")
            replacements.append((where, uid, uri, new, im.format))

    if not apply:
        return
    mime = {"WEBP": "image/webp", "JPEG": "image/jpeg", "PNG": "image/png"}
    for where, uid, uri, new, fmt in replacements:
        if where == "manifest":
            manifest[uid]["data"] = base64.b64encode(new).decode()
            manifest[uid]["mime"] = mime[fmt]
        else:
            if uri.startswith("/img/"):
                ext = {"WEBP": "webp", "JPEG": "jpg", "PNG": "png"}[fmt]
                ref = f"/img/{hashlib.sha1(new).hexdigest()[:16]}.{ext}"
                open(ref[1:], "wb").write(new)
                assets[uid] = assets[uid].replace(uri, ref)
            else:
                assets[uid] = assets[uid].replace(uri, f"data:{mime[fmt]};base64," + base64.b64encode(new).decode())
    for uid, text in assets.items():
        e = manifest[uid]
        raw = text.encode("utf-8")
        e["data"] = base64.b64encode(gzip.compress(raw, 9) if e["compressed"] else raw).decode()
    out = html[:m.start(2)] + json.dumps(manifest, separators=(",", ":")) + html[m.end(2):]
    open(PAGE, "w", encoding="utf-8").write(out)
    print(f"applied {len(replacements)} replacement(s); page now {len(out)/1e6:.1f} MB")

if __name__ == "__main__":
    main(sys.argv[1:])
