"""Generate illustrative images for customer stories that have no photograph (OpenAI image API).

Usage:
  python3 tools/gen_story_images.py --list
  python3 tools/gen_story_images.py --out DIR cs-05 [cs-06 ...]          # DRAFT, low quality (or --all)
  python3 tools/gen_story_images.py --final --out DIR cs-05 [...]        # FINAL, medium quality
  options and credit rules as tools/gen_benchmark_images.py (estimate first; --yes to go ahead).
  Read docs/image-generation.md first.

Customer stories are real events with real residents, children and colleagues, so the story text is
NOT sent to the image model. Each story has a short scene written here by hand: no names, no brands,
no likeness of anyone, and for illness or loss the gesture (flowers at a door, a gift) rather than the
person who is unwell or grieving. Apply approved images with tools/set_story_image.py --generated.
"""
import json, os, re, sys, time

sys.path.insert(0, os.path.dirname(__file__))
from gen_benchmark_images import generate, parse_args, budget_gate  # generation and credit rules

# Matches the hub's existing customer-story photographs (cs-01, cs-10, cs-31 ...): warm premium
# campaign look, close on the gesture and the reaction, staff in tailored navy/black uniforms.
STYLE = ("Warm, luxurious lifestyle photograph in the style of a premium hospitality brand campaign. Medium close-up: "
         "the people are large in the frame, their faces and the gesture (the gift, card, cake or flowers) sharp in the "
         "foreground, the background softly blurred with warm bokeh. Glowing golden natural light, rich warm tones, "
         "gentle contrast, shot on a full-frame camera at 50mm. Genuine, visible emotion: delight, surprise, laughter, "
         "being touched. Staff wear crisp tailored navy or black uniforms with a small plain gold name badge. Residents "
         "and guests are an international mix (European, Arab, South Asian, East Asian, African), dressed smart-casual. "
         "Elegant interiors with warm wood, marble, soft lamps and fresh flowers. Strictly no text, letters, numbers, "
         "logos, brand marks or signage anywhere (badges, cards and screens are blank or blurred). Do not depict any "
         "real person, and no recognisable landmarks.")

DATA = "data/customer-stories.js"

LINE_SETTING = {
    "Development": "a contemporary residential development in Abu Dhabi: sales lounge, show home or a newly handed-over home",
    "Estates": "a well-kept residential community in Abu Dhabi: villas or apartments, landscaped paths, a community centre",
    "Hospitality": "a refined resort, hotel restaurant or beach club in Abu Dhabi",
    "Retail": "an elegant shopping mall in Abu Dhabi",
    "Education": "a warm, modern British international school in Abu Dhabi",
}

# one name-free scene per story (what the picture shows)
SCENES = {
    "cs-05": "a property sales lounge: a staff member warmly handing a visibly moved customer an envelope with two event tickets, the customer starting to smile",
    "cs-06": "a property sales office after an appointment: a staff member surprising a father with concert tickets, his teenage son beside him delighted",
    "cs-07": "a grand, light-filled national museum gallery: a family of new homeowners enjoying their complimentary visit, the father pointing out an artefact to his son",
    "cs-09": "a sunlit living room: a smiling woman, now well, recording a thank-you video message on her phone, a get-well bouquet from the community team on the table beside her",
    "cs-13": "a newly married couple in their living room opening a gift box to find a stone photo frame, delighted; the frame's picture is soft and unrecognisable",
    "cs-14": "a couple arriving at an elegant restaurant table set for a surprise anniversary dinner, candles, a small wrapped keepsake on the table",
    "cs-15": "a concierge at a resident's front door presenting a festive red-and-gold Chinese New Year cake to a delighted East Asian family",
    "cs-16": "an almost empty new home on moving week, boxes on the floor: a family sitting on the floor sharing a delivered meal, laughing",
    "cs-17": "a sunny community street in the late afternoon: neighbours and children gathered around a pastel ice-cream truck, cones in hand",
    "cs-18": "a shaded villa garden: two community team members chatting warmly over tea with an older resident relaxing in a garden chair, recovering well, no medical equipment",
    "cs-19": "a concierge handing a parent a beautifully hand-wrapped first-birthday gift basket with soft baby-friendly items, the baby in the parent's arms",
    "cs-20": "an apartment doorway: a team member crouching to hand a small child a bag of sweets, the child's face lighting up, a parent smiling behind",
    "cs-21": "a close-up still life on a kitchen counter in soft morning light: a care package with a flask of soup, tea, a jar of honey, a folded soft blanket and a handwritten card (text unreadable), a hand placing the last item",
    "cs-23": "a resident's front door: a concierge delivering a bouquet of flowers and a box of chocolates to an older resident standing with a walker, both smiling",
    "cs-24": "a villa garden at golden hour: two team members presenting a resident with a thoughtful sympathy gift, a framed paw-print keepsake and white flowers, quiet and respectful",
    "cs-25": "a couple back from a trip, suitcases at the door, opening a surprise gift box with a stone photo frame, their grown children smiling behind them",
    "cs-26": "an intimate waterfront Italian restaurant at dusk: a couple at a candlelit table being handed a personalised invitation card by a host",
    "cs-27": "a community promenade at sunrise: a triathlete in a cycling kit with a road bike, being cheered by two community team members",
    "cs-28": "a children's birthday party in a bright community centre: a five-year-old boy receiving a wrapped gift from a team member, balloons and friends around",
    "cs-29": "a sunlit living room: a resident recovering at home happily arranging fresh flowers into elegant vases on a table, a concierge having just delivered them",
    "cs-30": "a couple in their home surprised by a small anniversary set-up: flowers, a cake and a wrapped keepsake on the dining table, a concierge at the door",
    "cs-34": "a hotel restaurant kitchen: a chef in whites guiding a female guest step by step as she prepares a shaved cauliflower salad, both laughing",
    "cs-35": "a ramen restaurant at a marina in the evening: a hostess bringing a Japanese cheesecake with a candle to a family's table, the young daughter beaming",
    "cs-36": "a beach club arrival desk: hand-painted seashell keychains laid out on a wooden tray, a staff member offering one to an arriving guest, the sea behind",
    "cs-39": "a shopping mall exit leading to the car park: a hostess calmly walking hand in hand with a male guest who uses a white cane, guiding him to his car",
    "cs-41": "a teacher in a bright school office smiling as she talks on the phone, sharing good news, a sunny classroom visible through the glass",
    "cs-42": "a school reception: a parent relations colleague sitting with an anxious mother on a sofa, reassuring her warmly over a cup of tea",
    "cs-43": "a bright indoor school pool: a smiling swimming teacher kneeling at the poolside giving a high-five to a young girl in a modest long-sleeved swimsuit and swim cap",
    "cs-44": "early morning in a warm family kitchen: a mother at the table reading a reassuring reply on her phone, relief and a smile on her face; beside her, her 15-year-old son in a casual school polo shirt zipping up his backpack, glancing at her. Only these two people in the scene, no other adults, nobody in a suit or tie",
    "cs-45": "a nursery classroom doorway: a kind teacher kneeling to welcome a shy little girl holding her mother's hand, the girl starting to smile",
}


