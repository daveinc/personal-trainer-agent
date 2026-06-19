# _index.md — Coach

## Quick Pointers

| What | Where |
|---|---|
| All pending tasks + history | `WORKLOG.md` |
| Current status + blockers | `WORKLOG.md` |
| Current version | v0.4.19 (deployed) |
| Repo | https://github.com/daveinc/personal-trainer-agent |
| Run rebuild after every push | HA → Addon Store → Reload → Coach → Rebuild |

---

## Architecture Overview

FastAPI + Jinja2 + HTMX + SQLite, packaged as an HA addon. Runs via ingress on port 8765. Auth via HA ingress headers (`X-Remote-User-Name`). Addon slug: `1226bac9_coach`.

```
HA Ingress (port 8765)
  → FastAPI app (main.py)
    → SQLite (local) or MariaDB (external)
    → Scheduler (60s tick — slot notifications + daily brief)
    → HA Client (get_ha_state via SUPERVISOR_TOKEN)
    → HA Events (webhook action callbacks from notifications)
```

---

## File Map

```
coach/
├── WORKLOG.md                          Pending tasks + completed history
├── WORKLOG.md                           Current status + blockers
├── _index.md                           This file
├── config.json                         Addon manifest, version, options schema
├── Dockerfile                          aarch64 target — LABEL version must match config.json
└── app/
    ├── main.py                         FastAPI app, lifespan, middleware
    ├── config.py                       Loads /data/options.json → env vars
    ├── database.py                     LocalSession (SQLite), ExtBase (MariaDB), init_db
    ├── models.py                       All SQLAlchemy models
    ├── deps.py                         Shared FastAPI deps
    ├── services/
    │   ├── notifier.py                 HA notify calls (pre-slot, post-slot, daily brief)
    │   ├── scheduler.py                60s tick — slot notifications + daily brief at 07:00
    │   ├── ha_client.py                get_ha_state(entity_id) via SUPERVISOR_TOKEN
    │   └── ha_events.py               HA event listener (webhook actions from notifications)
    └── routes/
        ├── ui.py                       Dashboard + main page rendering
        ├── auth.py                     Login/logout, HA ingress auto-login
        ├── onboarding.py               Category schedule: Fixed/Free/Skip per category
        ├── schedule.py                 Slot CRUD
        ├── checkins.py                 Daily check-in (mood, energy, notes)
        ├── finances.py                 FinanceLine CRUD
        ├── health.py / fitness.py      Health + workout tracking
        ├── learning.py                 LearningItem CRUD
        ├── relationships.py            Person CRUD
        ├── goals.py                    Goal + GoalProgress CRUD
        ├── trends.py                   TrendPeriod + TrendObservation
        ├── settings.py                 User preferences + Skills tab
        └── webhook.py / action_router.py  HA notification button callbacks
```

---

## Quick-Edit Reference

| To change... | Go to... |
|---|---|
| Daily brief time | `scheduler.py` → `_check_daily_brief`, change `"07:00"` |
| Daily brief content | `notifier.py` → `_SCHEDULE_CONTEXT` dict |
| Add a new notify type | `notifier.py` → add function, call from `scheduler.py` |
| Add a new model | `models.py` → add class, `database.py` → add to init_db |
| Add a new route/page | New file in `routes/`, import + include in `main.py` |
| Version bump | `config.json` version + Dockerfile `LABEL version=` — BOTH required |

---

## Deploy Sequence (non-negotiable)
1. Bump version in `config.json` AND `Dockerfile LABEL`
2. Push to GitHub
3. HA → Addon Store → ⋮ → **Reload**
4. HA → Coach → **Rebuild**
5. Test in browser before marking done

## Protected — Do Not Remove
- Onboarding step 2: Fixed/Free/Skip per category (`onboarding.html`, `onboarding.py`)
- `UserCategorySchedule` model — not the same as `Slot`, do not merge or drop

## Plans

| File | Covers |
|---|---|
| `plans/field-loop-spec.md` | Field notification loop — Phase 1 (foundation + models, done 2026-06-19) + Phase 2 (session start integration, pending). Architecture note: return path is calendar event write-back, not PendingMessage API. |
| `plans/notification-button-map.md` | Button sets per project stage — source of truth for all notification logic. Calendar write-back design. Billing sub-stages (40/40/20). Not yet implemented — active spec. |

