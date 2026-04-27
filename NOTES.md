---
name: Coach — project notes
description: HA addon life coach app — current state, deferred work, and direction
type: project
---

## What it is

Coach is a Home Assistant addon (local, GitHub-hosted) that acts as a personal life coach. It's a FastAPI + Jinja2 + HTMX web app running in Docker, accessible via HA ingress and optionally via a direct port. Multi-user, calendar-integrated, dual-database.

Repo: https://github.com/daveinc/personal-trainer-agent
Addon slug: `1226bac9_coach`
Current version: **0.3.0**
Target hardware: aarch64 (Raspberry Pi)

---

## Stack

- **FastAPI** — backend routes
- **Jinja2** — server-rendered templates
- **HTMX** — dynamic UI without a JS framework (tab switching, partial reloads)
- **SQLite** — local DB at `/data/coach.db`, 30-day rolling cache
- **MariaDB** (optional) — full history mirror, configured via addon settings
- **HA Calendar API** — all scheduled events stored in `calendar.coach`
- **HA Ingress** — primary access method; direct port (8765) optional via null-port trick

---

## What's built and working (v0.3.0)

- **Auth**: cookie-based login. Passwords stubbed — any input logs in, first login auto-creates the user.
- **Dashboard**: overview page (placeholder stats, wired to DB).
- **Fitness**: today/week/month views of calendar events. Done/Skip buttons log to DB. Logging syncs to external DB if configured.
- **Settings page**: single `/ui/settings` page with two HTMX-lazy-loaded tabs:
  - *Database tab*: SQLite stats, external DB stats, per-user log counts, delete user/logs, wipe all, backup/restore SQLite.
  - *Calendar tab*: list/filter events by user, edit/delete per event, backup to JSON, restore from JSON with optional "replace existing" checkbox.
- **8 category pages** (Health, Schedule, Finances, Learning, Relationships, Check-ins, Milestones, Challenges): pages exist and load, all showing static sample content — not yet wired to real data.
- **Sidebar**: Dashboard → 9 categories → Settings.
- **Dual DB**: SQLite always; MariaDB mirror if `db_host` is set. DB logic: host empty = SQLite only; host set + name empty = use `homeassistant` schema; host + name set = use that DB (must exist, never auto-create).
- **Translations**: `translations/en.yaml` labels all settings fields in HA UI.
- **Docker cache busting**: `LABEL version=` in Dockerfile before `COPY app/` — updated with every release.

---

## Deferred / known gaps

- **Passwords**: `verify_password` always returns True. Needs bcrypt before any real user has access.
- **Category pages**: all 8 non-fitness categories show static sample data. Each needs its own DB model, routes, and real data wired in.
- **Check-in form**: renders on the Check-ins page but submits nowhere — no backend yet.
- **AI coaching**: the original goal. No AI integration exists yet. The plan was a FastAPI agent layer (API-agnostic: Claude or local Ollama) that the web UI calls for advice, check-ins, and motivation.
- **Pattern/scoring system**: high-scoring AI interactions get promoted to a local pattern store to reduce API calls over time.
- **Beta tester**: user was close to adding a first beta tester at time of v0.3.0.

---

## Release workflow (critical)

1. Bump version in `config.json`
2. Bump `LABEL version=` in `Dockerfile` to match
3. Push to GitHub
4. In HA: **Addon Store → ⋮ → Reload** (pulls fresh git commit)
5. In HA: **Coach → Rebuild**

Both steps 4 and 5 required. Skipping Reload builds from stale on-disk files.

---

## General direction

Coach is scaffolding for a full AI life coach. The category pages are the UX skeleton — the next major phase is wiring each one to real data and eventually connecting an AI agent that:
- Gives advice per category (fitness plan, budget review, learning suggestions)
- Runs check-ins and stores mood/energy history
- Surfaces patterns over time ("you always skip gym on Tuesdays")
- Routes routine queries to a local model (Ollama) once a pattern library matures

Priority order for next sessions:
1. Real password auth (bcrypt)
2. Wire check-in form to DB (mood, energy, notes — template already exists)
3. Pick one category (Health or Finances) and wire it end-to-end as the model for the rest
4. AI agent integration (start with Claude API, design API-agnostic from day one)
