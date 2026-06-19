---
name: project-coach-state
description: Current in-progress state of Coach addon as of 2026-05-16 — what was built but not yet committed or wired up
metadata:
  type: project
---

Last known state as of 2026-05-16, v0.4.10 branch, 7 files modified but not committed.

**What was built (uncommitted):**

1. **Quick-log widget on dashboard** — mood slider + weight input that POST to `/log/quick`. Backend endpoint implemented in `ui.py`. Wired to `CheckIn` (mood) and `HealthEntry` (weight). UI exists in `dashboard.html` but styling is inline/rough.

2. **Goals progress API** (`goals.py`) — `/goals/progress` endpoint that calculates % complete per active goal using `GoalProgress` entries.

3. **Trends / correlations** (`trends.py`) — `/category/{name}/trends` stub (hardcoded user_id=1, not wired to real metric data yet). `/insights/correlations` endpoint with mood/energy Pearson correlation logic — real math, but only covers mood×energy so far.

4. **Skills model** (`models.py`) — `Skill` table added (id, name, category, description, enabled). Not migrated yet.

5. **Skills settings routes** (`settings.py`) — `PSYCHOLOGY_SKILLS` list defined. GET/POST `/settings/skills` endpoints. Toggle-enabled logic. Not wired to the Skills tab template yet.

6. **Dashboard data helpers** (`ui.py`) — `get_mood_trend()`, `get_sleep_average()`, `get_active_streaks()` (placeholder) added and passed to template. Template likely not rendering them yet.

**What's incomplete / next:**
- `_settings_skills.html` template needs to render the skills list with toggles
- Skills tab needs to seed default skills into DB on first load
- `/category/{name}/trends` uses hardcoded user_id=1 — needs real user
- `get_active_streaks()` is a stub — needs a Streak model or derived logic
- Quick-log widget unit is hardcoded "kg" — should respect user preference
- Dashboard template not yet rendering mood_trend or sleep_average data
- None of this is committed or deployed

**Why:** Mid-way through the v2 pass (todo.md: "Adding Value" section). Goals/targets, quick-log, trends/observations, and cross-category signals all in flight simultaneously.
