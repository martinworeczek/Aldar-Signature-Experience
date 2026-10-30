"""Apply the Aldar CX Time "4a/4b toggle + 5a reader" handoff (docs/cxtime-4a5a-README.md).

The reference build is the same dc component with the new design applied, so it is adopted
whole, keeping this app's own <head> (support script, Poppins link, edition data script) and
its onClick attribute style. The toggle glyph follows the README (▣ Cards). The reader's
"Open in Idea Exchange" uses the host's existing window.__SIG_GO('transfer').
Usage: python3 -I tools/apply_cxtime_4a5a.py <preview template.html>
"""
import base64, gzip, json, re, sys

PAGE = "index.html"
ASSET = "59c00ad5"

def main(preview_path):
    html = open(PAGE, encoding="utf-8").read()
    mm = re.search(r'(<script type="__bundler/manifest">\s*)(\{.*?\})(\s*</script>)', html, re.S)
    man = json.loads(mm.group(2))
    key = next(k for k in man if k.startswith(ASSET))
    e = man[key]
    raw = base64.b64decode(e["data"])
    cur = (gzip.decompress(raw) if e["compressed"] else raw).decode("utf-8")
    assert "layoutCards" not in cur, "4a/5a already applied"
    new = open(preview_path, encoding="utf-8").read()

    # head: this app's own scripts/fonts, then the preview from its component styles onward
    head_end = cur.index("<style>\n.atl a{")
    body_start = new.index("<style>\n.atl a{")
    new = cur[:head_end] + new[body_start:]
    new = new.replace("sc-camel-on-click=", "onClick=")
    new = new.replace("▦ Cards", "▣ Cards")
    assert "Experience Builder" not in new and "Open in Idea Exchange" in new
    raw = new.encode("utf-8")
    e["data"] = base64.b64encode(gzip.compress(raw, 9) if e["compressed"] else raw).decode()
    html = html[:mm.start(2)] + json.dumps(man, separators=(",", ":")) + html[mm.end(2):]

    open(PAGE, "w", encoding="utf-8").write(html)
    print("applied")

if __name__ == "__main__":
    main(sys.argv[1])