def stories():
    src = open(DATA, encoding="utf-8").read()
    d = json.loads(re.search(r"window\.CS_DATA\s*=\s*(\{.*\})\s*;?\s*$", src, re.S).group(1))
    try: gen = json.load(open("data/generated-images.json", encoding="utf-8")).get("stories", {})
    except FileNotFoundError: gen = {}
    return [s for s in d["stories"] if not s.get("hidden") and (not s.get("photo") or s["id"] in gen)]


def prompt_for(s):
    scene = SCENES[s["id"]]
    return (f"{STYLE}\n\nSetting: {LINE_SETTING.get(s['line'], 'a premium setting in Abu Dhabi')}.\nScene: {scene}.\n"
            "The photograph fills the whole frame edge to edge: no white or blank areas, fades, borders or empty bands.")


def main(argv):
    opt, flags, ids = parse_args(argv)
    recs = stories()
    missing_scene = [s["id"] for s in recs if s["id"] not in SCENES]
    if "--list" in flags:
        for s in recs: print(s["id"], "|", s["line"], "|", s["title"], "" if s["id"] in SCENES else "(no scene yet)")
        print(len(recs), "stories without a photo (or with a generated one)"); return
    pick = recs if "--all" in flags else [s for s in recs if s["id"] in ids]
    assert not set(ids) - {s["id"] for s in pick}, f"unknown or already photographed: {sorted(set(ids) - {s['id'] for s in pick})}"
    assert all(s["id"] in SCENES for s in pick), f"write a scene first: {missing_scene}"
    assert opt["--out"], "--out DIR is required"
    os.makedirs(opt["--out"], exist_ok=True)
    pj = os.path.join(opt["--out"], "prompts.json"); log = json.load(open(pj)) if os.path.exists(pj) else {}
    budget_gate(sum(not os.path.exists(os.path.join(opt["--out"], s["id"] + ".png")) for s in pick), opt, flags)
    for s in pick:
        p = prompt_for(s); dest = os.path.join(opt["--out"], s["id"] + ".png")
        if "--dry" in flags: print("---", s["id"], "\n" + p); continue
        if os.path.exists(dest): print("skip (exists)", s["id"]); continue
        t = time.time(); png = generate(p, opt["--model"], opt["--quality"], opt["--size"])
        open(dest, "wb").write(png)
        log[s["id"]] = {"prompt": p, "model": opt["--model"], "quality": opt["--quality"], "size": opt["--size"], "title": s["title"]}
        json.dump(log, open(pj, "w"), indent=1)
        print(f"{s['id']}: {len(png) // 1024} KB in {time.time() - t:.0f}s")


if __name__ == "__main__":
    main(sys.argv[1:])
