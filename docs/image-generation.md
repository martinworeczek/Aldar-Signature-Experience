# Generating images for the hub (OpenAI): credit rules

Group CX pays for every image from prepaid OpenAI API credit. The first full run (November 2026: 71
benchmarks, 30 customer stories) used about 165 high-quality images for about 100 final pictures:
roughly 40% were thrown away, almost all because of avoidable mistakes. These rules exist so that
doesn't happen again. Follow them every time you are asked to generate images.

## The rules

1. **Study what is already on the hub first.** Before writing a prompt, look at the existing
   photographs of the same kind (story photos, benchmark photos, experience photos) and describe their
   style in the generator's `STYLE`. The 30 customer stories were all generated twice because this
   was skipped.
2. **Draft at low quality, finish at medium.** Generate the whole batch as low-quality drafts, review
   them, fix prompts, and only render the approved ones with `--final` (medium). Use
   `--quality high` only for large hero images (showreel slides, story banners): on cards
   (about 200 to 500px wide) medium and high look the same.
3. **Plan variety before generating.** Write a distinct scene for each item up front. Similar items
   (admissions, doorstep deliveries, someone at a laptop) all come out as the same picture otherwise.
4. **One image per item.** Make alternatives only when the user asks for them.
5. **Estimate, then ask.** Every run prints how many images it will make and a rough cost, and does
   nothing without `--yes`. Show the user the estimate (drafts and finals) and wait for their OK
   before running with `--yes`. If the account runs out of credit the run stops; tell the user.
6. **Check drafts automatically and by eye.** `tools/image_contact_sheet.py` puts a folder of images
   on one sheet (cropped as the hub shows them) and warns about blank bands. Look at every image for
   text, logos, real landmarks, odd people (a stranger in a suit in a family kitchen) and repetition.

## Prompt lessons (already in the generators)

- Never ask for "space for a caption": the model adds a white wash along the bottom.
- Ban recognisable landmarks and skylines explicitly (the first fine-dining image showed the Burj Khalifa).
- Ask for the moment itself, never photographs, posters or screens of it.
- Give off-campus or away-from-home items their own setting (expeditions, exchanges, airports).
- Describe exactly who is in the scene and exclude everyone else when it matters.
- Customer stories are real events: never send the story text, names or brands to the model. Write a
  short name-free scene; for illness or loss show the gesture, not the person who is unwell or grieving.

## Workflow

```
# 1. drafts (low): estimate first, then --yes once the user agrees
python3 tools/gen_story_images.py --out DRAFTS cs-05 cs-06 ...
python3 tools/gen_story_images.py --out DRAFTS cs-05 cs-06 ... --yes
python3 tools/image_contact_sheet.py DRAFTS drafts.jpg --band 16:7     # stories; 3:2 for benchmarks
# 2. fix prompts / scenes, redraft only what failed, review with the user
# 3. finals (medium) for the approved ones only
python3 tools/gen_story_images.py --final --out FINAL cs-05 cs-06 ... --yes
# 4. apply, rebuild, check in the browser, deploy
python3 tools/set_story_image.py --generated cs-05=FINAL/cs-05.png@"center 40%" ...
python3 tools/set_benchmark_image.py --generated <id>=FINAL/<id>.png ...
```

To run many images in parallel (each takes about 80 seconds), give every id its own output folder,
e.g. `xargs -P 8 -I{} sh -c 'python3 tools/gen_story_images.py --out "DIR/{}" "{}" --yes'`.

## How it works

- The OpenAI key is saved on the Claude Code environment "aldar-signature-experience" and added by its
  network proxy; the scripts never read it. Generation uses background mode (the job is queued and
  polled), because high and medium renders take longer than the proxy keeps a request open.
- `data/generated-images.json` lists every generated image. The hub labels them
  "Illustrative image · AI" and `/mcp` marks benchmarks `image_is_illustrative`. Setting a real
  photograph with the same tools (without `--generated`) takes the item off the list.
- The generators only ever replace images they generated themselves, never a real photograph.
- Real spend: platform.openai.com, Settings, Usage. The script's estimate is approximate.
