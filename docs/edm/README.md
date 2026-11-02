# Handoff: Aldar CX Time — Edition announcement EDM "4b Sadu Thread"

## Overview
This is the email that tells colleagues a new edition of **Aldar CX Time** is live. CX Time is the weekly curated-stories feature in the Signature Experience Hub. The email has five parts:
- a full-bleed photographic hero with a centred masthead;
- the edition headline and intro;
- three lead stories, shown as alternating photo/text spreads;
- a call-to-action panel;
- a one-line sign-off.

The email teases the stories. It deliberately does not include the "For Aldar" takeaways, so that readers click through to the edition. The reference content is Edition 3 (2 November 2026). The template must render every future edition the same way.

## About the design file
`edm-e3-4b-sadu-thread.html` is **send-ready email HTML**. It uses nested `role="presentation"` tables, inline styles, no JavaScript, and Outlook conditionals and VML. Treat it as the exact target output.

The job is **to turn it into a template that renders any edition from data and real photographs.** That template can be a small Node build (template literal or Handlebars), React Email or MJML, or your email platform's own template language. Whichever you choose, the compiled HTML must keep the rules below. Do **not** rebuild it as web HTML: flex, grid, CSS-class layout and external stylesheets all break in Gmail and Outlook.

## Fidelity
**High-fidelity and approved by the client.** The colours, sizes, line-heights, padding and copy below are final.

## Client decisions (do not undo)
- **Poppins throughout.** No serif.
- **No "For Aldar" lines** on the stories.
- **No pills** in the hero. "Edition 3" sits on the date line instead.
- **No unsubscribe link, preferences link or postal address.** This is an internal send. If your platform injects a compliance footer, check with the client before letting it ship. Add an unsubscribe link only if the list will ever include external recipients.
- The pattern is the **Sadu lozenge** (see "Pattern assets"). It is used as `<img>` dividers, not as a background, so it shows in every email client.

## Email engineering rules
- The layout is one centred **600px** card (`class="w"`, `#141414`) inside a 100% outer table (`#0C0C0C`). The outer cell padding is `32px 0 48px`. Outlook gets a `<!--[if mso]>` 600px wrapper.
- Every style is inline. The `<style>` block holds only resets and the mobile media query.
- **Fonts:**
  - Poppins loads with a `<link>` and an `@import`, both inside `<!--[if !mso]><!-->` (weights 200, 300, 400 and 600).
  - Outlook on Windows is forced to Arial via an `mso` style.
  - The stack everywhere is `'Poppins','Helvetica Neue',Helvetica,Arial,sans-serif`.
  - Gmail and Outlook Windows show the fallback. That is expected.
- `mso-line-height-rule:exactly` goes on all text. Every table and cell has explicit widths.
- Spacers are `<div style="height:N;line-height:N;font-size:0">&nbsp;</div>`. Never use margins.
- Use `color-scheme: dark` only. The design is dark by intent, so clients won't invert it.
- The hidden preheader comes first in `<body>`, followed by 70 repetitions of `&#847;&zwnj;&nbsp;`.
- Keep the email under Gmail's ~102 KB clip. It is currently 18 KB.

### Mobile (`@media screen and (max-width:620px)`)
| class | effect |
|---|---|
| `.w` | card 100% |
| `.st` | stack the cell (`display:block;width:100%;box-sizing:border-box`) |
| `.px` | side padding becomes 24px |
| `.hs` | hide (story gutters, and the desktop-only `<br>` in the CTA sub-line) |
| `.fi` | image goes to 100% width, auto height |
| `.pt16` | stacked story text gets 16px top padding |
| `.phh` | hero spacer drops from 150px to 96px |
| `.mast` | "CX Time" drops from 54/56 to 44/46 |
| `.h1` | hero headline drops from 56/60 to 42/46 |

**Preview gotcha:** a 600px iframe triggers the mobile layout. Preview the desktop layout at 680px or wider.

