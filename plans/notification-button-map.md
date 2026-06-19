# Coach — Notification Button Map
*What buttons appear, when, and what they write back to the calendar event*
*Written: 2026-06-19 | Updated: 2026-06-19*

---

## Design Principle

Every notification is a question Coach is asking Dave on Claude's behalf.
Every button is Dave's one-tap answer.
The answer gets written back into the calendar event description so Claude reads it at next session start — no separate table, no queue.

Calendar event description format after a button tap:
```
[original event description]
---
📲 Dave @ 14:32: Got everything ✓
```

Multiple taps append in order:
```
[original event description]
---
📲 Dave @ 09:15: Postponed
📲 Dave @ 14:32: Got everything ✓
```

---

## How Project Status Is Determined

`PipelineJob.stage` is the single source of truth. Stage drives which notification fires and which buttons appear.

Stage sequence: `survey → materials → on_site → billing_deposit → billing_submission → billing_approval → done`

**Billing is broken into 3 sub-stages** (40/40/20 model):
- `billing_deposit` — 40% invoice sent at job start
- `billing_submission` — 40% invoice sent when work submitted to standards institute (within 30 days of project start)
- `billing_approval` — 20% invoice sent when standards institute approves

Stage advances automatically when Dave taps a completion button.
Stage stays on blocked/postponed — Dave remains in same stage.

Payment windows are **auto-calculated when a project is created** based on start date:
- `billing_deposit` notification → fires at job start (day 0)
- `billing_submission` reminder → fires day 25 (5-day warning before 30-day deadline)
- `billing_approval` → event-triggered (Dave marks approval received), not time-triggered

---

## Notification Map — Full Button Sets

---

### Stage: `survey`
**Fires:** Day of scheduled survey (30 min before)

> Title: "Survey — [Client Name]"
> Body: "Site visit today. Scope it, price it."

| Button | Writes to calendar | Stage change |
|---|---|---|
| "Survey done — quoting" | "📲 Dave @ HH:MM: Survey done — sending quote" | → `materials` |
| "Need more info first" | "📲 Dave @ HH:MM: Need more info — follow up" | stay |
| "Client wasn't there" | "📲 Dave @ HH:MM: Client no-show — reschedule" | stay |
| "Postponing" | "📲 Dave @ HH:MM: Postponed" | stay |

---

### Stage: `materials`
**Fires:** 1 day before scheduled on-site date

> Title: "Materials — [Job Name]"
> Body: "Got everything you need for [client]?"

| Button | Writes to calendar | Stage change |
|---|---|---|
| "Got everything ✓" | "📲 Dave @ HH:MM: Materials ready ✓" | → `on_site` |
| "Missing parts — ordering" | "📲 Dave @ HH:MM: Missing parts — ordering" | stay |
| "Supplier issue" | "📲 Dave @ HH:MM: Supplier problem — blocked" | stay |
| "Postponing" | "📲 Dave @ HH:MM: Postponed" | stay |

---

### Stage: `on_site`
**Two notifications per day: morning start + evening check-in. Repeats until Dave taps "Done ✓".**

**Start time is scheduled in advance** (set when the on-site calendar event is created).
**End time / ETA is discovered in-session** via the evening check-in — Dave's button tap tells Coach whether to schedule another day.

**Notification A — 30 min before scheduled start time:**
> Title: "On site today — [Client Name]"
> Body: "Starting [job] this morning."

| Button | Writes to calendar | Stage change |
|---|---|---|
| "On my way ✓" | "📲 Dave @ HH:MM: On my way" | stay |
| "Running late" | "📲 Dave @ HH:MM: Running late" | stay |
| "Not going today — rescheduling" | "📲 Dave @ HH:MM: Cancelled today" | stay |

**Notification B — evening check-in:**
Fires at: scheduled end time if set, else scheduled start + estimated duration, else 18:00.
On day 1, this is primarily to discover ETA. On day 2+, it's a completion check.

> Title: "How did [Job] go?"
> Body: "End of day check-in."

| Button | Writes to calendar | What Coach does next | Stage change |
|---|---|---|---|
| "Done ✓" | "📲 Dave @ HH:MM: Job done ✓" | Advance to billing_deposit | → `billing_deposit` |
| "1 more day" | "📲 Dave @ HH:MM: 1 more day" | Creates new on-site event for tomorrow at same start time | stay |
| "2–3 more days" | "📲 Dave @ HH:MM: 2–3 more days" | Creates on-site event for day after tomorrow | stay |
| "⚠️ Problem — discuss in session" | "📲 Dave @ HH:MM: ⚠️ Problem on site" | Flags for next session start | stay |

---

### Stage: `billing_deposit` (40%)
**Fires:** Immediately when job transitions to billing (on-site done)

