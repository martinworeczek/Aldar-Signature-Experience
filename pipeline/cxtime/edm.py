"""Edition announcement EDM, design "4b Sadu Thread" (docs/edm/README.md).

render(data) returns send-ready email HTML that follows the approved reference file: nested
presentation tables, inline styles, Outlook conditionals and VML, a hidden preheader, Poppins
with Arial for Outlook, and no "For Aldar" lines.

It fits the reading window. The card is fluid (100% wide, at most 600px), so it shrinks to a
narrow reading pane or a phone even where media queries are ignored. The story spreads are
"fluid hybrid": two inline-blocks that sit side by side when there is room and stack when there
isn't (image first in every row, via the dir="rtl" swap on 02). Outlook for Windows, which
supports neither, gets fixed 600px ghost tables.

make_images() writes the JPEG crops: the hero at 1200x1120 with both fades baked into the pixels,
and the story photos at 528x660. make_patterns() draws the Sadu lozenge PNGs. Everything is
written under sites/cx-time/email/ and so is hosted with the CX Time site.
"""
import html
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageOps, ImageStat

from .store import ROOT

EMAIL_DIR = ROOT / "sites" / "cx-time" / "email"
PRE_PAD = "&#847;&zwnj;&nbsp;" * 70
F = "font-family:'Poppins','Helvetica Neue',Helvetica,Arial,sans-serif;"
X = "mso-line-height-rule:exactly;"
IVORY, BODY, MUTED, RULE, HI, INK = "#F3EFE6", "#C4BFB5", "#8E897F", "#D9B46A", "#E6C47F", "#0E0E0E"


def e(s):
    return html.escape(s or "", quote=True).replace("&#x27;", "&rsquo;").replace("'", "&rsquo;")


def gap(n):
    return f'<div style="height:{n}px;line-height:{n}px;font-size:0;{X}">&nbsp;</div>'


def rule(w):
    return (f'<table role="presentation" width="{w}" cellpadding="0" cellspacing="0" border="0" style="width:{w}px">'
            f'<tr><td height="1" bgcolor="{RULE}" style="height:1px;line-height:1px;font-size:0;background:{RULE}">'
            f'&nbsp;</td></tr></table>')


def two_lines(headline):
    """The headline is set on two lines. An explicit line break wins; otherwise split the words
    where the two lines come out most even ("Worth leaving / home for.")."""
    if "\n" in headline:
        return "<br>".join(e(p.strip()) for p in headline.split("\n", 1))
    w = headline.split()
    if len(w) < 2:
        return e(headline)
    best = min(range(1, len(w)), key=lambda k: max(len(" ".join(w[:k])), len(" ".join(w[k:]))))
    return e(" ".join(w[:best])) + "<br>" + e(" ".join(w[best:]))


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


def _p99(zone):
    hist, acc = zone.histogram(), 0
    n = sum(hist)
    for v, c in enumerate(hist):
        acc += c
        if acc >= n * 0.99:
            return v
    return 255


def _hero(src):
    """1200x1120 cover crop (anchor 35% / 50%) with the two fades baked in: darkened behind the
    masthead, solid card colour at the foot. Over a bright photograph both fades deepen until the
    type reads: the masthead zone to a mean luminance of about 68 (peak about 125), and the zone
    behind the date line and headline (58-80% of the height) to a mean of about 60."""
    W, H = 1200, 1120
    base = _cover(src, W, H, 0.35, 0.5)
    top_h = int(H * 0.44)
    top_stops = [(0, .86), (.45, .72), (.75, .35), (1, 0)]
    for k, shift in ((1.0, 0), (1.1, .04), (1.2, .08), (1.3, .12), (1.45, .16), (1.6, .2)):
        foot_stops = [(0, 0), (.40 - shift, 0), (.62 - shift, .6 + shift), (.84 - shift / 2, .92), (1, 1)]
        im = base.copy()
        top = Image.new("L", (1, H), 0)
        foot = Image.new("L", (1, H), 0)
        for y in range(H):
            if y < top_h:
                top.putpixel((0, y), round(255 * min(1, _ramp(y / top_h, top_stops) * k)))
            foot.putpixel((0, y), round(255 * _ramp(y / (H - 1), foot_stops)))
        im = Image.composite(Image.new("RGB", (W, H), (14, 13, 12)), im, top.resize((W, H)))
        im = Image.composite(Image.new("RGB", (W, H), (20, 20, 20)), im, foot.resize((W, H)))
        mast = im.crop((0, 0, W, int(H * 0.30))).convert("L")
        text = im.crop((0, int(H * 0.58), W, int(H * 0.80))).convert("L")
        if (ImageStat.Stat(mast).mean[0] <= 72 and _p99(mast) <= 130
                and ImageStat.Stat(text).mean[0] <= 60):
            break
    return im


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