**Known behaviour to fix in the build:** story 02 has its image on the **right**, so it comes after the text in source order. On phones it therefore stacks text-first, while 01 and 03 stack image-first. To make all three stack image-first, use the `dir="rtl"` swap. Put the image cell first in the source, set `dir="rtl"` on 02's row table, and set `dir="ltr"` on each cell.

## Layout, top to bottom

**Palette:**
- Grounds: outer `#0C0C0C` · card `#141414`
- Text: ivory `#F3EFE6` · body `#C4BFB5` · muted `#8E897F`
- Gold: rule `#D9B46A` · highlight `#E6C47F` · button ink `#0E0E0E`
- CTA panel: gradient `#24211B`→`#16140F` · border `#3A3226`

### 1 · Hero
The hero is one table with the photograph as its background:
- `bgcolor="#141414"` and `background="img/e3-hero-mast.jpg"`;
- `style="background:#141414 url(…) center top / cover no-repeat"`;
- for Outlook, a VML `<v:rect>` of 600×560 with `<v:fill type="frame">` wrapping the content.

Top to bottom inside it:
- **Masthead,** centred, with padding `36px 40px 0`:
  - "ALDAR": 13/17, ivory, letter-spacing 11px, uppercase, `padding-left:11px`. The padding balances the trailing tracking so the word centres optically.
  - Gap of 10px.
  - "**CX** Time": 54/56, weight 200, letter-spacing 1px, ivory. "CX" is `#E6C47F` at weight 400. Class `mast`.
  - Gap of 14px.
  - Ornament row: a 56×1 gold rule, then `pat-sadu-mini-clear.png` at 92×25 with 10px padding each side, then a 56×1 gold rule.
- **Spacer:** 150px (96px on mobile). This is where the photograph shows.
- **Text block,** padding `0 40px`, left-aligned:
  - A 40×1 gold rule `#D9B46A`.
  - Gap of 20px.
  - Date line: 10/14, `#C4BFB5`, letter-spacing 2.6px, uppercase. It reads **`Edition 3`** (in `#E6C47F`) `  ·  2 November 2026`.
  - Gap of 16px.
  - Headline: "Worth leaving<br>home for.", 56/60, weight 300, letter-spacing −.8px, ivory. Class `h1`.
  - Gap of 24px.
  - Intro: 15/26, `#C4BFB5`.
  - An 8px bottom spacer.

### 2 · Sadu band divider
- Padding `52px 40px 52px`, centred.
- `pat-sadu-band.png` at 520×28, class `fi`.

### 3 · Three story spreads
Row padding: `0 40px` for the first row, `56px 40px 0` after that. Each row is one table with:
- an **image cell** 264px wide, holding a 264×330 image (2× asset 528×660), `display:block`, no radius, no frame;
- a **28px gutter** (class `hs`);
- a **text cell**, vertically centred.

The layout alternates: 01 image-left · 02 image-right · 03 image-left.

The text cell holds, in order:
- numeral `01`/`02`/`03`: 56/56, weight 200, `#D9B46A`;
- gap of 14px;
- `who · kind`: 9/13, `#8E897F`, letter-spacing 2.6px, uppercase;
- gap of 12px;
- title: 24/31, weight 300, ivory, linked to the edition, no underline;
- gap of 12px;
- what: 13/22, `#C4BFB5`.

### 4 · Second Sadu band
- Padding `60px 40px 0`, the same band image.

### 5 · Call-to-action panel
- **Wrapper cell:** padding `48px 24px 0`. The panel is deliberately wider than the text column.
- **Panel table:**
  - `bgcolor="#1C1A16"`, plus `background-image:linear-gradient(180deg,#24211B 0%,#16140F 100%)`;
  - `border:1px solid #3A3226`, `border-radius:4px`, `border-collapse:separate`.
- **Inner cell:** padding `56px 48px 54px`, centred.

