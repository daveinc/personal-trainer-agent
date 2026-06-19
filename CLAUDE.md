# Coach — HA Addon Life Coach

## Active Plan
@C:\Users\davei\.claude\plans\2026-05-28-coach-steps-0.1-0.3.md

## Project Rules
- Do NOT hardcode notify service — must be a settings dropdown (service + target)
- After every rebuild: test in browser before moving to the next task
- Release: bump BOTH `config.json` version AND `Dockerfile LABEL version=` — both required, no exceptions
- Never remove onboarding step 2 or UserCategorySchedule model — ever
- HA Reload + Rebuild: Dave only — Claude only pushes to GitHub
- **Plans own the todo list and intent** — update plan files when scope or approach changes, before doing the work. WORKLOG records timing and completion only (date + what shipped). Never duplicate a todo list in WORKLOG.

## Notify Service
- Confirmed service: `notify.mobile_app_notepro`, target: `notify.notepro`
- User must be able to choose notify service + target from a dropdown in Coach settings — do NOT hardcode

## Session Start — Read in Order
1. `WORKLOG.md` — pending tasks + history
2. `_index.md` — architecture, file map, quick-edit reference
3. `plans/field-loop-spec.md` — field notification loop architecture (Phase 1+2)
4. `plans/notification-button-map.md` — full button map per project stage (source of truth for all notification logic)

At the start of every conversation in this folder:
0. Read global CLAUDE.md → **"For Project Workers"** section (`C:\Users\davei\.claude\CLAUDE.md`) — skill discipline and universal rules
3. Invoke skills — mandatory before starting work:
   - `using-superpowers` — always first on any non-trivial task
   - `systematic-debugging` — any bug or unexpected behavior (start here before touching code)
   - `defense-in-depth` — any change touching auth or HA ingress headers
   - `webapp-testing` — test in browser after every change before claiming done
   - `verification-before-completion` — before marking any task complete
Do NOT read the master WORKLOG.md or daves-worklog.md — this is a worker session, scoped to Coach only.

## Worker Roles

**Autonomous — no Dave needed:**
- Backend Developer — implements features, fixes bugs, adds routes, models, templates per todo.md
- DevOps — version bumps (config.json + Dockerfile), Dockerfile changes, push to GitHub
- QA — tests features in browser after every deploy, verifies calendar/schedule behavior

**Non-autonomous — needs Dave input or approval:**
- Product Advisor — proposes new features or UX improvements to Coach, Dave decides priority
- Life Coach Designer — advises on what data to surface, how check-ins should feel, daily brief content
- HA Integration Advisor — proposes new HA integrations (push notifications, entity reads), Dave approves

**Never — Dave only:**
- HA Reload + Rebuild in addon store — Claude pushes to GitHub, Dave executes in HA UI
- Notify service configuration (mobile_app_dave — Dave's phone)
- Remove or simplify onboarding step 2 or UserCategorySchedule model — protected, no exceptions
- Change addon options schema without Dave review

---

FastAPI + Jinja2 + HTMX + SQLite/MariaDB personal life coach, packaged as an HA addon.

- **Repo:** https://github.com/daveinc/personal-trainer-agent
- **Addon slug:** `1226bac9_coach`
- **Current version:** 0.4.25 (deployed — confirmed 2026-06-03)
- **Target:** aarch64 (Raspberry Pi)

## Status (v0.4.25)
Auth (HA ingress auto-login), dashboard, all category pages wired to DB (health, finances, fitness, learning, relationships, routines, trends, check-ins), settings (preferences + categories + notifications tabs), onboarding with Fixed/Free/Skip schedule. Calendar events display in Schedule. Actionable push notifications 30 min before calendar events (Done/Skip/Snooze). Real-time event logging with inline form on Schedule, Today's Log on Dashboard. Dark HOD visual theme.

## Next priorities
1. AI agent integration (Claude API, model-agnostic)
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

## Master Templates — References

All files in `C:\Users\davei\.claude\projects\ha\master-templates\`

| File | Use for |
|---|---|
| `blueprint-ha-addon.md` | Addon structure, Dockerfile pattern, config.json schema |
| `reference-ha-mcp.md` | HA MCP tool reference — entities, services, dashboard calls |
| `ha_components.yaml` | HA component reference (entity types, platforms, config) |
| `ha_components.index` | Quick-lookup index for ha_components.yaml |

## Allowed Tools
File reads/writes to this folder and subfolders. Bash for git commands (dev branch only). HA MCP for testing notifications and calendar entities. No destructive HA operations.


