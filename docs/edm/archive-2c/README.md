# Handoff: Aldar CX Time — Edition announcement EDM ("2c Photo-ready")

## Overview
This is the email that tells colleagues a new edition of **Aldar CX Time** is out. CX Time is the weekly curated-stories feature in the Signature Experience Hub. The email holds:
- one headline and a short intro;
- the edition's **three lead stories**, each with a photo, a one-line description and a "For Aldar" line;
- one **Read the edition** button.

It is short on purpose: about one and a half screens. The reference is Edition 3 (2 November 2026), and the template must render every future edition the same way.

## About the design file
`edm-e3-2c-photo-ready.html` is **already send-ready email HTML**: nested `role="presentation"` tables, inline styles, no JavaScript, no web fonts, Outlook conditionals. Treat it as the exact target output.

The job is **to turn it into a template that renders any edition from data and real photographs.** Any of these works, as long as the compiled HTML keeps the rules below:
- a small build script (Node plus a template literal or Handlebars);
- React Email or MJML;
- your email platform's own template language.

Do **not** rebuild it as normal web HTML. Flex, grid, CSS classes for layout and web fonts all break in Gmail and Outlook.

## Fidelity
**High-fidelity.** The colours, sizes, line-heights, padding and copy below are final.

## Email engineering rules (non-negotiable)
- One centred **600px** card table (`class="w"`, `width="600"`, `style="width:600px;max-width:600px"`) sits inside a 100%-wide outer table. The outer cell padding is `28px 0 40px`. Outlook gets a `<!--[if mso]>` 600px wrapper table.
- **Every style is inline.** The `<style>` block holds only resets and the mobile media query. Several clients drop it, so the email must read correctly without it.
- Fonts are email-safe stacks only. Serif: `Georgia,'Times New Roman',Times,serif`. Sans: `Arial,Helvetica,sans-serif`.
- `mso-line-height-rule:exactly` goes on every text style. Every table and cell has explicit widths.
- Buttons are bulletproof: a `<td bgcolor>` with `border-radius:999px` and padding, wrapping an `<a style="display:block">`. Never an image, never a `<button>`.
- Spacers are `<div style="height:Npx;line-height:Npx;font-size:0;mso-line-height-rule:exactly">&nbsp;</div>`. Never use margins for spacing.
- `<meta name="color-scheme" content="light dark">` and `supported-color-schemes`. No pure `#000` or `#fff` grounds.
- The first element in `<body>` is the hidden preheader (`display:none;max-height:0;opacity:0;mso-hide:all`). Its text is followed by 70 repetitions of `&#847;&zwnj;&nbsp;` so that body text does not leak into the inbox preview.
- `<html lang="en">`. Every image has alt text. Every link is a real `href`.
- Stay well under Gmail's **~102 KB** clip. The reference is 17 KB.

### Mobile media query (`@media screen and (max-width:620px)`)
| class | effect |
|---|---|
| `.w` | card goes to 100% |
| `.st` | the cell stacks (`display:block;width:100%;box-sizing:border-box`) |
| `.px` | side padding becomes 22px |
| `.hs` | hidden (the 20px gutter between thumbnail and text) |
| `.pb0` | thumbnail cell loses its bottom padding when stacked |
| `.pt12` | text cell gets a 12px top padding when stacked |
| `.h1` | headline drops to 36/40 |
| `.ph` | image and slot tables go to 100% width |
| `.phh` | hero placeholder cell drops to 190px tall |
| `.fi` | a real image goes to 100% width with auto height |

**Preview gotcha:** the breakpoint is 620px, so a 600px-wide preview iframe shows the *mobile* layout. Preview desktop at 680px or wider.

## Layout (top to bottom)

**Palette:** outer `#E6E1D7` · card `#FDFCF8` · ink `#1B2730` · body `#44505A` · muted `#66707A` · gold `#8A6524` · rule `#E2DCCF` · moss `#2F5A43` · gold fill `#E8B96A` · CTA text on ink `#F6F1E6` · placeholder `#E4DCCD` / `#6B6455`.

