# Coach — Field Loop Spec
*Phase 1 + Phase 2: Fix buttons + Dynamic per-stage notifications + Pending message queue*
*Written: 2026-06-19*

---

## Problem

Current system sends the same Done/Skip/Snooze buttons for every calendar event regardless of what the event is about. The event listener is wired (`ha_events.py`) but is fragile — stream drops and reconnects silently, and the snooze re-fire was never implemented. Most critically: there is no return path. Dave taps a button in the field → action logs to `EventLog` → nothing surfaces to Claude at next session start.

---

## Vision

A closed loop:
1. Claude creates a job in Coach with steps per stage
2. Coach fires a notification when a step is due — with buttons specific to that stage
3. Dave taps a button in the field (or types a note)
4. Coach queues the response as a `PendingMessage`
5. Next session start → Claude reads pending messages, updates project files, no manual catch-up needed

---

## Phase 1 — Fix the Foundation

### 1.1 Fix event stream reliability

**File:** `app/services/ha_events.py`

- Add exponential backoff on reconnect (currently flat 5s)
- Log disconnect/reconnect events at WARNING level so they appear in addon logs
- Add `asyncio.shield()` on `handle_action` calls so a slow DB write can't kill the stream

### 1.2 Add `JobStep` model

**File:** `app/models.py`

```python
class JobStep(Base):
    __tablename__ = "job_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("pipeline_jobs.id"), nullable=False)
    stage: Mapped[str] = mapped_column(String(32), nullable=False)
    # survey | materials | on_site | billing | done
    label: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    # pending | done | skipped | blocked | snoozed
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)
```

### 1.3 Add `PendingMessage` model

**File:** `app/models.py`

```python
class PendingMessage(Base):
    __tablename__ = "pending_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("pipeline_jobs.id"), nullable=True)
    step_id: Mapped[int] = mapped_column(Integer, ForeignKey("job_steps.id"), nullable=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    # "notification_tap" | "manual"
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    # done | skipped | blocked | materials_missing | billing_needed | etc.
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
```

### 1.4 Update pipeline stages

**File:** `app/models.py` — replace `PIPELINE_STAGES`

```python
PIPELINE_STAGES = ["survey", "materials", "on_site", "billing", "done"]
PIPELINE_STAGE_LABELS = {
    "survey":    "Survey / Quote",
    "materials": "Materials",
    "on_site":   "On Site",
    "billing":   "Billing",
    "done":      "Done",
}
```

### 1.5 Stage-specific button sets

**File:** `app/services/notifier.py` — new function

```python
STAGE_BUTTONS = {
    "survey": [
        {"action": "STEP_{step_id}_DONE",     "title": "Survey done ✓"},
        {"action": "STEP_{step_id}_BLOCKED",  "title": "Can't get there"},
        {"action": "STEP_{step_id}_SNOOZE",   "title": "Postpone"},
    ],
    "materials": [
        {"action": "STEP_{step_id}_DONE",     "title": "Got everything ✓"},
        {"action": "STEP_{step_id}_MISSING",  "title": "Something missing"},
        {"action": "STEP_{step_id}_SNOOZE",   "title": "Postpone"},
    ],
    "on_site": [
        {"action": "STEP_{step_id}_DONE",     "title": "Job done ✓"},
        {"action": "STEP_{step_id}_PROGRESS", "title": "Still going"},
        {"action": "STEP_{step_id}_BLOCKED",  "title": "Problem on site"},
    ],
    "billing": [
        {"action": "STEP_{step_id}_DONE",     "title": "Payment received ✓"},
        {"action": "STEP_{step_id}_INVOICED", "title": "Invoice sent, waiting"},
        {"action": "STEP_{step_id}_MISSING",  "title": "Need to invoice"},
    ],
}
```

Action format: `STEP_{step_id}_{verb}` — parsed in `ha_events.py`.

### 1.6 Update `ha_events.py` to handle `STEP_*` actions

Add a branch for `STEP_*` actions alongside existing `coach_*` and `EVENT_*` branches:

```python
elif action.startswith("STEP_"):
    # format: STEP_{step_id}_{verb}
    parts = action.split("_", 2)
    if len(parts) == 3:
        step_id = int(parts[1])
        verb = parts[2].lower()
        await handle_step_action(step_id, verb)
```

### 1.7 `handle_step_action` in `action_router.py`

```python
async def handle_step_action(step_id: int, verb: str):
    async with LocalSession() as db:
        step = await db.get(JobStep, step_id)
        if not step:
            return
        step.status = verb  # done | blocked | missing | progress | invoiced | snoozed
        step.updated_at = datetime.now(timezone.utc)

        # write pending message for Claude
        user = (await db.execute(select(User).limit(1))).scalar_one_or_none()
        if user:
            msg = PendingMessage(
                user_id=user.id,
                job_id=step.job_id,
                step_id=step.id,
                source="notification_tap",
                action=verb,
            )
            db.add(msg)

        await db.commit()

    # if done → auto-advance job stage (call existing stage advance logic)
    if verb == "done":
        await _advance_job_stage(step.job_id)
```

---

## Phase 2 — Session Start Integration

