"""Step 1 - Harvest. Allow-list only: read each source's own feed, keep the last 7 days,
screen on metadata, then fetch the full text only for the shortlist.

Nothing here writes source text to disk. `sourceText` lives in memory for the run and is
handed to enrichment; only the URL, title and screening decision go into the run log.
"""
import email.utils, hashlib, html, json, re, time, urllib.parse, urllib.robotparser
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

import requests
from bs4 import BeautifulSoup

from .store import canon_url

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
    "media": "http://search.yahoo.com/mrss/",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "dc": "http://purl.org/dc/elements/1.1/",
    "podcast": "https://podcastindex.org/namespace/1.0",
}


class Fetcher:
    """Polite HTTP: one user agent, robots.txt respected, a gap between hits to the same host."""

    def __init__(self, cfg):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = cfg["user_agent"]
        self.timeout, self.delay = cfg["timeout"], cfg["delay_seconds"]
        self.last, self.robots = {}, {}

    def allowed(self, url):
        p = urllib.parse.urlsplit(url)
        base = f"{p.scheme}://{p.netloc}"
        if base not in self.robots:
            rp = urllib.robotparser.RobotFileParser()
            try:
                r = self.s.get(base + "/robots.txt", timeout=self.timeout)
                rp.parse(r.text.splitlines() if r.status_code == 200 else [])
            except requests.RequestException:
                rp.parse([])
            self.robots[base] = rp
        return self.robots[base].can_fetch(self.s.headers["User-Agent"], url)

    def get(self, url, check_robots=True, **kw):
        if check_robots and not self.allowed(url):
            raise PermissionError(f"robots.txt disallows {url}")
        host = urllib.parse.urlsplit(url).netloc
        wait = self.delay - (time.time() - self.last.get(host, 0))
        if wait > 0:
            time.sleep(wait)
        self.last[host] = time.time()
        r = self.s.get(url, timeout=self.timeout, **kw)
        r.raise_for_status()
        return r


# ---------- dates & text helpers ----------
def parse_date(s):
    if not s:
        return None
    s = s.strip()
    try:
        d = email.utils.parsedate_to_datetime(s)
    except (TypeError, ValueError):
        try:
            d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def strip_html(s):
    return re.sub(r"\s+", " ", BeautifulSoup(s or "", "lxml").get_text(" ")).strip()


def key_for(url):
    return hashlib.sha1(canon_url(url).encode()).hexdigest()[:8]


def duration_text(raw):
    """itunes:duration ('2280', '38:00', '1:02:10') -> '38 min'."""
    if not raw:
        return ""
    raw = raw.strip()
    if raw.isdigit():
        secs = int(raw)
    else:
        parts = [int(p) for p in raw.split(":") if p.isdigit()]
        secs = 0
        for p in parts:
            secs = secs * 60 + p
    return f"{max(1, round(secs / 60))} min" if secs else ""


# ---------- feeds ----------
def discover_feed(f, site):
    r = f.get(site)
    soup = BeautifulSoup(r.text, "lxml")
    for t in ("application/rss+xml", "application/atom+xml"):
        link = soup.find("link", rel="alternate", type=t)
        if link and link.get("href"):
            return urllib.parse.urljoin(site, link["href"])
    for guess in ("feed/", "rss/", "feed", "rss.xml", "feed.xml"):
        u = urllib.parse.urljoin(site if site.endswith("/") else site + "/", guess)
        try:
            rr = f.get(u)
            if b"<rss" in rr.content[:2000] or b"<feed" in rr.content[:2000]:
                return u
        except Exception:
            continue
    raise LookupError(f"no RSS/Atom feed found on {site}")


def podcast_feed(f, term):
    r = f.get("https://itunes.apple.com/search", check_robots=False,
              params={"term": term, "media": "podcast", "entity": "podcast", "limit": 5})
    res = r.json().get("results", [])
    if not res or not res[0].get("feedUrl"):
        raise LookupError(f"podcast '{term}' not found on Apple Podcasts")
    return res[0]["feedUrl"], res[0].get("collectionViewUrl"), res[0].get("artworkUrl600")


def youtube_feed(f, handle):
    r = f.get(f"https://www.youtube.com/{handle}", check_robots=False)
    m = re.search(r'"(?:externalId|channelId)":"(UC[\w-]{22})"', r.text)
    if not m:
        raise LookupError(f"YouTube channel {handle} not found")
    return f"https://www.youtube.com/feeds/videos.xml?channel_id={m.group(1)}"