1. **Header.** Padding `28px 40px 18px`. A two-cell table:
   - Left: "Aldar CX Time", Georgia 22/26, ink, bottom-aligned.
   - Right: "Edition 3 · 2 November 2026", Arial 10/14 bold uppercase, letter-spacing 1.8px, gold.
2. **Hero image.** Full-bleed, 600×300 with no side padding (2× asset 1200×600). No radius. The whole image links to the edition.
3. **Headline and intro.** Padding `32px 40px 4px`.
   - Headline: Georgia 38/44, ink (mobile 36/40).
   - 14px gap.
   - Intro: Arial 15/24, body.
4. **Three story rows.** Each row sits in a `0 40px` cell and has `border-bottom:1px solid #E2DCCF`, except the last. Each row has three cells:
   - **Thumbnail cell:** 168px wide, padding `24px 0`. The image is 168×126 (2× asset 336×252) with radius 6 and links to the edition.
   - **Gutter cell:** 20px, class `hs`.
   - **Text cell:** padding `22px 0 24px`, holding:
     - `NN · who`: Arial 10/14 bold uppercase, letter-spacing 1.4px, gold.
     - 7px gap, then the **title**: Georgia 19/25, ink, linked to the edition, no underline.
     - 8px gap, then the **what** line: Arial 13/20, body.
     - 9px gap, then the **For Aldar** line: Arial 13/19, moss, with "For Aldar ·" in bold.
   - On mobile the thumbnail and text cells stack (`st pb0` / `st pt12`) and the thumbnail goes full width.
5. **CTA band.** Padding `30px 40px 0`. A table with `bgcolor="#1B2730"`, `border-radius:8px` and `border-collapse:separate`, holding two cells that stack on mobile:
   - Left: "The full stories, and a Signature Experience to explore for each." Georgia 17/25 `#F6F1E6`. Padding `26px 10px 26px 28px`.
   - Right: the button, right-aligned. Padding `26px 28px 26px 10px`. Fill `#E8B96A`, text ink `#1B2730`, Arial 13/16 bold, padding `12px 22px`, radius 999, nowrap, label **"Read the edition →"**.
6. **Footer.** Padding `40px 40px 32px`. A 1px `#E2DCCF` hairline, a 22px gap, then three Arial 11/18 muted lines:
   - *Aldar CX Time is curated by Aldar Group Customer Experience for colleagues across every business line.*
   - *Aldar Properties PJSC · Aldar HQ, Al Raha Beach · P.O. Box 51133 · Abu Dhabi, UAE*
   - **Unsubscribe · Manage preferences**, as ink-coloured underlined links.

### Image slots
The reference file has no photographs yet. Each of the four images is a **placeholder cell**: `#E4DCCD` fill, centred 9px caps label in `#6B6455`, and "W×H · swap before sending" at 10px. The hero cell has no radius; the thumbnails have radius 6.

An HTML comment above each slot holds the exact `<img>` tag to paste in. The template should:
- render a real `<img src="https://…" width="600" height="300" class="fi" alt="…" style="display:block;width:600px;max-width:100%;height:auto;border:0">` when a URL exists (thumbnails: 168×126, add `border-radius:6px`);
- fall back to the placeholder cell when it does not.

Photographs must be on a public https host. Project-relative paths do not exist for recipients.

## Content and data

### Edition 3 copy (the reference)
- **Header date:** Edition 3 · 2 November 2026
- **Headline:** Worth leaving home for.
- **Intro:** This week's edition is about the moment a visit stops being a transaction and becomes an experience worth leaving home for. Three stories lead it, and each comes with what it could mean for Aldar.
- **Preheader:** Cosm's in-seat menus, a museum you navigate by mood, and a showroom that starts with lunch.
- **Suggested subject:** New in CX Time: when a visit becomes an experience

