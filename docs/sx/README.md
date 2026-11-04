# Submit & review: business-line submissions

Business-line leads submit new signature experiences, and updates to their existing ones, at
**https://aldar-signature-experience.netlify.app/sx/**. They can also reach it from the hub's sidebar.
Group CX reviews each submission. Approved submissions appear on the hub and in the MCP / CX Martin
straight away, with no redeploy.

## Who can do what

| Role | Signs in with | Can |
|---|---|---|
| Line lead (one per line) | That line's access code | Submit new experiences and updates for their own line only. See their submissions and status. Edit or withdraw while pending. Resubmit when sent back. |
| Reviewer (Group CX) | The reviewer code (`SX_REVIEWER_CODE`, a Netlify secret) | See everything. Approve, edit then approve, send back with a comment, reject, unpublish. Manage lead names, emails and codes. Set up notifications. |

Codes are sent as the `x-sx-code` header. The lead codes live in Netlify Blobs and are managed on the
**Leads & access codes** tab. "New code" revokes the old one immediately. To change the reviewer code,
edit `SX_REVIEWER_CODE` under Netlify → Project configuration → Environment variables, then redeploy.

## Lifecycle

`pending` → `approved` (published) · `returned` (changes requested) → `pending` again · `rejected` · `withdrawn` · `approved` → `unpublished`

- **New experience:** name, essence, narrative, pillar, journey stage, type, segment, stage, target month,
  assets in scope (and where it's live), touchpoints, benefits (Estates, Project Plus), latest note,
  photo (required) and a SharePoint folder link. The choices come from each line's own data, so a
  submission looks and filters like any other card.
- **Update:** pick one of your line's experiences, then add a note (required) and, optionally, a new stage,
- **Photos from the live experience:** part of an update. The lead chooses the asset (for example W Hotel), uploads photos and can add a caption. Once approved, the photos appear in the card detail under *Implementation photos*, grouped by asset. An update with only photos needs no written note.
  target, live assets, essence, narrative or photo. The note is added to the experience's dated history.

## How it works

- `sx/index.html`: the submit and review page.
- `netlify/functions/sx.mjs`: the API at `/api/sx/*`. It stores data in Netlify Blobs:
  - store `sx-submissions`: `sub/<id>`, `published`, `leads`, `settings`;
  - store `sx-photos`: uploaded photos, served at `/api/sx/photo/<key>`.
- `GET /api/sx/published` is the public list of approved records. It is CDN-cached and purged on every
  decision.
- `sx/sx-apply.js` turns approved records into each line's native data format. It is shared by:
  - **the hub:** `index.html` loads it in `<head>` and wraps the seven `*_DATA` globals, so records apply as
    each data set loads. The bundle loader waits up to 2.5 s for `/api/sx/published` before the first
    render. If that fails, the hub renders without the records. `tools/apply_sx_hook.py` installs this
    and also runs at every build;
  - **the MCP:** `netlify/functions/_lib/live-data.mjs` applies the same records to the build-time native
    snapshot and re-normalises, cached for 20 s. Records show `submitted_via_hub` or `last_hub_update`.
- Records apply in approval order, every time the page loads. They don't rewrite `index.html`, so an
  edit to `index.html` from elsewhere still shows. An approved update to the same experience overrides
  the fields it changed.

## Notifications (Teams + email)

These are set on the **Notifications** tab. Paste the webhook URL of a Teams **Workflows** flow ("Send webhook
alerts to a channel" or "…to a chat"). The hub posts an Adaptive Card. The same JSON also carries
`subject`, `html`, `text`, `link` and `email_to`. Add an Outlook **Send an email (V2)** step with:
- To: `triggerBody()?['email_to']`
- Subject: `triggerBody()?['subject']`
- Body: `triggerBody()?['html']`

New submissions are emailed to the reviewer. Decisions are emailed to that line's lead.

## Local test

`node tools/build_mcp_data.mjs`, then run the functions against `@netlify/blobs/server`'s `BlobsServer` with
`NETLIFY_BLOBS_CONTEXT` set (see this repo's history for the harness used).
