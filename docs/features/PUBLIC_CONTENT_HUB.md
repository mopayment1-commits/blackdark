# Public Content Hub — Features #177 + #182

Merged engine: **Chart/Idea Sharing** + **Public Dashboard Sharing**.

## Flow

**Create → Publish snapshot → Share link → View / Clone**

## Snapshot + version

When published, content is frozen in `immutable_snapshot` with an incrementing `version`.
Draft edits **do not** change the published view until the owner explicitly republishes.

## Privacy controls

| Mode | Behavior |
|------|----------|
| `private` | Owner only — no public view |
| `unlisted` | Anyone with link can view |
| `public` | Published snapshot via public URL |

## Public access

- **View only** — no public editing
- **Clone** — authenticated users can clone a published snapshot into a new private draft
- **Watermark** on all public views: `Powered by BLACKDARK` + signup link

## Content types

| Type | Use case |
|------|----------|
| `chart` | Shared chart configuration |
| `idea` | Trading idea / annotation |
| `dashboard` | Market Radar or custom dashboard snapshot |

## APIs

| Endpoint | Auth | Description |
|----------|------|-------------|
| `POST /api/platform/share/content` | User | Create draft (chart/idea/dashboard) |
| `POST /api/platform/share/content/capture-dashboard` | User | Capture Market Radar dashboard |
| `POST /api/platform/share/content/{id}/publish` | User | Publish versioned immutable snapshot |
| `PUT /api/platform/share/content/{id}` | User | Update draft (snapshot unchanged if published) |
| `POST /api/platform/share/content/{id}/clone` | User | Clone published snapshot |
| `GET /api/platform/share/content` | User | List user's content |
| `GET /api/platform/share/view/{slug}` | Public | View immutable snapshot (JSON) |
| `GET /api/platform/share/status` | Public | Engine status |

### #177 compatibility aliases

| Endpoint | Description |
|----------|-------------|
| `POST /api/platform/share/charts` | Create chart/idea draft |
| `POST /api/platform/share/charts/{id}/publish` | Publish chart |
| `GET /api/platform/share/chart/{slug}` | Public chart view |

## Public HTML pages

| URL | Description |
|-----|-------------|
| `/share/content/{slug}` | Generic shared view |
| `/share/dashboard/{slug}` | Dashboard snapshot view |
| `/share/chart/{slug}` | Chart snapshot view |

## Acceptance

- Snapshot/version on publish
- Privacy controls (private / unlisted / public)
- Watermark on public views
- View + clone only — no public editing
