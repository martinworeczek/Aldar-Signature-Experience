"""Hero photos: download the source's own editorial image (og:image, episode artwork or the
official video poster), crop to 16:9, encode WebP under the size budget, and store it in img/
by content hash. The source's file is never hotlinked. Missing or too-small images give None,
and the card falls back to its tag gradient."""
import hashlib, io, time
from pathlib import Path

import requests

from PIL import Image, ImageOps

from .store import ROOT


def process(raw_bytes, cfg):
    im = Image.open(io.BytesIO(raw_bytes))
    im = ImageOps.exif_transpose(im).convert("RGB")
    w, h = im.size
    if w < cfg["min_width"]:
        raise ValueError(f"image too small ({w}x{h})")
    target = cfg["aspect"]
    if w / h > target:  # too wide: trim the sides
        nw = int(h * target)
        im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    elif w / h < target:  # too tall: keep the upper-middle band, where subjects usually sit
        nh = int(w / target)
        top = max(0, int((h - nh) * 0.35))
        im = im.crop((0, top, w, top + nh))
    if max(im.size) > cfg["max_long_edge"]:
        im.thumbnail((cfg["max_long_edge"], cfg["max_long_edge"]), Image.LANCZOS)
    for q in (80, 72, 64, 56, 48):
        buf = io.BytesIO()
        im.save(buf, "WEBP", quality=q, method=6)
        if buf.tell() <= cfg["max_kb"] * 1024:
            return buf.getvalue(), im.size
    raise ValueError("could not compress under the size budget")


def fetch_and_store(url, fetcher, cfg):
    """Returns ('/img/<hash>.webp', newly_written) - the file is written under the repo's img/ - or raises."""
    if not url:
        raise ValueError("no image offered by the source")
    r = _get_patiently(url, fetcher)
    data, size = process(r.content, cfg)
    ref = f"/img/{hashlib.sha1(data).hexdigest()[:16]}.webp"
    path = ROOT / ref.lstrip("/")
    if path.exists():
        return ref, False
    path.write_bytes(data)
    return ref, True


# Image hosts are often slower than the article pages: Edition 3 lost the Lark Hotels photo to a
# single 25s read timeout. Network failures (timeouts, dropped connections, 5xx) get three tries
# with longer timeouts; a 4xx or an unusable image is final.
ATTEMPTS = ((None, 0), (45, 4), (75, 10))  # (timeout seconds, pause before the try); None = fetcher default


def _get_patiently(url, fetcher):
    last = None
    for timeout, pause in ATTEMPTS:
        if pause:
            time.sleep(pause)
        try:
            kw = {"timeout": timeout} if timeout else {}
            return fetcher.get(url, check_robots=False, **kw)
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code < 500:
                raise
            last = e
        except (requests.Timeout, requests.ConnectionError) as e:
            last = e
    raise last
