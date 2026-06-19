# Coach API Map
**Stack:** FastAPI + Jinja2 + HTMX | **Base:** HA ingress (no fixed port, path-prefix via `X-Ingress-Path`) | **Auth:** Cookie `uid` set on login, `X-Remote-User-Name` header for HA ingress auto-login

---

## Auth

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| POST | `/auth/login` | None | Form: `username`. Creates user if not exists. Sets `uid` cookie. |
| GET | `/auth/logout` | Cookie | Clears `uid` cookie. |

---

## UI Pages (HTML, HTMX)

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| GET | `/ui/login` | None | Login page |
| GET | `/ui/dashboard` | Cookie | Main dashboard |
| GET | `/ui/onboarding` | Cookie | Onboarding wizard (step 1+2) |
| GET | `/ui/profile` | Cookie | User profile |

---

## Schedule

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| GET | `/ui/schedule` | Cookie | Schedule view. Query: `selected={slot_id}`, `edit={slot_id}` |
| POST | `/ui/schedule/slot/add` | Cookie | Form: `category`, `label`, `schedule_type`, `days[]`, `start_time`, `end_time`, `notify_before` |
| POST | `/ui/schedule/slot/{slot_id}/save` | Cookie | Same fields as add |
| POST | `/ui/schedule/slot/{slot_id}/delete` | Cookie | Deletes slot + its attributes |
| POST | `/ui/schedule/slot/{slot_id}/attribute/add` | Cookie | Form: `attribute_name`, `unit` |
| POST | `/ui/schedule/slot/{slot_id}/attribute/{attr_id}/delete` | Cookie | |
| POST | `/ui/schedule/category/{category}/set-reminder` | Cookie | Form: `notify_before` (minutes) |
| POST | `/ui/schedule/category/{category}/clear-reminders` | Cookie | Clears `notify_before` on all category slots |

---

## Check-ins

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| GET | `/ui/checkins` | Cookie | Last 30 entries, streak, week calendar |
| POST | `/ui/checkins/log` | Cookie | Form: `mood` (1-10), `energy` (1-10), `notes`. Creates HA calendar event. |
| POST | `/ui/checkins/{entry_id}/delete` | Cookie | |

---

## Health

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| GET | `/ui/health` | Cookie | Query: `expand={metric}`, `edit_appt={id}` |
| POST | `/ui/health/entry/log` | Cookie | Form: `metric`, `value`, `value2` (e.g. BP systolic/diastolic) |
| POST | `/ui/health/entry/{entry_id}/delete` | Cookie | Form: `metric` (for redirect) |
| POST | `/ui/health/appointment/add` | Cookie | Form: `title`, `doctor`, `location`, `appt_date`, `appt_time`, `notes` |
| POST | `/ui/health/appointment/{appt_id}/save` | Cookie | Same fields |
| POST | `/ui/health/appointment/{appt_id}/delete` | Cookie | |

---

## Finances

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| GET | `/ui/finances` | Cookie | Income/expense lines + Spent pulse |
| POST | `/ui/finances/line/add` | Cookie | Form: `label`, `line_type` (income/expense), `amount` |
| POST | `/ui/finances/line/{line_id}/edit` | Cookie | Form: `label`, `amount` |
| POST | `/ui/finances/line/{line_id}/delete` | Cookie | |
| POST | `/ui/finances/goal/save` | Cookie | Form: `savings_target` |

---

## Pipeline (Business Jobs)

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| GET | `/ui/pipeline` | Cookie | Kanban board, by stage, total active value |
| POST | `/ui/pipeline/add` | Cookie | Form: `title`, `client`, `location`, `stage`, `value`, `due_date`, `notes` |
| GET | `/ui/pipeline/{job_id}` | Cookie | Job detail with notes |
| POST | `/ui/pipeline/{job_id}/stage` | Cookie | Form: `stage`. Fires HA event on stage change. |
| POST | `/ui/pipeline/{job_id}/advance` | Cookie | Advances to next stage. Fires HA event. |
| POST | `/ui/pipeline/{job_id}/note` | Cookie | Form: `body` |
| POST | `/ui/pipeline/{job_id}/archive` | Cookie | Sets `is_active=False` |

