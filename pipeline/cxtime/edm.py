"""Edition announcement EDM, design "5a Top Five" (docs/edm/README.md).

The five most relevant stories of the edition (the lead first, then the highest relevance in
edition order), each as a full-bleed photo board fading into forest green, with The story beside
Why it matters for Aldar (the Hub's own `why`, verbatim). Each board's Read / Watch / Listen
link goes to the source material; titles and the CTA go to the CX Time edition.

It fits the reading window. The card fills the pane up to 800px and shrinks to any narrower pane
or phone. Board photos are cut at 1600x1000, the shape of the widest panel (800x500), so CSS
`cover` only ever trims their sides, never the baked top fade, and boards join without a seam at
every width. Outlook for Windows gets 800px ghost tables and VML panels.

make_images() writes the board photos (flat filler bands trimmed, cover crop, both fades baked
in); make_patterns() draws the Sadu lozenge PNGs into sites/cx-time/email/assets/.
"""
import html
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageOps, ImageStat

from .store import ROOT

EMAIL_DIR = ROOT / "sites" / "cx-time" / "email"
PRE_PAD = "&#847;&zwnj;&nbsp;" * 70
F = "font-family:'Poppins','Helvetica Neue',Helvetica,Arial,sans-serif;"
X = "mso-line-height-rule:exactly;"
GREEN, GOLD, PALE, WHITE, BODY, MUTED = "#122216", "#D9B35C", "#F3DFA4", "#FFFFFF", "#ECEDEA", "#99936B"
RULE_TOP, RULE_COL = "#565B41", "#616448"
FMT = {"read": "Article", "watch": "Video", "listen": "Podcast"}
VERB = {"read": "Read", "watch": "Watch", "listen": "Listen to"}
CARD = 800


def e(s):
    return html.escape(s or "", quote=True).replace("&#x27;", "&rsquo;").replace("'", "&rsquo;")


def gap(n):
    return f'<div style="height:{n}px;line-height:{n}px;font-size:0;{X}">&nbsp;</div>'


def rule(w):
    return (f'<table role="presentation" width="{w}" cellpadding="0" cellspacing="0" border="0" style="width:{w}px">'
            f'<tr><td height="1" bgcolor="{GOLD}" style="height:1px;line-height:1px;font-size:0;background:{GOLD}">'
            f'&nbsp;</td></tr></table>')


# ---------------------------------------------------------------- images

def _cover(src, w, h, ax=0.5, ay=0.5):
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    s = max(w / im.width, h / im.height)
    im = im.resize((max(w, round(im.width * s)), max(h, round(im.height * s))), Image.LANCZOS)
    x, y = int((im.width - w) * ax), int((im.height - h) * ay)
    return im.crop((x, y, x + w, y + h))


def _ramp(t, stops):
    for (t0, a0), (t1, a1) in zip(stops, stops[1:]):
        if t <= t1:
            return a0 + (a1 - a0) * (t - t0) / ((t1 - t0) or 1)
    return stops[-1][1]


def _trim_bands(im):
    """Crop away pillarbox bands: columns (from either edge) whose luminance barely varies
    down the full height. Returns (image, trimmed?)."""
    g = im.convert("L")
    w, h = g.size
    def flat(x):
        return ImageStat.Stat(g.crop((x, 0, x + 1, h))).stddev[0] < 2.0
    left = 0
    while left < w // 3 and flat(left):
        left += 1
    right = w
    while right > w * 2 // 3 and flat(right - 1):
        right -= 1
    if left > 4 or w - right > 4:
        return im.crop((left + 6 if left > 4 else 0, 0, right - 6 if w - right > 4 else w, h)), True
    return im, False


GREEN_RGB = (18, 34, 22)


