# Showing and hiding hub sections

`features.json` (repository root) decides which sections of the hub are visible. Set a value to `true` to show
a section and `false` to hide it, then commit and redeploy. Nothing is deleted. Code, data and photos stay in place,
so switching a section back on brings it back exactly as it was.

| Switch | When `false`, this is hidden |
|---|---|
| `report_studio` | The Report Studio tab (Signature Experiences: Catalogue · Activity · ~~Report Studio~~), its view and `#report` links, Ask Echo's "Open in Report Studio" and report-PDF download, and report suggestions in Ask Echo |
| `rag_status` | The RAG strip on experience cards (On track / On watch / Needs a decision, priority and next action). In Ask Echo: the RAG instructions and counts, RAG reasons and dots in lists and timelines, the Health table column, the spotlight RAG pill, and "Which experiences are Red?" suggestions |
| `idea_exchange` | The Idea Exchange menu item and view, "See it in Idea Exchange" on experience cards, and Idea Exchange wording in AI disclaimers. In `/mcp` (CX Martin): the `get_idea_moves` tool, the `idea_move` filter, the search category and the `idea_moves` fields |
| `benchmark_editor` | The Benchmark Editor tab inside Benchmark. Library, Business Line Transfer Viewer and Boards stay |
| `project_plus` | Project Plus as a business line everywhere: menu and line page, catalogue chips and counts, catalogue hero, Portfolio Discovery (its headline becomes "six programmes"), Activity feed and search. In `/mcp`: its experiences, programme and counts (asking for it returns "not part of the hub right now"). In Submit & review: its lead and code |
| `board_sharing` | Boards' file sharing: Save board and Import board, a board's Share sheet, the "Shared with me" shelf and the download-file reminder. Boards are labelled *My boards · private to this browser* (wording in `tools/board-sharing.json`) |
| `cx_academy` | The "In development · CX Academy" menu item and view, and the "CX Academy highlights" panel on Portfolio Discovery. Corporate experiences that mention CX Academy, such as *Aldar Performance Pins*, stay |

Hidden destinations also drop out of "Search everything" (⌘K). A bookmark or link to a hidden view opens
Portfolio Discovery instead. Ask Echo is told these sections aren't part of the hub, and never receives RAG data.

**How it works:** `tools/apply_features.py`, which runs on every Netlify build, does three things:
- writes `window.__SIG_OFF` into the page `<head>`;
- adds small guards to the hub's template wherever it builds those menus, tabs, buttons and answer cards;
- swaps a few fixed sentences that name a hidden section for neutral wording, and back again.

It is idempotent, and turning a section off, on and off again gives a byte-identical page. `/mcp` reads
`features.json` directly in `netlify/functions/_lib/mcp-core.mjs`.

## Always on: weekly Portfolio Discovery, and one AI read for comparisons

The same tool also installs three things that aren't switches:
- **Theme of the week.** The third rail on Portfolio Discovery rotates through `discovery-themes.json`, one theme per week, starting each Monday.
  - Each theme has a title, a blurb, colours and a `match` pattern, which is tested against each experience's name and essence.
  - A theme is only used when at least 4 photographed experiences match it.
  - Edit, add or reorder themes, then redeploy.
- **Defining moment of the week.** The showreel opens on it once the welcome screen closes, and the Defining moments rail leads with it.
  - Each week moves to the next business line, then to that line's next flagship.
- **One comparison read.** The compare view asks `/api/compare-read` for its AI read, and CX Martin's `compare_experiences` uses the same code and the same cache. The hub and CX Martin give the same read for the same set, until one of the experiences changes.
