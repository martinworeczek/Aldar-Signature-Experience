"""Move images embedded in index.html's bundled scripts out into img/ files.

Usage: python3 -I tools/externalize_images.py

Every data: URI image inside a script/HTML asset in the bundle manifest is written to
img/<content-hash>.<ext> (identical images share one file) and the URI is replaced with
the absolute path "/img/<file>". The browser then fetches each image only when the view
that shows it renders, instead of downloading every image as part of the page.
Manifest-level image entries (referenced by uuid through the bundler) are left inline.
"""
import base64, gzip, hashlib, json, os, re

PAGE = "index.html"
OUT = "img"
URI = re.compile(r'data:image/(webp|jpeg|png|gif);base64,([A-Za-z0-9+/=]{200,})')

def main():
    html = open(PAGE, encoding="utf-8").read()
    m = re.search(r'(<script type="__bundler/manifest">\s*)(\{.*?\})(\s*</script>)', html, re.S)
    manifest = json.loads(m.group(2))
    os.makedirs(OUT, exist_ok=True)
    written, replaced = set(), 0

    def swap(mm):
        nonlocal replaced
        ext = "jpg" if mm.group(1) == "jpeg" else mm.group(1)
        data = base64.b64decode(mm.group(2))
        name = f"{hashlib.sha1(data).hexdigest()[:16]}.{ext}"
        if name not in written:
            with open(os.path.join(OUT, name), "wb") as f:
                f.write(data)
            written.add(name)
        replaced += 1
        return f"/{OUT}/{name}"

    for uid, e in manifest.items():
        if "javascript" not in e["mime"] and "html" not in e["mime"]:
            continue
        raw = base64.b64decode(e["data"])
        text = (gzip.decompress(raw) if e["compressed"] else raw).decode("utf-8")
        new = URI.sub(swap, text)
        if new != text:
            raw = new.encode("utf-8")
            e["data"] = base64.b64encode(gzip.compress(raw, 9) if e["compressed"] else raw).decode()

    out = html[:m.start(2)] + json.dumps(manifest, separators=(",", ":")) + html[m.end(2):]
    open(PAGE, "w", encoding="utf-8").write(out)
    print(f"replaced {replaced} references with {len(written)} files; page now {len(out)/1e6:.1f} MB")

if __name__ == "__main__":
    main()