def _first(el, *paths):
    """ElementTree elements are falsy when they have no children, so never chain them with `or`."""
    for p in paths:
        x = el.find(p, NS)
        if x is not None:
            return x
    return None


def _t(el, path):
    x = el.find(path, NS)
    return (x.text or "").strip() if x is not None and x.text else ""


def parse_feed(xml_bytes):
    """RSS 2.0 or Atom -> list of plain dicts (metadata only)."""
    root = ET.fromstring(xml_bytes.lstrip())  # some feeds start with a blank line before <?xml
    out = []
    channel_img = ""
    ch = root.find("channel")
    if ch is not None:
        im = ch.find("itunes:image", NS)
        channel_img = im.get("href") if im is not None else _t(ch, "image/url")
        for it in ch.findall("item"):
            enc = it.find("enclosure")
            im = it.find("itunes:image", NS)
            mt = _first(it, "media:thumbnail", "media:content")
            tr = it.find("podcast:transcript", NS)
            out.append({
                "title": strip_html(_t(it, "title")),
                "url": _t(it, "link") or (enc.get("url") if enc is not None else ""),
                "published": _t(it, "pubDate") or _t(it, "dc:date"),
                "excerpt": strip_html(_t(it, "description"))[:600],
                "body": _t(it, "content:encoded") or _t(it, "description"),
                "categories": [c.text for c in it.findall("category") if c.text],
                "duration": _t(it, "itunes:duration"),
                "episode": _t(it, "itunes:episode"),
                "image": (im.get("href") if im is not None else "") or (mt.get("url") if mt is not None else ""),
                "channel_image": channel_img,
                "author": _t(it, "itunes:author") or _t(it, "dc:creator"),
                "transcript": tr.get("url") if tr is not None else None,
                "guid": _t(it, "guid"),
            })
        return out
    for e in root.findall("atom:entry", NS):
        link = _first(e, "atom:link[@rel='alternate']", "atom:link")
        grp = e.find("media:group", NS)
        th = grp.find("media:thumbnail", NS) if grp is not None else None
        out.append({
            "title": strip_html(_t(e, "atom:title")),
            "url": link.get("href") if link is not None else "",
            "published": _t(e, "atom:published") or _t(e, "atom:updated"),
            "excerpt": strip_html((_t(grp, "media:description") if grp is not None else "") or _t(e, "atom:summary"))[:600],
            "body": (_t(grp, "media:description") if grp is not None else "") or _t(e, "atom:content") or _t(e, "atom:summary"),
            "categories": [],
            "duration": "",
            "episode": "",
            "image": th.get("url") if th is not None else "",
            "channel_image": "",
            "author": _t(e, "atom:author/atom:name"),
            "transcript": None,
            "video_id": _t(e, "yt:videoId"),
        })
    return out


def collect_metadata(src, f, run_date, cfg_ed, seen, log):
    """One source -> in-window, unseen items (metadata only). Errors are logged, never raised."""
    status = {"source": src["name"], "format": src["format"], "kind": src["kind"], "ok": False, "found": 0, "inWindow": 0, "new": 0}
    try:
        artwork = show_page = None
        if src["kind"] == "rss":
            feed = src["url"]
            r = f.get(feed)
            if not (b"<rss" in r.content[:3000] or b"<feed" in r.content[:3000] or b"<rdf" in r.content[:3000]):
                feed = discover_feed(f, src["url"])
                r = f.get(feed)
        elif src["kind"] == "podcast":
            feed, show_page, artwork = podcast_feed(f, src["search"])
            r = f.get(feed, check_robots=False)
        else:
            feed = youtube_feed(f, src["handle"])
            r = f.get(feed, check_robots=False)
        status["feed"] = feed
        items = parse_feed(r.content)[: src.get("max_items", 25)]
        status["found"] = len(items)
    except Exception as e:  # a broken source is reported, not fatal
        status["error"] = f"{type(e).__name__}: {e}"[:300]
        return [], status
    status["ok"] = True

    window_start = run_date - timedelta(days=cfg_ed["window_days"])
    oldest = run_date - timedelta(days=cfg_ed["fallback_max_age_days"])
    dated = [(parse_date(i["published"]), i) for i in items if i["url"] and i["title"]]
    dated = [(d, i) for d, i in dated if d and d <= run_date + timedelta(days=1)]
    dated.sort(key=lambda x: x[0], reverse=True)
    fresh = [(d, i) for d, i in dated if d >= window_start]
    status["inWindow"] = len(fresh)
    if not fresh:  # quiet week for this source: offer its newest few, if still recent
        fresh = [(d, i) for d, i in dated if d >= oldest][: cfg_ed["fallback_items"]]
        status["fallback"] = bool(fresh)

    out = []
    for d, i in fresh:
        url = i["url"]
        if re.search(r"\.(mp3|m4a|aac)(\?|$)", url, re.I):  # audio file, not a page: link the show instead
            if not show_page:
                continue
            url = show_page + ("&" if "?" in show_page else "?") + "ep=" + key_for(i["guid"] or i["title"])
        cu = canon_url(url)
        if cu in seen:
            log.append({"key": key_for(url), "url": url, "title": i["title"], "source": src["name"],
                        "stage": "harvest", "decision": "skip", "reason": "already seen in an earlier run or edition"})
            continue
        out.append({
            "key": key_for(url), "sourceUrl": url, "source": src["name"], "sourceShort": src["short"],
            "formatHint": src["format"], "titleRaw": i["title"], "publishedRaw": d.isoformat(),
            "excerpt": i["excerpt"], "categories": i["categories"][:6], "durationRaw": i["duration"],
            "episode": i["episode"], "rawImageUrl": i["image"] or i["channel_image"] or artwork or "",
            "imageCredit": (f"{src['name']} - show artwork" if src["format"] == "listen" and not i["image"] else src["name"]),
            "speakersRaw": [], "transcriptUrl": i.get("transcript"), "videoId": i.get("video_id"),
            "author": i["author"], "_body": i["body"], "_src": src,
        })
    status["new"] = len(out)
    return out, status


