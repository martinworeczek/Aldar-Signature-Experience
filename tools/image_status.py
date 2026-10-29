"""Report per-asset image resolution status and delete img/ files nothing references.

Usage: python3 -I tools/image_status.py [ASSET_PREFIX] [--sheet OUT.png]
With ASSET_PREFIX, also lists that asset's images still at or below 1100px wide and can
write a numbered contact sheet of them.
"""
import base64, gzip, json, os, re, sys
from PIL import Image, ImageDraw

REF = re.compile(r'/img/[0-9a-f]{16}\.(?:webp|jpg|png|gif)')

def main(argv):
    html = open("index.html", encoding="utf-8").read()
    manifest = json.loads(re.search(r'<script type="__bundler/manifest">\s*(\{.*?\})\s*</script>', html, re.S).group(1))
    refs_by_asset, all_refs = {}, set()
    for uid, e in manifest.items():
        if "javascript" not in e["mime"] and "html" not in e["mime"]:
            continue
        raw = base64.b64decode(e["data"])
        text = (gzip.decompress(raw) if e["compressed"] else raw).decode("utf-8")
        refs = sorted(set(REF.findall(text)))
        if refs:
            refs_by_asset[uid] = refs
            all_refs.update(refs)
    pruned = 0
    for f in os.listdir("img"):
        if f"/img/{f}" not in all_refs:
            os.remove(os.path.join("img", f)); pruned += 1
    print(f"pruned {pruned} unreferenced file(s)")
    for uid, refs in refs_by_asset.items():
        low = [r for r in refs if Image.open(r[1:]).width <= 1100]
        print(f"{uid[:8]}: {len(refs)} images, {len(refs) - len(low)} high-res, {len(low)} remaining")
    if len(argv) > 0 and not argv[0].startswith("--"):
        uid = next(u for u in refs_by_asset if u.startswith(argv[0]))
        low = [r for r in refs_by_asset[uid] if Image.open(r[1:]).width <= 1100]
        if "--sheet" in argv and low:
            out = argv[argv.index("--sheet") + 1]
            W, H, cols = 300, 200, min(4, len(low))
            rows = (len(low) + cols - 1) // cols
            sheet = Image.new("RGB", (cols * W, rows * (H + 24)), "white"); d = ImageDraw.Draw(sheet)
            for i, r in enumerate(low):
                im = Image.open(r[1:]).convert("RGB"); im.thumbnail((W - 8, H - 8))
                x, y = (i % cols) * W, (i // cols) * (H + 24)
                sheet.paste(im, (x + 4, y + 4)); d.text((x + 6, y + H + 4), f"#{i + 1}", fill="black")
            sheet.save(out); print("sheet:", out)

if __name__ == "__main__":
    main(sys.argv[1:])