Content, in order:
- Kicker: "Edition 3 is live in the Hub", 10/14, `#C4BFB5`, letter-spacing 3px, uppercase.
- Gap of 18px.
- "Step inside<br>the edition.", 40/46, weight 300, letter-spacing −.5px, ivory. No class, so it stays 40 on mobile.
- Gap of 18px.
- "Three stories, and a Signature Experience `<br class="hs">` to explore for each.", 15/24, `#C4BFB5`.
- Gap of 34px.
- **Button,** label **READ THE EDITION →**:
  - **Outlook:** `<v:roundrect>` 340×60, `arcsize="50%"`, `fillcolor="#D9B46A"`, `stroke="f"`, text Arial 14 bold, letter-spacing 3px, `#0E0E0E`. The `xmlns:w` namespace is on `<html>` for `<w:anchorlock/>`.
  - **Everything else (`<!--[if !mso]><!-->`):** a `<td>` with `bgcolor="#D9B46A"`, `background-image:linear-gradient(180deg,#E6C47F,#C9A257)`, `border-radius:999px` and `box-shadow:0 10px 30px rgba(217,180,106,.28)`. It wraps `<a style="display:block;padding:21px 46px">`, set 14/18, weight 600, letter-spacing 3px, uppercase, `#0E0E0E`, nowrap.

### 6 · Sign-off
- Padding `48px 40px 44px`, centred.
- `pat-sadu-mini.png` at 104×28.
- Gap of 22px.
- "Curated by Aldar Group Customer Experience": 9/13, `#8E897F`, letter-spacing 2.4px, uppercase.

## Content (Edition 3 reference)
- **Preheader:** Cosm's in-seat menus, a museum you navigate by mood, and a showroom that starts with lunch.
- **Suggested subject:** Edition 3 · Worth leaving home for
- **Date line:** Edition 3 · 2 November 2026
- **Headline:** Worth leaving home for.
- **Intro:** This week's edition is about the moment a visit stops being a transaction and becomes an experience worth leaving home for. Three stories lead it, and each comes with what it could mean for Aldar.

| # | who · kind | title | what |
|---|---|---|---|
| 01 | Cosm · Cinema domes | The film's own menu, served to your seat | Cosm's cinema domes pair each film with its own menu and bring it to your seat, so dinner becomes part of the show. |
| 02 | Portland's science museum · Museum | A route you choose by mood, not by floor plan | Visitors pick their way through the museum by how they want to feel, rather than following a fixed map. |
| 03 | Jaguar, London · Showroom | A showroom that opens with lunch, not a pitch | Jaguar's London showroom welcomes visitors to the table before anyone talks about a car. |

### Template variables
| variable | notes |
|---|---|
| `edition.number`, `edition.date` | From CX Time data (`window.AT_DATA.editions[0]`: `n`, `date`) or editor input. Used in the date line, the CTA kicker and `<title>`. |
| `headline` (with a manual line break), `intro`, `preheader`, `subject` | Editorial input per send. The data has no field for these. |
| `stories[0..2]` → `who`, `kind`, `title`, `what`, `image` | Editor-picked. The defaults are the lead item plus the next two; `title` is from `title` and `what` is from `dek`. |
| `heroImage` | Must go through the hero pipeline below. |
| `editionUrl` | Every link in the email. The current value is a placeholder: `https://hub.aldar.com/cx-time/edition-03`. |

## Image pipeline
All images are JPEG cover crops. Host them on a public https server. Relative `img/` paths only work in this folder.

- **Hero** (`e3-hero-mast.jpg`):
  - Size and crop: 1200×1120, q≈.74, cover crop with its horizontal anchor at 35% and vertical at 50%.
  - Two fades are **baked into the pixels**, so clients that drop CSS gradients still read correctly:
    1. **Top darkening** behind the masthead, over the top 44% of the height: `rgba(14,13,12,.86)` at 0 → `.72` at 45% of the band → `.35` at 75% → `0` at the end.
    2. **Foot fade** into the card: clear until 40%, `rgba(20,20,20,.6)` at 62%, `.92` at 84%, solid `#141414` at 100%.
  - Check that the masthead zone stays dark: average luminance ≈ 68/255, peak ≤ ~125. Over bright skies, deepen the top fade.