# ---------- deep fetch (shortlist only) ----------
def _meta(soup, *names):
    for n in names:
        t = soup.find("meta", attrs={"property": n}) or soup.find("meta", attrs={"name": n})
        if t and t.get("content"):
            return t["content"].strip()
    return ""


def article_text(soup):
    for bad in soup(["script", "style", "nav", "header", "footer", "aside", "form", "noscript", "figure"]):
        bad.decompose()
    def text_of(el):
        paras = [p.get_text(" ", strip=True) for p in el.find_all(["p", "h2", "h3", "li"])]
        return "\n".join(p for p in paras if len(p) > 40 or p.endswith((".", "?", "!")))
    # pages differ: the story may sit in <article>, <main> or a plain div; take whichever
    # container holds the most real prose (a small <article> card must not win)
    options = soup.find_all("article") + soup.find_all("main") + [soup.body or soup]
    return max((text_of(el) for el in options), key=lambda t: len(t.split()), default="")


def deep_fetch(c, f, cfg_fetch):
    """Fill in full text, hero image and media details for one shortlisted candidate."""
    fmt = c["formatHint"]
    if fmt == "read":
        r = f.get(c["sourceUrl"])
        soup = BeautifulSoup(r.text, "lxml")
        c["rawImageUrl"] = _meta(soup, "og:image", "twitter:image") or c["rawImageUrl"]
        c["titleRaw"] = c["titleRaw"] or _meta(soup, "og:title")
        c["author"] = c["author"] or _meta(soup, "author", "article:author")
        text = article_text(soup)
        feed_text = strip_html(c.get("_body", ""))
        if len(feed_text.split()) > len(text.split()):  # many feeds carry the full story
            text = feed_text
        words = len(text.split())
        c["durationRaw"] = str(words)
        c["sourceText"] = text[: cfg_fetch["max_source_chars"]]
        if words < cfg_fetch["min_read_words"]:
            raise ValueError(f"only {words} words of accessible text (paywall or stub)")
    elif fmt == "watch":
        vid = c.get("videoId")
        text = strip_html(c.get("_body", ""))
        try:
            r = f.get(c["sourceUrl"], check_robots=False)
            m = re.search(r'"lengthSeconds":"(\d+)"', r.text)
            if m:
                c["durationRaw"] = m.group(1)
            m = re.search(r'"shortDescription":"(.*?)","', r.text)
            if m and len(m.group(1)) > len(text):
                text = json.loads('"' + m.group(1) + '"')
        except Exception:
            pass
        if vid:
            c["rawImageUrl"] = f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg"
        c["sourceText"] = text[: cfg_fetch["max_source_chars"]]
        if len(text.split()) < 60:
            raise ValueError("video description too thin to summarise faithfully")
    else:  # listen
        text = strip_html(c.get("_body", ""))
        c["sourceText"] = text[: cfg_fetch["max_source_chars"]]
        if len(text.split()) < 80:
            raise ValueError("episode notes too thin to summarise faithfully")
    return c