def board_photo(src):
    """1600x1000 board photo: bands trimmed, cover crop (anchor 55%/35%, 50% if trimmed), and both
    fades baked in green: top 1 -> 0 over 16% (joins the board above), bottom from 32% to solid
    at 100% (the pill and title sit on it, and its foot meets the green split row)."""
    W, H = 1600, 1000
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    im, trimmed = _trim_bands(im)
    s = max(W / im.width, H / im.height)
    im = im.resize((max(W, round(im.width * s)), max(H, round(im.height * s))), Image.LANCZOS)
    ax = 0.5 if trimmed else 0.55
    x, y = int((im.width - W) * ax), int((im.height - H) * 0.35)
    im = im.crop((x, y, x + W, y + H))
    top = [(0, 1), (.16, 0), (1, 0)]
    foot = [(0, 0), (.32, 0), (.48, .36), (.66, .82), (.84, .95), (1, 1)]
    col = Image.new("L", (1, H))
    for yy in range(H):
        t = yy / (H - 1)
        col.putpixel((0, yy), round(255 * max(_ramp(t, top), _ramp(t, foot))))
    return Image.composite(Image.new("RGB", (W, H), GREEN_RGB), im, col.resize((W, H)))


def _lozenge(path, w, h, units, peak, opaque):
    """Sadu lozenge line work in gold #E6C47F, drawn at 4x and faded across the width (README
    recipe). The band carries rules top and bottom; the minis are the motif alone."""
    S = 4
    W, H = w * S, h * S
    shape = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(shape)
    u = W / units
    cy = H / 2
    lw = round(1.6 * S)
    if units >= 10:
        for y in (3.5 * S, H - 3.5 * S):
            d.line([(0, y), (W, y)], fill=255, width=lw)
    for i in range(units):
        cx = u * (i + 0.5)
        hw, hh = 0.42 * u, 0.36 * H
        d.polygon([(cx - hw, cy), (cx, cy - hh), (cx + hw, cy), (cx, cy + hh)], outline=255, width=lw)
        d.polygon([(cx - hw / 2, cy), (cx, cy - hh / 2), (cx + hw / 2, cy), (cx, cy + hh / 2)], fill=255)
    for i in range(units + 1):
        x = u * i
        r = 1.1 * S * 2
        d.ellipse([x - r, cy - r, x + r, cy + r], fill=255)
        tw, th = 0.05 * H, 0.085 * H  # upright tick diamonds, taller than wide
        for ty in (cy - 0.26 * H, cy + 0.26 * H):
            d.polygon([(x - tw, ty), (x, ty - th), (x + tw, ty), (x, ty + th)], fill=255)
    shape = shape.resize((w, h), Image.LANCZOS)
    mask = Image.new("L", (w, 1))
    for x in range(w):
        mask.putpixel((x, 0), round(255 * peak * (1 - abs(2 * x / (w - 1) - 1))))
    alpha = ImageChops.multiply(shape, mask.resize((w, h)))
    gold = Image.new("RGBA", (w, h), (0xE6, 0xC4, 0x7F, 255))
    gold.putalpha(alpha)
    if opaque:
        out = Image.new("RGBA", (w, h), (0x14, 0x14, 0x14, 255))
        out.alpha_composite(gold)
        out.convert("RGB").save(path, "PNG", optimize=True)
    else:
        gold.save(path, "PNG", optimize=True)


def make_patterns():
    """The three Sadu PNGs (at 2x), shared by every edition: email/assets/."""
    out = EMAIL_DIR / "assets"
    out.mkdir(parents=True, exist_ok=True)
    specs = {"pat-sadu-band.png": (1040, 56, 20, .5, True),
             "pat-sadu-mini.png": (208, 56, 4, .6, True),
             "pat-sadu-mini-clear.png": (184, 50, 4, .75, False)}
    for name, (w, h, n, peak, opaque) in specs.items():
        if not (out / name).exists():
            _lozenge(out / name, w, h, n, peak, opaque)
    return out


def make_images(edition_n, srcs, base_url):
    """Write one board photo per story (None where a story has no photograph); return the URLs."""
    make_patterns()
    out = EMAIL_DIR / f"edition-{edition_n}"
    out.mkdir(parents=True, exist_ok=True)
    urls = []
    for k, src in enumerate(srcs, 1):
        if not src:
            urls.append(None)
            continue
        board_photo(src).save(out / f"top5-{k:02d}.jpg", "JPEG", quality=76, optimize=True, progressive=True)
        urls.append(f"{base_url}/email/edition-{edition_n}/top5-{k:02d}.jpg")
    return urls