> Title: "Invoice 40% — [Client Name]"
> Body: "Job done. Send the 40% deposit invoice."

| Button | Writes to calendar | Stage change |
|---|---|---|
| "Invoice sent ✓" | "📲 Dave @ HH:MM: 40% invoice sent" | → `billing_submission` |
| "Already collected upfront" | "📲 Dave @ HH:MM: 40% already collected" | → `billing_submission` |
| "Client asked to delay" | "📲 Dave @ HH:MM: Client delay request" | stay |
| "⚠️ Dispute — discuss next session" | "📲 Dave @ HH:MM: ⚠️ Billing dispute" | stay |

---

### Stage: `billing_submission` (40%)
**Fires:** Day 25 from project start (5-day warning before 30-day submission deadline)

> Title: "Submit + Invoice 40% — [Client Name]"
> Body: "5 days to standards institute deadline. Submit work + send second invoice."

| Button | Writes to calendar | Stage change |
|---|---|---|
| "Submitted + invoice sent ✓" | "📲 Dave @ HH:MM: Submitted to standards institute + 40% invoiced" | → `billing_approval` |
| "Submitted — billing next" | "📲 Dave @ HH:MM: Submitted — billing soon" | stay |
| "Not ready — delay risk" | "📲 Dave @ HH:MM: ⚠️ Submission at risk — discuss" | stay |
| "Payment received ✓" | "📲 Dave @ HH:MM: 40% payment received" | stay (wait for approval) |

---

### Stage: `billing_approval` (20%)
**Fires:** When Dave marks standards institute approval received (event-triggered, not time-triggered)

> Title: "Final Invoice 20% — [Client Name]"
> Body: "Approval received. Send the final 20% invoice."

| Button | Writes to calendar | Stage change |
|---|---|---|
| "Invoice sent ✓" | "📲 Dave @ HH:MM: Final 20% invoice sent" | stay (wait for payment) |
| "Payment received ✓ — job closed" | "📲 Dave @ HH:MM: 20% received — job closed ✓" | → `done` |
| "Client disputing final" | "📲 Dave @ HH:MM: ⚠️ Final payment dispute" | stay |

**Approval trigger:** Dave taps "Standards institute approved" on a dedicated calendar event Coach creates at project start, timed ~45 days from start as a placeholder.

---

### Stage: `done`
No scheduled notifications. Terminal stage.
Claude reads all calendar entries at session start and updates the project file.

---

## ⚠️ Flag Handling

Any button tap containing ⚠️ must be handled **before anything else** at the next session start:
- Claude scans calendar events for unprocessed ⚠️ entries
- Surfaces them as the first item in the session opening, ahead of financial status or weekly rhythm
- Resolves each one (updates project file, escalates, or logs decision) before proceeding

---

## How Coach Determines Which Notification to Fire

Scheduler runs each tick, checks all active `PipelineJob` rows:

```
survey          → fire on survey_date (from calendar event)
materials       → fire 1 day before on_site_date
on_site         → fire A: 30min before start_time
                   fire B: start_time + estimated_duration + 30min (fallback: 18:00 day 1)
billing_deposit → fire immediately on stage entry (one-time)
billing_submission → fire on project_start + 25 days
billing_approval → fire when approval_event tapped (event-triggered)
done            → no notifications
```

Don't fire if already fired today for same job+stage (check `EventLog`).

---

## Calendar Event Write-Back — Technical

When Dave taps a button, Coach calls `ha_config_set_calendar_event` to update the event:
1. Read current event description
2. Append `\n---\n📲 Dave @ {HH:MM}: {button_label}`
3. Write back

Calendar: `calendar.coach` (UTC+3 / Asia/Jerusalem)

---

## What Claude Does at Session Start

1. Call `ha_config_get_calendar_events` for `calendar.coach` — past 7 days + next 30 days
2. Scan all event descriptions for `📲 Dave @` lines not yet processed
3. Handle ⚠️ flags first — before opening assessment
4. For each clean update: match to `PipelineJob` by title, update project file, advance stage if needed, update `_index.md` + WORKLOG
5. Surface summary of what was processed in session opening

---

## Open Items — Dave to Confirm

- [ ] Private client billing model (Rosh HaAyin style: deposit + balance) — does this system also handle simple 2-stage billing, or is 40/40/20 the only model for now?

## Resolved
- ✅ Billing: 40/40/20 model confirmed — deposit / submission to standards institute / approval
- ✅ On-site start time: scheduled in advance via calendar event
- ✅ ETA: discovered via evening check-in buttons ("Done ✓" / "1 more day" / "2–3 more days" / "⚠️ Discuss") — Coach auto-schedules next day based on response
