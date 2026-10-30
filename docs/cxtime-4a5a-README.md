# Aldar CX Time — shelves "4a/4b toggle" + article reader "5a Continuous Portrait"

Two linked changes to the Aldar CX Time page, bringing it onto the same visual system as the catalogue card (`card-2a-handoff`) and the experience detail (`detail-3a-handoff`). Poppins only. No data, routing or permission changes.

Reference build: `Aldar Times Live - 4a5a Preview.html` (open in a browser). It renders the real Edition 2 with gradient fallbacks where it cannot reach the shared image loader; in the app the photographs attach.

## Palette and shared pieces
Same tokens as the detail handoff: ground `#0A0A0A`, panel `#161616` + `1px solid rgba(255,255,255,.08)` radius 14, gold `#E8B96A`, white ink with `.88 / .7 / .55 / .5` alphas, rules `rgba(255,255,255,.14)` / `.1`.

Pills: gold pill (`#E8B96A` fill, `#0A1014` text, 10px / 600 / `.14em` uppercase, radius 999, `5px 11px`) for the one "hero" label; dark pill (`rgba(0,0,0,.66)`, `1px solid rgba(255,255,255,.18)`, blur 6px, white 10px / 500 / `.1em` uppercase) for everything else. All pills `white-space:nowrap`.

Photo layers are **style objects** (`backgroundImage: url("…")`), never CSS strings — base64 URLs contain `;`.

## A · Signal of the Week → 2a hero
Replaces the two-column lead card. A `16/7` (min-height 340px) black card, radius 12, photo cover `center 40%`, scrim `linear-gradient(180deg, rgba(0,0,0,.3) 0%, rgba(0,0,0,0) 25%, rgba(0,0,0,0) 40%, rgba(0,0,0,.62) 62%, rgba(0,0,0,.9) 100%)`.
- Top-left: gold pill "✦ Signal of the week", then dark pills for format (Read / Watch / Listen) and tag.
- Bottom-left (`left/right:28px; bottom:26px`, text-shadow `0 1px 2px rgba(0,0,0,.6), 0 0 18px rgba(0,0,0,.5)`): source · date eyebrow (11px / 600 / `.12em` uppercase), title Poppins 300 `clamp(26px,3.2vw,34px)` / 1.1 / max 22ch, dek 14px / 1.55 / max 68ch, then two buttons: gold "Read the article →" (or "Watch →" / "Listen →") and outline "Why it matters to Aldar". Whole card opens the reader.

## B · Shelves with a Cards / List toggle
- Shelves are renamed **Articles · Videos · Podcasts**, each headed by a gold numeral (28px / 300) + 15px / 500 white name + "N in this edition" (12px `.5`). Numbers run 01, 02, 03 over the shelves that actually have items. The existing All / Read / Watch / Listen format filter is unchanged.
- A segmented toggle sits right-aligned above the first shelf: `▣ Cards` / `☰ List`, pill group (`rgba(255,255,255,.06)` track, `1px solid rgba(255,255,255,.12)`, radius 999, 3px padding), active segment gold fill. **Persist the choice** (`localStorage['atl-layout']`, default `cards`).
- **Cards** (4a): grid `repeat(auto-fill, minmax(250px,1fr))`, gap 16. Each card is the catalogue 2a card: `aspect-ratio:3/4`, radius 10, photo + the 2a scrim (`.32 0% → 0 18% → 0 36% → .58 54% → .84 72% → .92 100%`), top row = tag pill left + duration pill right (`▶ 12 min` for video, `♫ 33 min` for podcast, `8 min read` for articles; omit when empty), bottom: source (11px / 600 uppercase, ellipsis), title in a **fixed 58px box** (20px / 29px line-height, clamp 2), **why it matters** as the two-line essence (12px / 18px, height 36px, clamp 2), then a hairline rule with an outline format button (Read / Watch / Listen) left and gold "Why it matters →" right. Hover lifts 4px.
- **List** (4b): rows `grid-template-columns: 150px minmax(0,1fr) auto`, gap 22, `padding:18px 0`, `border-bottom:1px solid rgba(255,255,255,.1)`. 4/3 thumbnail (radius 8, play badge for video/podcast), then source · tag · duration eyebrow (11px / 600 uppercase, `.75`), title 19px / 1.3, and "**Why it matters ·** …" in 12.5px `.7` with the label in gold; an outline pill "Read → / Watch → / Listen →" on the right. Nothing is clipped in List.

Podcast and video artwork with heavy lettering fights the card text — if that bothers reviewers, favour List for those shelves or ask the pipeline for a focal point per story.

## C · Reader → 5a Continuous Portrait
Replaces the sand two-column reader (rail + article). One dark panel (`#0A0A0A`, radius 14), full width.
- **Hero** `height:min(520px,62vh); min-height:420px`, photo + the detail scrim (`.35 0% → 0 22% → 0 40% → .6 62% → .9 82% → #0A0A0A 100%`). For watch/listen the ▶ play link to the source sits at 38% height.
  - Top-left: gold "✦ Signal of the week" (only on the lead), then dark pills: format, tag, insight type (if any). Top-right: outline "← Library" button (the existing back action).
  - Bottom-left: source · date · read time eyebrow; title Poppins 300 `clamp(32px,4.2vw,44px)` / 1.06 / max 20ch; dek 14px / 1.55 / max 60ch; buttons: gold "Read original article ↗" (the existing `ctaLabel` + source URL), outline Save (gold fill once saved — same contract as the catalogue card); image credit line under them (10px uppercase `.5`).
- **Speakers / transcript** row (media only) under the hero, dark pills + gold link.
- **Chapters** use the detail-handoff shell (`display:flex; flex-wrap:wrap; gap:20px 32px; padding:28px 32px; #161616; radius 14`, left column `flex:0 0 170px` with gold numeral 34px / 300 and 15px / 500 white label, right column `flex:1 1 420px`):
  - **01 AI summary** (`✦ AI-generated` tag under the label) — the summary paragraphs 14px / 1.7 `.88`; Key insights beneath a hairline with gold "—" markers when present.
  - Pull quote between 01 and 02: centred, Poppins 300 26px / 1.4, max 36ch, source in 10px uppercase `.5`. Strip any quote marks and trailing "- Source" already in the data; render with typographic quotes.
  - **02 Why it matters to Aldar** (`✦ AI`) — 17px / 1.55 white; "Relevant to" line pills under a hairline.
  - **03 Signature Experience to explore** (`✦ AI-suggested`) — title 22px / 400, text 13.5px `.75`, gold button "Open in Idea Exchange →" (replaces the old "Draft in Experience Builder" — that destination no longer exists; wire to the Idea Exchange / transfer view).
  - **04 More in this edition** — the former left rail becomes a row of 2a cards (`minmax(220px,1fr)`, 3/4, tag + format pills, source + 3-line clamped title), every other story in the edition. Clicking swaps the reader.
- The old "Continue exploring" (related) section is covered by 04; `related` stays in the data.

## Done when
- Shelves show the 2a hero, numbered shelves and a working Cards/List toggle that survives reload.
- Opening any story from cards, list or the hero shows the dark reader with sections 01–04; video/podcast stories show the play link and speakers.
- Save, Read original, back to library, and the edition archive all still work.
- No light-theme colour leaks (old `#F3EFE7` / `#152632` reader styles are gone).
- Titles, pills and buttons never wrap mid-word at 1280px and at 900px.
- No console errors.
