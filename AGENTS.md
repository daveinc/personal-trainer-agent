# Coach — HA Addon Life Coach

FastAPI + Jinja2 + HTMX + SQLite/MariaDB personal life coach, packaged as an HA addon.

- **Repo:** https://github.com/daveinc/personal-trainer-agent
- **Addon slug:** `1226bac9_coach`
- **Current version:** 0.4.6 (deployed on HA)
- **Target:** aarch64 (Raspberry Pi)

## Status (v0.4.7)
Auth (HA ingress auto-login), dashboard, all category pages wired to DB (health, finances, fitness, learning, relationships, routines, trends, check-ins), settings (preferences + categories tabs), onboarding with Fixed/Free/Skip schedule.

## Next priorities
1. AI agent integration (Codex API, model-agnostic)
2. Real password auth (bcrypt — currently any input logs in)

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
