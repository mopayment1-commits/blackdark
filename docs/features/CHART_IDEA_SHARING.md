# Chart / Idea Sharing — Feature #177

Sprint 2 growth engine. Simple flow: **Share → Public Link → Immutable Snapshot**.

## Privacy controls

| Mode | Behavior |
|------|----------|
| `private` | Owner only — no public view |
| `unlisted` | Anyone with link can view |
| `public` | Published snapshot via public URL |

## Immutable snapshot

When published, chart data is frozen in `immutable_snapshot`. Edits to the original draft **do not** change the published view — protects against historical tampering.

## Watermark

All public views include:
- `Powered by BLACKDARK`
- Signup link: `/create-checkout-session?tier=pro`

## APIs

| Endpoint | Auth | Description |
|----------|------|-------------|
| `POST /api/platform/share/charts` | User | Create draft |
| `POST /api/platform/share/charts/{id}/publish` | User | Publish immutable snapshot |
| `PUT /api/platform/share/charts/{id}` | User | Update draft (snapshot unchanged if published) |
| `GET /api/platform/share/charts` | User | List user's shares |
| `GET /api/platform/share/chart/{slug}` | Public | View immutable snapshot |
| `GET /api/platform/share/status` | Public | Engine status |

## Acceptance

- Privacy controls (private / unlisted / public)
- Immutable published snapshot verified by tests