- **Story images** (`e3-01..03.jpg`): 528×660 (4:5), q≈.74, cover crop. Tune the anchor per image to keep faces in frame.
- **Dummies:** all four current photographs are placeholders from the Hub's own photo library:
  - hero: Hospitality *golden-hour beach gathering*;
  - 01: *arcade dining*;
  - 02: *secret door*;
  - 03: Development *welcome lounge*.

  Replace them with Edition 3 imagery.

## Pattern assets (Sadu lozenge)
These are gold `#E6C47F` line work, drawn at 2× and faded horizontally with an alpha mask. Regenerate them from this recipe if you need other sizes:
- **`pat-sadu-band.png`:** 1040×56 drawn on opaque `#141414`, shown at 520×28.
  - It has 20 units (unit width u = 52), plus 1.6px rules at y = 3.5 and y = H − 3.5.
  - Each unit has: an outer diamond outline (half-width .42u, half-height .36H); an inner filled diamond at half that size; a 2.2px dot at each unit boundary; and small filled tick diamonds above and below each boundary.
  - Mask: 0 → .5 → 0 across the width.
- **`pat-sadu-mini.png`:** 208×56, 4 units, mask peak .6, on opaque `#141414`. Used at the sign-off.
- **`pat-sadu-mini-clear.png`:** the same motif on a **transparent** ground, mask peak .75. Used over the hero photograph. **Do not swap in the opaque version there**, because it shows as a dark box on the photo.

## Before every send
1. Fill in the hosted image URLs. Re-export the hero with its baked fades.
2. Set `editionUrl` to the real edition page.
3. Set the subject line and confirm the preheader.
4. Test in Gmail (web and app), Outlook 365 and Windows desktop, Apple Mail (iOS and macOS) and Samsung Mail.

## Files
- `edm-e3-4b-sadu-thread.html`: the approved email (18 KB).
- `img/`: `e3-hero-mast.jpg`, `e3-01.jpg`–`e3-03.jpg` (dummy photography), `pat-sadu-band.png`, `pat-sadu-mini.png` and `pat-sadu-mini-clear.png`.
- In the project root (not in this folder): `CX Time EDM Options.dc.html` is the review canvas. 4b is under Turn 4, and the Tweaks panel has a 375px mobile toggle.

## How the pipeline builds it (`pipeline/cxtime/edm.py`)
- **Fits the reading window.** The card is fluid: `width:100%; max-width:600px`, not a fixed 600px, so it shrinks to a narrow reading pane or phone even in mail apps that ignore the media query. The story spreads are fluid-hybrid inline-blocks (264px photo + 256px text with the 28px gutter inside it). They sit side by side at 520px and stack, photo first, below that. Outlook for Windows gets 600px ghost tables. The CTA button may wrap, so it never forces the email wider than the window.
- **Story 02** uses the `dir="rtl"` swap, so every row stacks photo first on phones.
- **Hero photo** is a story from the edition that the email does not feature, so the lead's photo isn't shown twice in a row. Over bright photographs both baked fades deepen automatically: the masthead zone, and the zone behind the date line and headline.
- **Headline** is set on two lines, split where the lines come out most even, unless the editor gives an explicit line break.
- **Subject** is `Edition N · <headline without the full stop>`.
- **Sadu patterns** are drawn from the recipe above into `sites/cx-time/email/assets/` and shared by every edition.
- **Images** are hosted at `https://aldar-cx-time.netlify.app/email/edition-N/`, and every link goes to `https://aldar-cx-time.netlify.app`.
