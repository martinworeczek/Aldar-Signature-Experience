"""Edition announcement EDM, design "2c Photo-ready" (docs/edm/README.md).

render(data) returns send-ready email HTML matching the reference file exactly: nested
presentation tables, inline styles, Outlook conditionals, hidden preheader. Photographs are
real <img> tags when a hosted https URL is given, otherwise the design's placeholder cells.
make_images() writes the JPEG crops the email needs (hero 1200x600, thumbs 336x252, cover crop
40% from the top) into sites/cx-time/email/edition-N/, so they are hosted with the CX Time site.
"""
import html
from pathlib import Path

from PIL import Image, ImageOps

from .store import ROOT

PRE_PAD = "&#847;&zwnj;&nbsp;" * 70
S = "font-family:Georgia,'Times New Roman',Times,serif;"
A = "font-family:Arial,Helvetica,sans-serif;"
X = "mso-line-height-rule:exactly;"


def e(s):
    return html.escape(s or "", quote=True).replace("&#x27;", "&rsquo;").replace("'", "&rsquo;")


def gap(n):
    return f'<div style="height:{n}px;line-height:{n}px;font-size:0;{X}">&nbsp;</div>'


def _cover(src, w, h, top=0.40):
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    sw, sh = im.size
    scale = max(w / sw, h / sh)
    im = im.resize((round(sw * scale), round(sh * scale)), Image.LANCZOS)
    left = (im.width - w) // 2
    y = int((im.height - h) * top)
    return im.crop((left, y, left + w, y + h))


def make_images(edition_n, hero_src, thumb_srcs, base_url):
    """Write hero + thumbnails as JPEG; return their public URLs."""
    out = ROOT / "sites" / "cx-time" / "email" / f"edition-{edition_n}"
    out.mkdir(parents=True, exist_ok=True)
    _cover(hero_src, 1200, 600).save(out / "hero.jpg", "JPEG", quality=82, optimize=True, progressive=True)
    urls = []
    for k, src in enumerate(thumb_srcs, 1):
        _cover(src, 336, 252).save(out / f"{k:02d}.jpg", "JPEG", quality=82, optimize=True, progressive=True)
        urls.append(f"{base_url}/email/edition-{edition_n}/{k:02d}.jpg")
    return f"{base_url}/email/edition-{edition_n}/hero.jpg", urls


def _slot(label, size, w, h, radius, cls_h=""):
    r = f"border-radius:{radius}px;" if radius else ""
    hc = f' class="{cls_h}"' if cls_h else ""
    return (f'<table role="presentation" width="{w}" cellpadding="0" cellspacing="0" border="0" class="ph" '
            f'style="width:{w}px;border-collapse:separate"><tr><td{hc} align="center" valign="middle" height="{h}" '
            f'bgcolor="#E4DCCD" style="height:{h}px;background:#E4DCCD;{r}padding:0 12px">'
            f'<div style="{A}font-size:9px;line-height:13px;{X}color:#6B6455;font-weight:bold;letter-spacing:1.4px;'
            f'text-transform:uppercase;">{label}</div>{gap(4)}'
            f'<div style="{A}font-size:10px;line-height:14px;{X}color:#6B6455;">{size} &middot; swap before sending</div>'
            f'</td></tr></table>')