def make_images(edition_n, hero_src, story_srcs, base_url):
    """Write the hero and the three story photographs as JPEG; return their public URLs."""
    make_patterns()
    out = EMAIL_DIR / f"edition-{edition_n}"
    out.mkdir(parents=True, exist_ok=True)
    jpg = dict(format="JPEG", quality=74, optimize=True, progressive=True)
    _hero(hero_src).save(out / "hero.jpg", **jpg)
    urls = []
    for k, src in enumerate(story_srcs, 1):
        _cover(src, 528, 660, 0.5, 0.4).save(out / f"{k:02d}.jpg", **jpg)
        urls.append(f"{base_url}/email/edition-{edition_n}/{k:02d}.jpg")
    return f"{base_url}/email/edition-{edition_n}/hero.jpg", urls


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
<title>Aldar CX Time &middot; Edition {n}</title>
<!--[if mso]><noscript><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml></noscript><![endif]-->
<!--[if !mso]><!--><link href="https://fonts.googleapis.com/css2?family=Poppins:wght@200;300;400;600&display=swap" rel="stylesheet"><style>@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@200;300;400;600&display=swap');</style><!--<![endif]-->
<!--[if mso]><style>td,div,a,span,p{{font-family:Arial,Helvetica,sans-serif !important}}</style><![endif]-->
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
.fi{{width:100%!important;max-width:100%!important;height:auto!important}}
.pt16{{padding-top:16px!important}}
.g0{{padding-left:0!important;padding-right:0!important}}
.h1{{font-size:42px!important;line-height:46px!important}}
.phh{{height:96px!important}}
.mast{{font-size:44px!important;line-height:46px!important}}
.outer{{padding:0!important}}
.cta{{padding:18px 24px!important;letter-spacing:2px!important;white-space:normal!important}}
}}
</style>
</head>
"""


def _story(k, s, url, flip):
    """One spread: a 264px photo and a 256px text block (28px gutter inside it). Inline-blocks
    sit side by side in a 520px row and stack, photo first, in anything narrower."""
    img = (f'<a href="{url}" target="_blank"><img src="{e(s["image"])}" width="264" height="330" alt="{e(s["who"])}" '
           f'class="fi" style="display:block;width:264px;max-width:100%;height:auto;border:0;background:#1E1E1E;'
           f'font-family:Arial,sans-serif;font-size:12px;color:{MUTED}"></a>') if s.get("image") else (
           f'<table role="presentation" width="264" cellpadding="0" cellspacing="0" border="0" class="fi" style="width:264px">'
           f'<tr><td height="330" bgcolor="#1E1E1E" style="height:330px;background:#1E1E1E">&nbsp;</td></tr></table>')
    kind = f' &middot; {e(s["kind"])}' if s.get("kind") else ""
    pad = "padding-right:28px" if flip else "padding-left:28px"
    text = (f'<div style="{F}font-size:56px;line-height:56px;{X}color:{RULE};font-weight:200;">{k:02d}</div>{gap(14)}'
            f'<div style="{F}font-size:9px;line-height:13px;{X}color:{MUTED};letter-spacing:2.6px;text-transform:uppercase;">'
            f'{e(s["who"])}{kind}</div>{gap(12)}'
            f'<div style="{F}font-size:24px;line-height:31px;{X}color:{IVORY};font-weight:300;"><a href="{url}" target="_blank" '
            f'style="color:{IVORY};text-decoration:none">{e(s["title"])}</a></div>{gap(12)}'
            f'<div style="{F}font-size:13px;line-height:22px;{X}color:{BODY};">{e(s["what"])}</div>')
    d = ' dir="rtl"' if flip else ""
    top = "0" if k == 1 else "56px"
    return (f'<tr><td class="px" style="padding:{top} 40px 0">'
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%"><tr>'
            f'<td{d} valign="middle" style="font-size:0;text-align:left">'
            f'<!--[if mso]><table role="presentation" width="520" cellpadding="0" cellspacing="0" border="0"{d}><tr>'
            f'<td width="264" valign="middle" dir="ltr"><![endif]-->'
            f'<div class="st" dir="ltr" style="display:inline-block;width:100%;max-width:264px;vertical-align:middle;text-align:left">{img}</div>'
            f'<!--[if mso]></td><td width="256" valign="middle" dir="ltr"><![endif]-->'
            f'<div class="st pt16" dir="ltr" style="display:inline-block;width:100%;max-width:256px;vertical-align:middle;text-align:left">'
            f'<div class="g0" style="{pad}">{text}</div></div>'
            f'<!--[if mso]></td></tr></table><![endif]-->'
            f'</td></tr></table></td></tr>')


def render(d):
    """d: number, date, headline, intro, preheader, editionUrl, heroImage, assetsUrl,
    stories=[{who, kind, title, what, image}] (three)."""
    url = e(d["editionUrl"])
    n = d["number"]
    assets = d["assetsUrl"].rstrip("/")
    hero = e(d.get("heroImage") or "")
    bg_attr = f' background="{hero}"' if hero else ""
    bg_css = f"background:#141414 url({hero}) center top / cover no-repeat" if hero else "background:#141414"
    vml_open = (f'<!--[if mso]><v:rect xmlns:v="urn:schemas-microsoft-com:vml" fill="true" stroke="false" '
                f'style="width:600px;height:560px"><v:fill type="frame" src="{hero}" color="#141414"/>'
                f'<v:textbox inset="0,0,0,0"><![endif]-->') if hero else ""
    vml_close = '<!--[if mso]></v:textbox></v:rect><![endif]-->' if hero else ""
    band = (f'<img src="{assets}/pat-sadu-band.png" width="520" height="28" alt="" class="fi" '
            f'style="display:block;width:520px;max-width:100%;height:auto;border:0;margin:0 auto">')
    stories = "".join(_story(k, s, url, k == 2) for k, s in enumerate(d["stories"], 1))
    btn = "Read the edition"
    body = f"""<body style="margin:0;padding:0;background:#0C0C0C" bgcolor="#0C0C0C">
