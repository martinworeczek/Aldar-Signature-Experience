"""Contact sheet for reviewing generated images (drafts or finals) before anything is applied.

Usage: python3 tools/image_contact_sheet.py DIR OUT.jpg [--band 16:7] [--cols 5]

DIR is a generator output folder: either DIR/<id>.png, or one sub-folder per id (DIR/<id>/<id>.png),
as the parallel runs in docs/image-generation.md produce. Titles come from DIR's prompts.json files.
--band crops each image the way the hub shows it (16:7 for customer-story cards, 3:2 otherwise).
It also prints a warning for images with a flat, blank band along the bottom edge (a known failure).
"""
import glob, json, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageStat

args = [a for a in sys.argv[1:]]
opt = {"--band": "3:2", "--cols": "5"}
for k in list(opt):
    if k in args: i = args.index(k); opt[k] = args[i + 1]; del args[i:i + 2]
assert len(args) == 2, __doc__
src, out = args
files = sorted(glob.glob(os.path.join(src, "*.png")) + glob.glob(os.path.join(src, "*", "*.png")))
assert files, f"no .png images in {src}"
titles = {}
for pj in glob.glob(os.path.join(src, "prompts.json")) + glob.glob(os.path.join(src, "*", "prompts.json")):
    for k, v in json.load(open(pj)).items(): titles[k] = v.get("title", "")

bw, bh = (int(x) for x in opt["--band"].split(":"))
cols = int(opt["--cols"]); W = 480; H = round(W * bh / bw); cap, pad = 30, 12
rows = (len(files) + cols - 1) // cols
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
except OSError:
    font = ImageFont.load_default()
sheet = Image.new("RGB", (cols * W + (cols + 1) * pad, rows * (H + cap) + (rows + 1) * pad), (14, 23, 29))
draw = ImageDraw.Draw(sheet)
for k, f in enumerate(files):
    key = os.path.splitext(os.path.basename(f))[0]
    im = Image.open(f).convert("RGB"); w, h = im.size
    g = im.convert("L")
    if ImageStat.Stat(g.crop((0, int(h * .94), w, h))).stddev[0] < 12:
        print(f"check {key}: flat band along the bottom edge")
    th = min(h, round(w * bh / bw)); tw = round(th * bw / bh); top = round((h - th) * .4); left = (w - tw) // 2
    tile = im.crop((left, top, left + tw, top + th)).resize((W, H), Image.LANCZOS)
    x = pad + (k % cols) * (W + pad); y = pad + (k // cols) * (H + cap + pad)
    sheet.paste(tile, (x, y))
    t = titles.get(key, ""); t = t if len(t) < 40 else t[:38] + "…"
    draw.text((x, y + H + 6), f"{key}  {t}", fill=(246, 243, 236), font=font)
sheet.save(out, quality=86)
print(f"{len(files)} images -> {out}")