---

## Goals

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| GET | `/ui/goals` | Cookie | All goals with progress |
| POST | `/ui/goals/add` | Cookie | Form: `title`, `category`, `metric`, `target_value`, `target_unit`, `start_value`, `total_steps`, `start_date`, `deadline`, `notes` |
| POST | `/ui/goals/{goal_id}/progress` | Cookie | Form: `steps` (int), `note`. Auto-completes if steps >= total_steps. |
| POST | `/ui/goals/{goal_id}/complete` | Cookie | Marks achieved today |
| POST | `/ui/goals/{goal_id}/reopen` | Cookie | Clears achieved_at, is_active=True |
| POST | `/ui/goals/{goal_id}/delete` | Cookie | Deletes goal + all progress |
| GET | `/goals/progress` | Cookie | **JSON API** — returns active goals with percent_complete |

---

## Settings

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| GET | `/ui/settings` | Cookie | Main settings shell (tab container) |
| GET | `/ui/settings/preferences` | Cookie | Preferences partial |
| POST | `/ui/settings/preferences/save` | Cookie | Form: `display_name`, `currency`, `unit_distance`, `unit_weight`, `week_start`, `steps_entity`, `health_metrics[]` |
| GET | `/ui/settings/notifications` | Cookie | Notifications partial |
| GET | `/ui/settings/categories` | Cookie | Category schedule settings |
| POST | `/ui/settings/categories/save` | Cookie | Form: `type_{slug}`, `days_{slug}[]`, `start_{slug}`, `end_{slug}` for each category |
| GET | `/ui/settings/skills` | Cookie | Psychology skills tab |
| GET | `/settings/skills` | Cookie | **JSON API** — list all skills |
| GET | `/settings/skills/defaults` | None | **JSON API** — default skill list |
| POST | `/settings/skills` | Cookie | **JSON API** — toggle skill enabled. Form: `id` |
| GET | `/ui/settings/db` | Cookie | DB stats (SQLite size, log counts) |
| POST | `/ui/settings/delete-user-logs` | Cookie | Form: `user_id` |
| POST | `/ui/settings/delete-user` | Cookie | Form: `user_id` |
| POST | `/ui/settings/wipe-logs` | Cookie | Deletes ALL workout logs |
| GET | `/ui/settings/backup` | Cookie | Downloads `coach_backup.db` |
| POST | `/ui/settings/restore` | Cookie | File upload: replaces SQLite DB |
| GET | `/ui/settings/calendar` | Cookie | Calendar event list. Query: `user_filter` |
| POST | `/ui/settings/calendar-config/add` | Cookie | Form: `entity_id`, `label`, `default_category`, `ignore_keywords` |
| POST | `/ui/settings/calendar-config/{config_id}/delete` | Cookie | |
| GET | `/ui/settings/calendar/edit` | Cookie | Edit event form. Query: `uid` |
| POST | `/ui/settings/calendar/edit` | Cookie | Form: `uid`, `title`, `date`, `start_time`, `duration`, `description` |
| POST | `/ui/settings/calendar/delete` | Cookie | Form: `uid` |
| GET | `/ui/settings/calendar/backup` | Cookie | Downloads calendar events JSON |
| POST | `/ui/settings/calendar/restore` | Cookie | File upload: JSON events. Form: `replace` (bool) |

---

## Webhook (HA → Coach)

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| POST | `/api/webhook` | None | JSON: `{"action": "coach_{slot_id}_{verb}"}`. Verb: start/skip/done/miss |

---

## Notes

- **Pipeline stages:** `marketing → quote → deposit → active → complete → lost`
- **HA calendar events** created on: checkin log, schedule reminders
- **Onboarding gate:** middleware redirects incomplete users to `/ui/onboarding`
- **HA ingress:** `X-Ingress-Path` header sets root_path; `X-Remote-User-Name` auto-logs in HA user
