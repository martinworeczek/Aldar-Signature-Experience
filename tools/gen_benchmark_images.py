"""Generate illustrative images for benchmarks that have no photograph (OpenAI image API).

Usage:
  python3 tools/gen_benchmark_images.py --list                 # the benchmarks without an image
  python3 tools/gen_benchmark_images.py --out DIR id [id ...]  # generate those (or --all)
  options: --model gpt-image-2  --quality high|medium|low  --size 1536x1024  --dry (print prompts only)

The API key is never read here: requests go to api.openai.com through the session's network proxy,
which adds the key (saved on the Claude Code environment). Run outside that environment, set
OPENAI_API_KEY and the script sends it itself.

Images are written as DIR/<id>.png with DIR/prompts.json (id -> prompt, model, quality). Nothing is
added to the hub here: review them first, then apply the approved ones with
  python3 tools/set_benchmark_image.py --generated <id>=DIR/<id>.png ...
which also records them in data/generated-images.json (the hub labels them "Illustrative image").

Prompts describe the idea, never the organisation: no brand names, logos, signage or real people,
so a generated picture can't pass for a photograph of a real school or company.
"""
import base64, json, os, sys, time, urllib.request, urllib.error

DATASET = "netlify/functions/_data/mcp-dataset.json"

STYLE = ("Editorial documentary photograph, shot on a full-frame camera with a 35mm lens, natural soft light with "
         "warm golden tones, shallow depth of field, an authentic candid moment, premium and calm atmosphere, "
         "cinematic colour grade, landscape composition with the subject slightly off-centre. People are of diverse "
         "backgrounds, including Gulf Arab and expatriate families where it fits, dressed in contemporary modest "
         "clothing. Strictly no text, letters, words, numbers, logos, brand marks, signage, crests or watermarks "
         "anywhere in the image; any screens, papers or signs are blurred or turned away. Do not depict any specific "
         "real school, company, building or real person.")

SETTING = {
    "Education": "inside a modern international school campus",
    "Education technology": "a student or parent at home or in a modern school, using a laptop or tablet",
    "Food & beverage": "an elegant fine-dining district at dusk",
    "Retail": "a contemporary retail setting",
    "Healthcare": "a calm, modern healthcare setting",
    "Transportation": "a modern city street",
    "Real estate": "a refined customer service centre of a property developer",
    "Technology": "a bright, modern workplace",
    "Online marketplace": "a person working from a bright home office",
}

MOMENT = {"pre": "before joining (discovery, visits, applying)", "onb": "the first days (arrival and onboarding)",
          "emp": "everyday life", "exit": "the time of leaving or graduating", "after": "staying connected afterwards"}


def records():
    d = json.load(open(DATASET, encoding="utf-8"))
    return [b for b in d["benchmarks"] if not b.get("image_url")]


def prompt_for(b):
    setting = SETTING.get(b.get("industry"), "a contemporary, premium setting")
    return (f"{STYLE}\n\nScene: {setting}, during {MOMENT.get(b.get('moment'), 'everyday life')}. "
            f"It illustrates this idea: \"{b['title']}\" - {b.get('summary') or ''} "
            f"{(b.get('lead') or '')[:400]}\n"
            "Show the human moment of this idea, not a diagram. Leave calm space at the bottom of the frame for a caption.")


def generate(prompt, model, quality, size):
    body = json.dumps({"model": model, "prompt": prompt, "size": size, "quality": quality, "n": 1}).encode()
    key = os.environ.get("OPENAI_API_KEY") or "proxy-injected"  # the proxy replaces the header
    req = urllib.request.Request("https://api.openai.com/v1/images/generations", data=body, method="POST",
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                j = json.loads(r.read())
            return base64.b64decode(j["data"][0]["b64_json"])
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", "ignore")[:400]
            if "insufficient_quota" in msg or "billing" in msg:  # no credits: retrying can't help
                raise SystemExit("OpenAI: the account has no API credits. Add credits at "
                                 "https://platform.openai.com/settings/organization/billing/ and run again.")
            if e.code in (429, 500, 502, 503) and attempt < 3:
                time.sleep(10 * (attempt + 1)); continue
            raise SystemExit(f"OpenAI error {e.code}: {msg}")


def main(argv):
    args = list(argv); opt = {"--model": "gpt-image-2", "--quality": "high", "--size": "1536x1024", "--out": None}
    flags = {a for a in args if a in ("--list", "--all", "--dry")}
    for k in list(opt):
        if k in args: i = args.index(k); opt[k] = args[i + 1]; del args[i:i + 2]
    ids = [a for a in args if not a.startswith("--")]
    recs = records()
    if "--list" in flags:
        for b in recs: print(b["id"], "|", b["brand"], "|", b["title"])
        print(len(recs), "benchmarks without an image"); return
    pick = recs if "--all" in flags else [b for b in recs if b["id"] in ids]
    missing = set(ids) - {b["id"] for b in pick}
    assert not missing, f"not a benchmark without an image: {sorted(missing)}"
    assert opt["--out"], "--out DIR is required"
    os.makedirs(opt["--out"], exist_ok=True)
    pj = os.path.join(opt["--out"], "prompts.json")
    log = json.load(open(pj)) if os.path.exists(pj) else {}
    for b in pick:
        p = prompt_for(b); dest = os.path.join(opt["--out"], b["id"] + ".png")
        if "--dry" in flags: print("---", b["id"], "\n" + p); continue
        if os.path.exists(dest): print("skip (exists)", b["id"]); continue
        t = time.time(); png = generate(p, opt["--model"], opt["--quality"], opt["--size"])
        open(dest, "wb").write(png)
        log[b["id"]] = {"prompt": p, "model": opt["--model"], "quality": opt["--quality"], "size": opt["--size"], "title": b["title"], "brand": b["brand"]}
        json.dump(log, open(pj, "w"), indent=1)
        print(f"{b['id']}: {len(png) // 1024} KB in {time.time() - t:.0f}s")


if __name__ == "__main__":
    main(sys.argv[1:])