### 2.1 `/api/v1/pending-messages` endpoint

**New file:** `app/routes/pending_messages.py`

```
GET /api/v1/pending-messages
```

Returns all unread `PendingMessage` rows, formatted for Claude:

```json
[
  {
    "id": 12,
    "job": "Rosh HaAyin Water Deterrent",
    "stage": "materials",
    "step": "Buy solenoid + head + box",
    "action": "missing",
    "notes": null,
    "created_at": "2026-06-19T14:32:00Z"
  }
]
```

```
POST /api/v1/pending-messages/mark-read
body: { "ids": [12, 13] }
```

Marks messages read after Claude processes them.

### 2.2 Session start hook update

**File:** `superceo/CLAUDE.md` and/or global session start hook

After this is built, session start reads:
```
GET http://hq.local:8099/api/v1/pending-messages
```
via HA MCP or direct HTTP call. If messages exist → Claude processes them before anything else → marks them read.

**NOT done until Phase 2 is deployed and tested.** Do not update CLAUDE.md before Phase 2 is live.

### 2.3 Job step creation — Claude writes to Coach

When Claude creates or updates a project in a superceo session, it also writes job steps to Coach via:

```
POST /api/v1/jobs/{job_id}/steps
body: { "stage": "materials", "label": "Buy solenoid + head + box", "scheduled_at": "2026-06-20T09:00:00Z" }
```

This closes the loop: Claude writes steps → Coach fires notifications → Dave responds → Claude reads at next session start.

---

## Build Order for Worker

- [x] 1. `models.py` — add `JobStep` + `PendingMessage`, update `PIPELINE_STAGES` *(done 2026-06-19)*
- [x] 2. `notifier.py` — add `STAGE_BUTTONS` + `notify_job_step()` function *(done 2026-06-19)*
- [x] 3. `ha_events.py` — add `STEP_*` handler + exponential backoff on reconnect *(done 2026-06-19)*
- [x] 4. `action_router.py` — add `handle_step_action()` + `_advance_job_stage()` *(done 2026-06-19)*
- [x] 5. `routes/pending_messages.py` — new route file *(done 2026-06-19, renamed to _removed 2026-06-19)*
- [x] 6. `main.py` — wire new router *(done 2026-06-19, removed 2026-06-19)*
- [x] 7. DB migration — `Base.metadata.create_all()` confirmed; `job_steps` table auto-created at startup *(done 2026-06-19)*
- [x] 8. **Architecture correction** — replace `PendingMessage` return path with calendar event write-back *(done 2026-06-19 — see correction notes below)*
- [ ] 9. Smoke test — create a test job step with `calendar_event_uid` set, fire notification manually, tap button, confirm calendar event description updated with `📲 Dave @ HH:MM: ...` line *(pending — Dave to verify after deploy)*

---

## Out of Scope (Phase 3+)

- WORKLOG.md → Coach calendar migration
- Session start reading Coach schedule instead of WORKLOG.md
- Worker module (Block 3)
- Admin UI for job steps in Coach portal

---

## Files to Change

| File | Change |
|---|---|
| `app/models.py` | Add `JobStep`, `PendingMessage`, update `PIPELINE_STAGES` |
| `app/services/notifier.py` | Add `STAGE_BUTTONS`, `notify_job_step()` |
| `app/services/ha_events.py` | Add `STEP_*` handler, fix reconnect backoff |
| `app/routes/action_router.py` | Add `handle_step_action()`, `_advance_job_stage()` |
| `app/routes/pending_messages.py` | New file — GET + POST mark-read |
| `app/main.py` | Wire pending_messages router |

---

## Implementation Notes
*Written: 2026-06-19 — Phase 1 complete + Architecture correction applied*

> **⚠️ Architecture correction (2026-06-19):** PendingMessage return path rejected by Dave — the `PendingMessage` table was built as spec'd, but the approved return path is **calendar event write-back** (see `notification-button-map.md`). When Dave taps a button, Coach appends to the calendar event description (`📲 Dave @ HH:MM: ...`). Claude reads this at session start via `ha_config_get_calendar_events`. The `/api/v1/pending-messages` endpoint has been **removed** (renamed to `pending_messages_removed.py`). Phase 2.2 session start hook should use calendar event scanning, not the pending-messages API.

### Correction — what changed in v0.4.26

**`app/models.py`**
- `PendingMessage` class removed entirely
- `JobStep` model gains `calendar_event_uid: Mapped[str]` (nullable, String 256) — set when the calendar event is created for this step; used by `handle_step_action` to write back without embedding uid in the action string

**`app/services/ha_client.py`**
- `append_to_calendar_event(event_uid, calendar_entity, note)` added — fetches current event via `GET /api/calendars/{entity}/{uid}`, appends `📲 Dave @ HH:MM: {note}` to description, writes back via PATCH (PUT fallback). Time in UTC+3 (Asia/Jerusalem).
- `create_calendar_event(calendar_entity, summary, start_dt, end_dt, description)` added — creates new event via `POST /api/calendars/{entity}`. Used by on-site day continuation.

