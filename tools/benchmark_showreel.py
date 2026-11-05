"""The Benchmark showreel only shows photos good enough to fill it (data/benchmark-showreel.json).

reel_ok_js(html) returns "window.__BM_REEL_OK=[ids];" for the <head> feature script (apply_features.py):
the benchmarks whose photo is at least min_width wide (read from the WebP/PNG/JPEG header, no
image library needed at build time) and not on the exclude list. The gallery's showreel reads it.
"""
import base64, gzip, json, os, re, struct

CONF = "data/benchmark-showreel.json"


def _width(path):
    try:
        with open(path, "rb") as f: b = f.read(64 * 1024)
    except OSError: return 0
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
        c = b[12:16]
        if c == b"VP8 ": return struct.unpack("<H", b[26:28])[0] & 0x3FFF
        if c == b"VP8L": return 1 + (((b[22] & 0x3F) << 8) | b[21])
        if c == b"VP8X": return 1 + int.from_bytes(b[24:27], "little")
    if b[:8] == b"\x89PNG\r\n\x1a\n": return struct.unpack(">I", b[16:20])[0]
    if b[:2] == b"\xff\xd8":
        i = 2
        while i < len(b) - 9:
            if b[i] != 0xFF: i += 1; continue
            m = b[i + 1]
            if m in (0xC0, 0xC1, 0xC2): return struct.unpack(">H", b[i + 7:i + 9])[0]
            i += 2 + struct.unpack(">H", b[i + 2:i + 4])[0]
    return 0


def reel_ok_js(html):
    conf = json.load(open(CONF))
    minw, excl = int(conf.get("min_width", 1400)), set(conf.get("exclude", []))
    man = json.loads(re.search(r'<script type="__bundler/manifest">\s*(\{.*?\})\s*</script>', html, re.S).group(1))
    imgs = {}
    for e in man.values():
        if "javascript" not in e.get("mime", ""): continue
        raw = base64.b64decode(e["data"]); s = (gzip.decompress(raw) if e.get("compressed") else raw).decode("utf-8", "ignore")
        if re.match(r"\s*window\.BM_IMAGES_[A-D]\s*=", s): imgs.update(dict(re.findall(r'"([^"]+)"\s*:\s*"(/img/[^"]+)"', s)))
    ok = sorted(k for k, u in imgs.items() if k not in excl and _width(u.lstrip("/")) >= minw)
    return "window.__BM_REEL_OK=" + json.dumps(ok, separators=(",", ":")) + ";"
