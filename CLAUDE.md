# Coach — HA Addon Life Coach

FastAPI + Jinja2 + HTMX + SQLite/MariaDB personal life coach, packaged as an HA addon.

- **Repo:** https://github.com/daveinc/personal-trainer-agent
- **Addon slug:** `1226bac9_coach`
- **Current version:** 0.3.0 (deployed on HA)
- **Target:** aarch64 (Raspberry Pi)

## Status (v0.3.0)
Auth, dashboard, fitness page, settings (DB + calendar tabs), 8 category page shells — all built.
All 8 non-fitness category pages show static data, not wired to real data yet.

## Next priorities
1. Real password auth (bcrypt — currently any input logs in)
2. Wire check-in form to DB (template exists, no backend)
3. Wire one category end-to-end (Health or Finances as the model)
4. AI agent integration (Claude API, design model-agnostic from day one)

## Release workflow (critical — both steps required)
1. Bump version in `config.json` AND `LABEL version=` in `Dockerfile`
2. Push to GitHub
3. HA: Addon Store → ⋮ → **Reload** (fetches fresh commit)
4. HA: Coach → **Rebuild** (skipping Reload builds from stale files)

## Protected features — do not remove without explicit discussion
These were built, removed by accident, and had to be restored. Never simplify them away:
- **Onboarding step 2**: category selection with Fixed / Free / Skip per category, days + time range. Lives in `onboarding.html` and `onboarding.py`. Backed by `UserCategorySchedule` model.
- **UserCategorySchedule model**: stores per-user category schedule preferences. Not the same as `Slot`. Do not merge or drop.

## Testing procedure (required after every deploy)
After every rebuild, test the changed feature in the browser before moving to the next task.
Confirm it works end-to-end — don't assume a clean build means working features.