| # | who | title | what | For Aldar (draft) |
|---|---|---|---|---|
| 01 | Cosm | The film's own menu, served to your seat | Cosm's cinema domes pair each film with its own menu and bring it to your seat, so dinner becomes part of the show. | Food as part of the programme rather than a queue in the interval, for cinema and dining nights at Aldar's retail destinations. |
| 02 | Portland's science museum | A route you choose by mood, not by floor plan | Visitors pick their way through the museum by how they want to feel, rather than following a fixed map. | Wayfinding that starts with how someone wants to feel, for malls, community spaces and school open days. |
| 03 | Jaguar, London | A showroom that opens with lunch, not a pitch | Jaguar's London showroom welcomes visitors to the table before anyone talks about a car. | Host first, sell second: a sales-gallery welcome built around hospitality rather than the brochure. |

> ⚠ The "For Aldar" lines were **drafted from the client's summary**. Edition 3 is not yet in the project data. Replace them with the edition's own `why` text before sending.

### Template variables
| variable | source when driven by CX Time data (`window.AT_DATA.editions[0]`, also `data/aldar-times.json`) |
|---|---|
| `edition.number`, `edition.date` | `n`, `date` |
| `headline`, `intro`, `preheader`, `subject` | **editorial input per send.** The data has no field for them, so expose them as form fields or front-matter. |
| `stories[0..2]` | the lead (`lead:true`) first, then the next two items in edition order. Allow an editor override, because Edition 3's three were hand-picked. |
| `story.who` | `sourceShort`, or an editor-supplied subject (the brand or venue, as in Edition 3) |
| `story.title` | `title` |
| `story.what` | `dek` |
| `story.forAldar` | the **first sentence** of `why`. Keep it to one line of thought, roughly 20 words or fewer. |
| `story.image` | hosted URL of the story photograph: a 2× cover crop at 336×252, cropped 40% from the top |
| `hero.image` | hosted URL, 1200×600 (usually the lead story's photograph) |
| `editionUrl` | the edition's page in the Hub. Every link in the email points here. |
| `unsubscribeUrl`, `preferencesUrl` | your email platform's merge tags |

## Interactions and behaviour
- This is static email: there are no hover states and no JavaScript.
- **Every link** (hero, thumbnails, titles, button) opens `editionUrl` in a new tab.
- Responsive: one breakpoint at 620px. Below it, story rows stack (full-width thumbnail first), the CTA band stacks, the hero placeholder shrinks to 190px, and the side padding drops to 22px.
- Dark mode: the light palette is designed to survive automatic inversion. Do not add `prefers-color-scheme` overrides unless testing shows a problem.

## Before every send
1. Host the photographs and fill the four image URLs.
2. Replace the placeholder `https://hub.aldar.com/cx-time/edition-03` with the real edition URL.
3. Swap the `mailto:groupcx@aldar.com…` Unsubscribe / Preferences links for your email platform's merge tags. That address is a placeholder too.
4. Set the subject line and confirm the preheader in your email platform.
5. Test in Gmail (web and app), Outlook 365 and desktop, Apple Mail (iOS and macOS) and Samsung Mail, in light and dark mode.

## Design tokens
- **Colours:** listed in the palette under Layout.
- **Type scale:**
  - Georgia: 38/44 headline · 22/26 wordmark · 19/25 story title · 17/25 CTA line.
  - Arial: 15/24 intro · 13/20 what · 13/19 For Aldar · 13/16 button · 11/18 footer · 10/14 caps labels.
- **Spacing:**
  - Side padding: 40, or 22 on mobile.
  - Section padding tops: 28 / 32 / 22–24 / 30 / 40.
  - Text gaps: 7 / 8 / 9 / 14 / 22.
- **Radii:** 999 (button) · 8 (CTA band) · 6 (thumbnails) · 0 (hero).
- **Widths:** card 600 · thumbnail 168 · gutter 20 · text cell fluid (332 at desktop).

## Files
- `edm-e3-2c-photo-ready.html`: the reference email, send-ready apart from the placeholders above.
- In the project root (not in this folder): `CX Time EDM Options.dc.html`, the review canvas with an inbox preview and a 375px mobile toggle (option 2c).