# ---------------------------------------------------------------- html

HEAD = """<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:w="urn:schemas-microsoft-com:office:word">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta name="x-apple-disable-message-reformatting">
<meta name="format-detection" content="telephone=no,address=no,email=no,date=no">
<meta name="color-scheme" content="dark">
<meta name="supported-color-schemes" content="dark">
<title>Aldar CX Times &middot; Edition {n} &middot; Top five</title>
<!--[if mso]><noscript><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml></noscript><style>td,div,a,span,p{{font-family:Arial,Helvetica,sans-serif !important}}</style><![endif]-->
<!--[if !mso]><!--><link href="https://fonts.googleapis.com/css2?family=Poppins:wght@200;300;400;500;600&display=swap" rel="stylesheet"><style>@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@200;300;400;500;600&display=swap');</style><!--<![endif]-->
<style>
body{{margin:0!important;padding:0!important;width:100%!important;-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%}}
table{{border-collapse:collapse;mso-table-lspace:0pt;mso-table-rspace:0pt}}
img{{border:0;outline:none;text-decoration:none;-ms-interpolation-mode:bicubic}}
a[x-apple-data-detectors]{{color:inherit!important;text-decoration:none!important}}
@media screen and (max-width:620px){{
.w{{width:100%!important;max-width:100%!important}}
.st{{display:block!important;width:100%!important;max-width:100%!important;box-sizing:border-box}}
.px{{padding-left:24px!important;padding-right:24px!important}}
.hs{{display:none!important}}
.bl0{{border-left:0!important;padding-left:0!important;padding-top:20px!important}}
.ph5{{height:auto!important}}
.bsp{{height:150px!important;line-height:150px!important;max-height:none!important}}
.h2{{font-size:30px!important;line-height:35px!important}}
.mast{{font-size:44px!important;line-height:46px!important}}
.outer{{padding:0!important}}
.cta{{padding:18px 24px!important;letter-spacing:2px!important}}
}}
</style>
</head>
"""