**`app/routes/action_router.py`**
- `PendingMessage` import removed
- `VERB_LABELS` dict added — maps action verb → human-readable button label
- `_verb_to_label(verb)` helper added
- `handle_step_action()` rewritten: updates `step.status`, calls `append_to_calendar_event` with `step.calendar_event_uid` (logs a warning and skips if uid not set), calls `_advance_job_stage` on `verb == "done"`, calls `_schedule_next_onsite_day` for `1_more_day` / `2_3_more_days`
- `_schedule_next_onsite_day(step_id, job_id, scheduled_at, days_ahead)` added — creates a new `calendar.coach` event at original start time + `days_ahead` days, 8-hour default duration

**`app/routes/pending_messages.py`**
- Renamed to `pending_messages_removed.py` — route is dead, file preserved for reference

**`app/main.py`**
- `pending_messages_router` import and `app.include_router` call removed

**Version:** bumped to `0.4.26` in `config.json` and `Dockerfile`

### What was changed

**`app/models.py`**
- `PIPELINE_STAGES` updated from `["marketing", "offer", "design", "install", "paid"]` to `["survey", "materials", "on_site", "billing", "done"]` with matching `PIPELINE_STAGE_LABELS`. Note: existing `PipelineJob` rows in the DB will have the old stage values — Dave should manually update any active jobs via the pipeline UI after deploy.
- `JobStep` model added with `__tablename__ = "job_steps"` — uses `Base`, auto-created by `Base.metadata.create_all()` at startup.
- `PendingMessage` model added with `__tablename__ = "pending_messages"` — uses `Base`, auto-created at startup.

**`app/services/notifier.py`**
- `STAGE_BUTTONS` dict added at module level. Action strings use `{step_id}` as a placeholder that gets replaced at runtime.
- `notify_job_step(step, job_title, notify_svc, notify_target)` added. Pulls buttons from `STAGE_BUTTONS` by `step.stage`, falls back to a generic Done+Postpone pair for any unlisted stage (e.g., `"done"` stage which normally wouldn't get a notification). Strips `notify.` prefix automatically.

**`app/services/ha_events.py`**
- `asyncio.shield()` applied to all three handler calls (`handle_action`, `handle_event_action`, `handle_step_action`) so a slow DB write cannot cancel the stream.
- Exponential backoff added to `run_event_listener`: starts at 5s, doubles each reconnect attempt, caps at 60s. Resets to 5s on clean disconnect (stream ended without exception).
- Disconnect/reconnect events now log at WARNING level.
- `STEP_*` branch added: splits on `_` with maxsplit=2 to support multi-word verbs, converts verb to lowercase before passing to `handle_step_action`.

**`app/routes/action_router.py`**
- Added imports for `JobStep`, `PendingMessage`, `User`, `PipelineJob`, `PIPELINE_STAGES`.
- `handle_step_action(step_id, verb)` added: updates `step.status`, writes a `PendingMessage`, commits. Calls `_advance_job_stage` only when `verb == "done"`.
- `_advance_job_stage(job_id)` added: looks up job, advances one stage in `PIPELINE_STAGES` sequence, fires `fire_pipeline_event` for any existing HA automations listening on `coach_pipeline_stage_changed`. Already-at-final-stage is a no-op with an info log.

**`app/routes/pending_messages.py`** (new file)
- `GET /api/v1/pending-messages` — returns unread messages ordered oldest-first, joined with job title and step label/stage. Uses individual `db.get()` calls per message (not a join) — fine for expected low volume.
- `POST /api/v1/pending-messages/mark-read` — accepts `{"ids": [1,2,3]}`, uses `PendingMessage.id.in_(body.ids)` to batch-load then marks `read=True`. Returns `{"marked": N}`.

**`app/main.py`**
- `pending_messages_router` imported and wired with `app.include_router(pending_messages_router)`.

### DB migration
No Alembic required. `database.py` line 98 runs `Base.metadata.create_all` at startup, which picks up all new models that import `Base`. Both `JobStep` and `PendingMessage` use `Base` — tables will be created on first startup after deploy.

### Decisions made
- `STEP_` parser uses `split("_", 2)` (maxsplit=2) to handle verbs like `MATERIALS_MISSING` if those get added later. Current verbs are all single words so this is forward-safe.
- `_advance_job_stage` fires `fire_pipeline_event` for HA side-effects — consistent with how `pipeline_advance` in `pipeline.py` already works.
- `notify_job_step` has a fallback button set for unrecognized stages rather than silently no-op, to avoid silent failures if a step in a new/custom stage triggers a notification.

### Dave needs to verify manually
1. After deploy: existing `PipelineJob` rows will still have old stage values (`marketing`, `offer`, etc.). Update active jobs via the pipeline UI to use new stages.
2. Smoke test: create a job step via direct DB insert or future API (Phase 2.3), fire `notify_job_step` manually, tap a button, confirm a `PendingMessage` row appears, confirm `GET /api/v1/pending-messages` returns it.
3. Check pipeline UI (`/ui/pipeline`) still renders correctly — it reads `PIPELINE_STAGES` from `models.py` which has changed. The kanban columns will now show Survey/Materials/On Site/Billing/Done instead of the old labels.