<div style="display:none;font-size:1px;line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden;mso-hide:all;color:#0C0C0C">{e(d["preheader"])}{PRE_PAD}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#0C0C0C" style="width:100%;background:#0C0C0C"><tr><td class="outer" align="center" style="padding:32px 0 48px">
<!--[if mso]><table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" align="center"><tr><td><![endif]-->
<table role="presentation" class="w" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#141414" style="width:100%;max-width:600px;background:#141414;margin:0 auto">
<tr><td style="padding:0">
{vml_open}
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#141414"{bg_attr} style="width:100%;{bg_css}"><tr><td style="padding:0">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%">
<tr><td class="px" align="center" style="padding:36px 40px 0;text-align:center">
<div style="{F}font-size:13px;line-height:17px;{X}color:{IVORY};letter-spacing:11px;text-transform:uppercase;padding-left:11px;">Aldar</div>{gap(10)}
<div class="mast" style="{F}font-size:54px;line-height:56px;{X}color:{IVORY};font-weight:200;letter-spacing:1px;"><span style="color:{HI};font-weight:400">CX</span>&nbsp;Time</div>{gap(14)}
<table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center" style="margin:0 auto"><tr><td width="56" valign="middle" style="width:56px">{rule(56)}</td><td valign="middle" style="padding:0 10px"><img src="{assets}/pat-sadu-mini-clear.png" width="92" height="25" alt="" style="display:block;width:92px;height:25px;border:0"></td><td width="56" valign="middle" style="width:56px">{rule(56)}</td></tr></table></td></tr>
<tr><td class="phh" height="150" style="height:150px;font-size:0;line-height:0">&nbsp;</td></tr>
<tr><td class="px" style="padding:0 40px 0">{rule(40)}{gap(20)}
<div style="{F}font-size:10px;line-height:14px;{X}color:{BODY};letter-spacing:2.6px;text-transform:uppercase;"><span style="color:{HI}">Edition {n}</span>&nbsp;&nbsp;&middot;&nbsp;&nbsp;{e(d["date"])}</div>{gap(16)}
<div class="h1" style="{F}font-size:56px;line-height:60px;{X}color:{IVORY};letter-spacing:-.8px;font-weight:300;">{two_lines(d["headline"])}</div>{gap(24)}
<div style="{F}font-size:15px;line-height:26px;{X}color:{BODY};">{e(d["intro"])}</div></td></tr>
<tr><td height="8" style="height:8px;font-size:0;line-height:0">&nbsp;</td></tr>
</table></td></tr></table>
{vml_close}
</td></tr>
<tr><td class="px" align="center" style="padding:52px 40px 52px;text-align:center">{band}</td></tr>
{stories}
<tr><td class="px" align="center" style="padding:60px 40px 0;text-align:center">{band}</td></tr>
<tr><td class="px" style="padding:48px 24px 0">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#1C1A16" style="width:100%;background:#1C1A16;background-image:linear-gradient(180deg,#24211B 0%,#16140F 100%);border:1px solid #3A3226;border-collapse:separate;border-radius:4px"><tr><td align="center" class="px" style="padding:56px 48px 54px;text-align:center">
<div style="{F}font-size:10px;line-height:14px;{X}color:{BODY};letter-spacing:3px;text-transform:uppercase;">Edition {n} is live in the Hub</div>{gap(18)}
<div style="{F}font-size:40px;line-height:46px;{X}color:{IVORY};font-weight:300;letter-spacing:-.5px;">Step inside<br>the edition.</div>{gap(18)}
<div style="{F}font-size:15px;line-height:24px;{X}color:{BODY};">Three stories, and a Signature Experience<br class="hs"> to explore for each.</div>{gap(34)}
<!--[if mso]><v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" href="{url}" style="height:60px;v-text-anchor:middle;width:340px" arcsize="50%" stroke="f" fillcolor="{RULE}"><w:anchorlock/><center style="color:{INK};font-family:Arial,sans-serif;font-size:14px;font-weight:bold;letter-spacing:3px">READ THE EDITION &rarr;</center></v:roundrect><![endif]-->
<!--[if !mso]><!--><table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center" style="border-collapse:separate;margin:0 auto"><tr><td align="center" bgcolor="{RULE}" style="background:{RULE};background-image:linear-gradient(180deg,{HI} 0%,#C9A257 100%);border-radius:999px;box-shadow:0 10px 30px rgba(217,180,106,.28)"><a class="cta" href="{url}" target="_blank" style="display:block;padding:21px 46px;{F}font-size:14px;line-height:18px;{X}color:{INK};font-weight:600;letter-spacing:3px;text-transform:uppercase;text-decoration:none;">{btn}&nbsp;&nbsp;&rarr;</a></td></tr></table><!--<![endif]-->
</td></tr></table></td></tr>
<tr><td class="px" style="padding:48px 40px 44px;text-align:center"><img src="{assets}/pat-sadu-mini.png" width="104" height="28" alt="" style="display:block;width:104px;height:28px;border:0;margin:0 auto">{gap(22)}<div style="{F}font-size:9px;line-height:13px;{X}color:{MUTED};letter-spacing:2.4px;text-transform:uppercase;">Curated by Aldar Group Customer Experience</div></td></tr>
</table>
<!--[if mso]></td></tr></table><![endif]-->
</td></tr></table>
</body>
</html>
"""
    return HEAD.format(n=n) + body