def _board(k, s, url, last):
    """One story: Row A, the photo panel with pill and title; Row B, the gold-ruled split."""
    label = "Signal of the week" if s.get("lead") else f'{FMT.get(s["format"], "Article")} &middot; {e(s.get("sourceShort") or s.get("source"))}'
    img = e(s.get("image") or "")
    # a board without a photograph is just its pill and title on green, sized to its text
    h_attr = ' height="500"' if img else ""
    h_css = "height:500px;" if img else ""
    spacer = ('<div class="bsp" style="height:0;line-height:0;font-size:0;max-height:0;overflow:hidden">&nbsp;</div>'
              if img else "")
    bg_attr = f' background="{img}"' if img else ""
    bg_css = f"background:{GREEN} url({img}) center bottom / cover no-repeat" if img else f"background:{GREEN}"
    vml_o = (f'<!--[if mso]><v:rect xmlns:v="urn:schemas-microsoft-com:vml" fill="true" stroke="false" style="width:{CARD}px;height:500px">'
             f'<v:fill type="frame" src="{img}" color="{GREEN}"/><v:textbox inset="0,0,0,0" style="mso-fit-shape-to-text:true"><![endif]-->') if img else ""
    vml_c = '<!--[if mso]></v:textbox></v:rect><![endif]-->' if img else ""
    src_url = e(s.get("sourceUrl") or url)
    lbl = f"{F}font-size:10px;line-height:14px;{X}color:{PALE};letter-spacing:2.8px;text-transform:uppercase;"
    return f"""<tr><td style="padding:0">
{vml_o}
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="{GREEN}"{bg_attr} style="width:100%;{bg_css}"><tr><td class="px ph5"{h_attr} valign="bottom" style="{h_css}padding:0 40px;vertical-align:bottom">
{spacer}
<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="border-collapse:separate"><tr><td bgcolor="#1F2A1F" style="background:#1F2A1F;background:rgba(18,14,10,.45);border:1px solid #A39A72;border:1px solid rgba(243,223,164,.6);border-radius:999px;padding:6px 14px 6px 12px;{F}font-size:10px;line-height:14px;{X}color:{PALE};letter-spacing:2.4px;text-transform:uppercase;white-space:nowrap;"><span style="color:{GOLD};font-size:9px;text-shadow:0 0 10px {GOLD}">&#9679;</span>&nbsp;&nbsp;{k:02d} &middot; {label}</td></tr></table>{gap(18)}
<div class="h2" style="{F}font-size:40px;line-height:44px;{X}color:{WHITE};font-weight:200;letter-spacing:-1px;max-width:640px;"><a href="{url}" target="_blank" style="color:{WHITE};text-decoration:none">{e(s["title"])}</a></div>{gap(26)}
</td></tr></table>
{vml_c}
</td></tr>
<tr><td class="px" bgcolor="{GREEN}" style="padding:0 40px;background:{GREEN}">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;border-top:1px solid {RULE_TOP}"><tr>
<td class="st" width="36%" valign="top" style="width:36%;padding:22px 0 0">
<div style="{lbl}">The story</div>{gap(12)}
<div style="{F}font-size:14px;line-height:22px;{X}color:{BODY};font-weight:300;">{e(s["dek"])}</div></td>
<td class="hs" width="24" style="width:24px;font-size:0">&nbsp;</td>
<td class="st bl0" valign="top" style="padding:22px 0 0 24px;border-left:1px solid {RULE_COL}">
<div style="{lbl}">Why it matters for Aldar</div>{gap(12)}
<div style="{F}font-size:16px;line-height:25px;{X}color:{PALE};font-weight:300;">{e(s["why"])}</div></td>
</tr></table>{gap(24)}
<a href="{src_url}" target="_blank" style="{F}font-size:11px;line-height:15px;{X}color:{GOLD};letter-spacing:2.6px;text-transform:uppercase;font-weight:500;text-decoration:none;">{VERB.get(s["format"], "Read")} the story&nbsp;&nbsp;&rarr;</a>
{gap(8 if last else 44)}
</td></tr>
"""


def more_line(rest):
    if rest <= 0:
        return "Every story, and a Signature Experience<br class=\"hs\"> to explore for each."
    noun = "story" if rest == 1 else "stories"
    return f"{rest} more {noun}, and a Signature Experience<br class=\"hs\"> to explore for each."


