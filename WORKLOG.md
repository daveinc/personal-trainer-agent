# Coach — Worklog

## Pending

### Field Loop — Phase 1+2 (spec ready 2026-06-19)
Plan: `plans/field-loop-spec.md`

**Phase 1 — Fix + foundation** (one worker session):
- [x] 2026-06-19 Fix `ha_events.py` reconnect — add exponential backoff (5s→10→20→40→60s cap), shield DB calls with asyncio.shield()
- [x] 2026-06-19 Add `JobStep` model — per-stage step with status tracking
- [x] 2026-06-19 Add `PendingMessage` model — queue for Claude to read at session start
- [x] 2026-06-19 Update `PIPELINE_STAGES` → survey / materials / on_site / billing / done
- [x] 2026-06-19 `notifier.py` — `STAGE_BUTTONS` dict + `notify_job_step()` function
- [x] 2026-06-19 `ha_events.py` — add `STEP_{step_id}_{verb}` handler branch
- [x] 2026-06-19 `action_router.py` — `handle_step_action()` + `_advance_job_stage()`
- [x] 2026-06-19 `routes/pending_messages.py` — GET /api/v1/pending-messages + POST mark-read
- [x] 2026-06-19 `main.py` — wire new router
- [x] 2026-06-19 DB migration — Base.metadata.create_all() confirmed in database.py, new tables auto-created at startup
- [x] 2026-06-19 **Architecture correction v0.4.26** — replace `PendingMessage` return path with calendar write-back: `PendingMessage` removed from `models.py`, `pending_messages.py` renamed to `_removed`, `append_to_calendar_event()` + `create_calendar_event()` added to `ha_client.py`, `handle_step_action()` rewritten to write `📲 Dave @ HH:MM: {label}` to calendar event description, `_schedule_next_onsite_day()` added for 1-more-day / 2–3-more-days taps, `calendar_event_uid` field added to `JobStep`
- [ ] Smoke test end-to-end — create job step with `calendar_event_uid` set, tap button, confirm calendar event description updated *(Dave to verify after deploy)*

**Phase 2 — Session start integration** (after Phase 1 confirmed working):
- [ ] `/api/v1/jobs/{job_id}/steps` POST endpoint (Claude writes steps to Coach)
- [ ] Session start scans `calendar.coach` last 7 days for `📲 Dave @` lines (NOT pending-messages API — that path was removed)
- [ ] Update superceo CLAUDE.md to scan calendar at session start
- [ ] WORKLOG.md → Coach calendar migration

**Owner:** Worker (Phase 1) → Dave+Claude verify → Worker (Phase 2)

- [x] 2026-06-19 **v0.4.27** — confirmed scheduler tight loop fix: `asyncio.sleep(60)` between ticks + `_notified_events` guard prevent duplicate calendar API calls. Version bumped in config.json + Dockerfile.

### Known gaps — next session
- [ ] ⚡ PRIORITY: Test events from Jun 3 still in calendar.coach — delete at session start
- [ ] Snooze does not re-fire notification — logs "snoozed" but no follow-up push
- [x] Daily brief weekday-only vs 7 days — DAILY, 7 days/week
- [ ] Daily routine slots — Dave to provide times, then add as recurring Slots in Coach
- [ ] Step 0.3 Log button — not yet tested by Dave in browser

### Backlog — Goals with Deadlines
- [ ] Add deadline date field to Goal model
- [ ] Goals with deadlines within 7 days appear in daily brief
- [ ] UI: goals list shows deadline + days remaining, color-coded

### Block 2 — Manual Financial Data Entry (after June 13)
- [ ] Income entries per job/month, fixed obligations, cash position snapshot

### Block 3 — Worker Module (after HOD admin Block 1)
- [ ] Worker profiles in Coach
- [ ] Lead coaching — stage-by-stage guidance with required info gates
- [ ] Step status tracking — workers mark steps done via HA or Coach

### Block 4 — CEO Dashboard
- [ ] All active projects: name, stage, workers, timetable, next due step
- [ ] Financial snapshot: pipeline, cash position
- [ ] Flags: overdue steps, stalled projects, idle workers

### Block 5 — HA Integration
- [ ] Push notifications to workers when step deadline approaches
- [ ] Workers report status back via HA notification reply

### Block 6 — Company Intelligence Feed
- [ ] Coach exposes summary endpoint Claude can read
- [ ] Claude flags anomalies to Dave via notification

### Block 7 — Daily Standup Feature
- [ ] On first load: greet Dave with company + project summary
- [ ] Accept input — mark tasks done, add new, note blockers

### Block 8 — AI Agent Integration
- [ ] Claude API integration (model-agnostic)
- [ ] Real password auth (bcrypt)

### Block 9 — Job Photo Reminders
- [ ] When HOD project moves to "in progress" → schedule photo reminder
- [ ] Reminder at job start + completion

---

## Done

- [x] `fix:` Startup bug
- [x] 2026-05-15 `feat:` Daily brief notification — reads live from configured HA calendar (v0.4.15)
- [x] 2026-05-15 `feat:` Calendar entity configurable via addon options
- [x] 2026-05-16 `feat:` Business Pipeline module — Kanban + job tracker (v0.4.16)
- [x] `feat:` All category pages wired to DB
- [x] 2026-05-23 `feat:` v0.4.19 deployed — calendar UI, settings tabs, onboarding Fixed/Free/Skip
- [x] 2026-06-02 `fix:` v0.4.20 — calendar events not showing in schedule. Root cause: `_prep_cal_events()` double-called `normalize_event()` on already-normalized dicts → all dates empty → all events skipped. Fixed by removing redundant normalize call.
- [x] 2026-06-03 `feat:` v0.4.21 — actionable push notifications for calendar events. Per-user notify_service/notify_target/lead_minutes stored in User model. Scheduler scans calendar events each tick, fires 30 min before. Done/Skip/Snooze buttons. HA event stream handles EVENT_* actions.
- [x] 2026-06-03 `fix:` v0.4.22 — notify service now a dropdown fetched live from HA. `notify.` prefix stripped automatically when calling API.
- [x] 2026-06-03 `feat:` v0.4.23 — real-time event logging. EventLog model, /events/log routes, Log button on every calendar event in Schedule, Today's Log section on Dashboard (HTMX). Notification button taps write real DB entries.
- [x] 2026-06-03 `style:` v0.4.24 — full visual restyle to match House of David. Dark bg #1A1816, gold accent #C9A870, Inter+Syne fonts, gold left-border active nav, square corners.
- [x] 2026-06-03 `fix:` v0.4.25 — all notify functions (daily brief, slot pre/post, calendar events) now read per-user notify_service from DB, fall back to NOTIFY_SERVICE env var. NOTIFY_SERVICE env var in addon options no longer required. Root cause of missed notifications confirmed in logs.
- [x] 2026-06-03 `ops:` Notifications confirmed working end-to-end — test events created, push received on phone with Done/Skip/Snooze buttons.
- [x] 2026-06-03 `ops:` Calendar events pushed for all Dave-action items from daves-worklog.md and projects WORKLOG — Subaru, Ford audit, Max card, Bank Mizrahi, Tel Aviv lead call, Rosh HaAyin install, Savyon, domain, FB/IG.