def render(d):
    """d: number, date, headline, intro, preheader, editionUrl, heroImage, unsubscribeUrl,
    preferencesUrl, stories=[{who,title,what,forAldar,image}] (three)."""
    url = e(d["editionUrl"])
    if d.get("heroImage"):
        hero = (f'<a href="{url}" target="_blank"><img src="{e(d["heroImage"])}" width="600" height="300" '
                f'alt="Aldar CX Time, Edition {d["number"]}" class="fi" '
                f'style="display:block;width:600px;max-width:100%;height:auto;border:0"></a>')
    else:
        hero = _slot("Edition hero image", "1200 &times; 600", 600, 300, 0, "phh")
    rows = []
    stories = d["stories"]
    for k, s in enumerate(stories, 1):
        border = "border-bottom:1px solid #E2DCCF" if k < len(stories) else ""
        if s.get("image"):
            thumb = (f'<a href="{url}" target="_blank"><img src="{e(s["image"])}" width="168" height="126" '
                     f'alt="{e(s["who"])}" class="ph" style="display:block;width:168px;max-width:100%;height:auto;'
                     f'border:0;border-radius:6px"></a>')
        else:
            thumb = _slot(f'{e(s["who"])} photo', "336 &times; 252", 168, 126, 6)
        rows.append(
            f'<tr><td class="px" style="padding:0 40px;"><table role="presentation" width="100%" cellpadding="0" '
            f'cellspacing="0" border="0" style="width:100%;{border}"><tr>\n'
            f'<td class="st pb0" width="168" valign="top" style="width:168px;padding:24px 0">{thumb}</td>\n'
            f'<td class="hs" width="20" style="width:20px;font-size:0">&nbsp;</td>\n'
            f'<td class="st pt12" valign="top" style="padding:22px 0 24px">'
            f'<div style="{A}font-size:10px;line-height:14px;{X}color:#8A6524;font-weight:bold;letter-spacing:1.4px;'
            f'text-transform:uppercase;">{k:02d} &middot; {e(s["who"])}</div>{gap(7)}\n'
            f'<div style="{S}font-size:19px;line-height:25px;{X}color:#1B2730;"><a href="{url}" target="_blank" '
            f'style="color:#1B2730;text-decoration:none">{e(s["title"])}</a></div>{gap(8)}\n'
            f'<div style="{A}font-size:13px;line-height:20px;{X}color:#44505A;">{e(s["what"])}</div>{gap(9)}\n'
            f'<div style="{A}font-size:13px;line-height:19px;{X}color:#2F5A43;"><strong>For Aldar &middot;</strong> '
            f'{e(s["forAldar"])}</div></td></tr></table></td></tr>')
    unsub = e(d.get("unsubscribeUrl") or "mailto:groupcx@aldar.com?subject=Unsubscribe%20from%20Aldar%20CX%20Time")
    prefs = e(d.get("preferencesUrl") or "mailto:groupcx@aldar.com?subject=Aldar%20CX%20Time%20preferences")
    return f"""<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta name="x-apple-disable-message-reformatting">
<meta name="format-detection" content="telephone=no,address=no,email=no,date=no">
<meta name="color-scheme" content="light dark">
<meta name="supported-color-schemes" content="light dark">
<title>Aldar CX Time &middot; Edition {d["number"]}</title>
<!--[if mso]><noscript><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml></noscript><![endif]-->
<style>
body{{margin:0!important;padding:0!important;width:100%!important;-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%}}
table{{border-collapse:collapse;mso-table-lspace:0pt;mso-table-rspace:0pt}}
img{{border:0;outline:none;text-decoration:none;-ms-interpolation-mode:bicubic}}
a[x-apple-data-detectors]{{color:inherit!important;text-decoration:none!important}}
@media screen and (max-width:620px){{
.w{{width:100%!important;max-width:100%!important}}
.st{{display:block!important;width:100%!important;max-width:100%!important;box-sizing:border-box}}
.px{{padding-left:22px!important;padding-right:22px!important}}
.hs{{display:none!important}}
.fi{{width:100%!important;max-width:100%!important;height:auto!important}}
.gv{{display:block!important;width:100%!important;height:22px!important;line-height:22px!important}}
.pb0{{padding-bottom:0!important}}
.pt12{{padding-top:12px!important}}
.h1{{font-size:36px!important;line-height:40px!important}}
.tile{{height:auto!important}}
.ph{{width:100%!important;max-width:100%!important}}
.phh{{height:190px!important}}
}}
</style>
</head>
<body style="margin:0;padding:0;background:#E6E1D7" bgcolor="#E6E1D7">
<div style="display:none;font-size:1px;line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden;mso-hide:all;color:#E6E1D7">{e(d["preheader"])}{PRE_PAD}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#E6E1D7" style="width:100%;background:#E6E1D7"><tr><td align="center" style="padding:28px 0 40px">
<!--[if mso]><table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" align="center"><tr><td><![endif]-->
<table role="presentation" class="w" width="600" cellpadding="0" cellspacing="0" border="0" bgcolor="#FDFCF8" style="width:600px;max-width:600px;background:#FDFCF8;margin:0 auto">

<tr><td class="px" style="padding:28px 40px 18px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;"><tr><td valign="bottom" style="{S}font-size:22px;line-height:26px;{X}color:#1B2730;">Aldar CX Time</td><td align="right" valign="bottom" style="{A}font-size:10px;line-height:14px;{X}color:#8A6524;font-weight:bold;letter-spacing:1.8px;text-transform:uppercase;">Edition {d["number"]} &middot; {e(d["date"])}</td></tr></table></td></tr>
<tr><td style="padding:0">{hero}</td></tr>
<tr><td class="px" style="padding:32px 40px 4px;"><div class="h1" style="{S}font-size:38px;line-height:44px;{X}color:#1B2730;">{e(d["headline"])}</div>{gap(14)}<div style="{A}font-size:15px;line-height:24px;{X}color:#44505A;">{e(d["intro"])}</div></td></tr>
{"".join(rows)}
<tr><td class="px" style="padding:30px 40px 0;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#1B2730" style="width:100%;background:#1B2730;border-collapse:separate;border-radius:8px"><tr><td class="st" valign="middle" style="padding:26px 10px 26px 28px;{S}font-size:17px;line-height:25px;{X}color:#F6F1E6;">The full stories, and a Signature Experience to explore for each.</td><td class="st" valign="middle" align="right" style="padding:26px 28px 26px 10px"><table role="presentation" cellpadding="0" cellspacing="0" border="0" style="border-collapse:separate"><tr><td align="center" bgcolor="#E8B96A" style="background:#E8B96A;border-radius:999px;padding:12px 22px"><a href="{url}" target="_blank" style="display:block;{A}font-size:13px;line-height:16px;{X}color:#1B2730;font-weight:bold;text-decoration:none;white-space:nowrap;">Read the edition &rarr;</a></td></tr></table></td></tr></table></td></tr>
<tr><td class="px" style="padding:40px 40px 32px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;"><tr><td height="1" bgcolor="#E2DCCF" style="height:1px;line-height:1px;font-size:0;background:#E2DCCF">&nbsp;</td></tr></table>{gap(22)}
<div style="{A}font-size:11px;line-height:18px;{X}color:#66707A;">Aldar CX Time is curated by Aldar Group Customer Experience for colleagues across every business line.</div>{gap(8)}
<div style="{A}font-size:11px;line-height:18px;{X}color:#66707A;">Aldar Properties PJSC &middot; Aldar HQ, Al Raha Beach &middot; P.O. Box 51133 &middot; Abu Dhabi, UAE</div>{gap(10)}
<div style="{A}font-size:11px;line-height:18px;{X}color:#66707A;"><a href="{unsub}" style="color:#1B2730;text-decoration:underline">Unsubscribe</a>&nbsp;&nbsp;&middot;&nbsp;&nbsp;<a href="{prefs}" style="color:#1B2730;text-decoration:underline">Manage preferences</a></div></td></tr>
</table>
<!--[if mso]></td></tr></table><![endif]-->
</td></tr></table>
</body>
</html>
"""