def render(d):
    """d: number, date, preheader, editionUrl, assetsUrl, total (stories in the edition), credits,
    stories=[{lead, format, sourceShort, title, dek, why, sourceUrl, image}] (up to five)."""
    url = e(d["editionUrl"])
    n = d["number"]
    assets = d["assetsUrl"].rstrip("/")
    boards = "".join(_board(k, s, url, k == len(d["stories"])) for k, s in enumerate(d["stories"], 1))
    credits = " &middot; ".join(e(c) for c in d.get("credits", []))
    credit_html = (f'{gap(16)}<div style="{F}font-size:9px;line-height:14px;{X}color:{MUTED};">Images: {credits}</div>'
                   if credits else "")
    mini = f'<img src="{assets}/pat-sadu-mini-clear.png" width="92" height="25" alt="" style="display:block;width:92px;height:25px;border:0">'
    body = f"""<body style="margin:0;padding:0;background:#0B0907" bgcolor="#0B0907">
<div style="display:none;font-size:1px;line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden;mso-hide:all;color:#0B0907">{e(d["preheader"])}{PRE_PAD}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#0B0907" style="width:100%;background:#0B0907"><tr><td class="outer" align="center" style="padding:32px 0 48px">
<!--[if mso]><table role="presentation" width="{CARD}" cellpadding="0" cellspacing="0" border="0" align="center"><tr><td><![endif]-->
<table role="presentation" class="w" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="{GREEN}" style="width:100%;max-width:{CARD}px;background:{GREEN};margin:0 auto">
<tr><td class="px" align="center" bgcolor="{GREEN}" style="padding:48px 40px 0;text-align:center;background:{GREEN}">
<div style="{F}font-size:13px;line-height:17px;{X}color:{WHITE};letter-spacing:11px;text-transform:uppercase;padding-left:11px;">Aldar</div>{gap(10)}
<div class="mast" style="{F}font-size:54px;line-height:56px;{X}color:{WHITE};font-weight:200;letter-spacing:1px;"><span style="color:{GOLD};font-weight:400">CX</span>&nbsp;Times</div>{gap(14)}
<table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center" style="margin:0 auto"><tr><td width="56" valign="middle" style="width:56px">{rule(56)}</td><td valign="middle" style="padding:0 10px">{mini}</td><td width="56" valign="middle" style="width:56px">{rule(56)}</td></tr></table>{gap(26)}
<div style="{F}font-size:10px;line-height:14px;{X}color:{BODY};letter-spacing:2.6px;text-transform:uppercase;"><span style="color:{PALE}">Edition {n}</span>&nbsp;&nbsp;&middot;&nbsp;&nbsp;{e(d["date"])}</div>{gap(36)}
</td></tr>
{boards}<tr><td class="px" bgcolor="{GREEN}" style="padding:56px 24px 0;background:{GREEN}">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#0F1D12" style="width:100%;background:#0F1D12;background-image:linear-gradient(180deg,#1A2E1E 0%,#0D1910 100%);border:1px solid {RULE_TOP};border-collapse:separate;border-radius:4px"><tr><td align="center" class="px" style="padding:54px 44px 52px;text-align:center">
<div style="{F}font-size:10px;line-height:14px;{X}color:{PALE};letter-spacing:3px;text-transform:uppercase;">Edition {n} is live in the Hub</div>{gap(18)}
<div style="{F}font-size:38px;line-height:44px;{X}color:{WHITE};font-weight:200;letter-spacing:-.5px;">Step inside<br>the edition.</div>{gap(18)}
<div style="{F}font-size:15px;line-height:24px;{X}color:{BODY};font-weight:300;">{more_line(d["total"] - len(d["stories"]))}</div>{gap(34)}
<!--[if mso]><v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" href="{url}" style="height:60px;v-text-anchor:middle;width:340px" arcsize="50%" stroke="f" fillcolor="{GOLD}"><w:anchorlock/><center style="color:#0C1C27;font-family:Arial,sans-serif;font-size:14px;font-weight:bold;letter-spacing:3px">READ THE EDITION &rarr;</center></v:roundrect><![endif]-->
<!--[if !mso]><!--><table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center" style="border-collapse:separate;margin:0 auto"><tr><td align="center" bgcolor="#E8CD8D" style="background:#E8CD8D;background-image:linear-gradient(90deg,#F7E7BE 0%,{GOLD} 100%);border-radius:999px;box-shadow:0 10px 30px rgba(217,179,92,.28)"><a class="cta" href="{url}" target="_blank" style="display:block;padding:21px 46px;{F}font-size:14px;line-height:18px;{X}color:#0C1C27;font-weight:600;letter-spacing:3px;text-transform:uppercase;text-decoration:none;">Read the edition&nbsp;&nbsp;&rarr;</a></td></tr></table><!--<![endif]-->
</td></tr></table></td></tr>
<tr><td class="px" align="center" bgcolor="{GREEN}" style="padding:48px 40px 40px;text-align:center;background:{GREEN}">
<img src="{assets}/pat-sadu-mini-clear.png" width="104" height="28" alt="" style="display:block;width:104px;height:28px;border:0;margin:0 auto">{gap(22)}
<div style="{F}font-size:9px;line-height:13px;{X}color:{MUTED};letter-spacing:2.4px;text-transform:uppercase;">Curated by Aldar Group Customer Experience</div>{credit_html}</td></tr>
</table>
<!--[if mso]></td></tr></table><![endif]-->
</td></tr></table>
</body>
</html>
"""
    return HEAD.format(n=n) + body
