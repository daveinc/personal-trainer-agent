import logging
import os

import httpx

logger = logging.getLogger(__name__)

_HA_API = "http://supervisor/core/api"


def _token() -> str:
    return os.getenv("SUPERVISOR_TOKEN", "")


def _service() -> str:
    return os.getenv("NOTIFY_SERVICE", "")


async def _call_ha(path: str, payload: dict) -> bool:
    token = _token()
    if not token:
        logger.warning("SUPERVISOR_TOKEN not set — skipping HA call")
        return False
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                f"{_HA_API}/{path}",
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
            )
            if r.status_code not in (200, 201):
                logger.error(f"HA call failed {r.status_code}: {r.text}")
                return False
        return True
    except Exception as e:
        logger.error(f"HA call error: {e}")
        return False


async def notify_pre_slot(slot) -> bool:
    svc = _service()
    if not svc:
        logger.warning("NOTIFY_SERVICE not configured")
        return False
    return await _call_ha(f"services/notify/{svc}", {
        "title": slot.label,
        "message": f"Your {slot.label} starts soon.",
        "data": {
            "tag": f"coach_{slot.id}_pre",
            "actions": [
                {"action": f"coach_{slot.id}_start", "title": "Starting now"},
                {"action": f"coach_{slot.id}_skip",  "title": "Skip"},
            ],
        },
    })


async def notify_post_slot(slot) -> bool:
    svc = _service()
    if not svc:
        return False
    return await _call_ha(f"services/notify/{svc}", {
        "title": slot.label,
        "message": f"How did your {slot.label} go?",
        "data": {
            "tag": f"coach_{slot.id}_post",
            "actions": [
                {"action": f"coach_{slot.id}_done", "title": "Done ✓"},
                {"action": f"coach_{slot.id}_miss", "title": "Didn't do it"},
            ],
        },
    })


async def notify_calendar_event(event: dict, notify_service: str, notify_target: str | None = None) -> bool:
    """
    Send an actionable push notification 30 min before a calendar event.
    event: dict with title, start, end, all_day (from get_calendar_events_with_dt).
    notify_service: e.g. "mobile_app_notepro" (without "notify." prefix).
    """
    if not notify_service:
        logger.warning("notify_service not configured — skipping calendar event notification")
        return False

    start_str = event["start"].strftime("%H:%M") if not event.get("all_day") else "All day"
    message = f"{event['title']} at {start_str}"
    title_key = event["title"][:30]

    payload: dict = {
        "title": "Coach Reminder",
        "message": message,
        "data": {
            "tag": f"coach_event_{title_key}",
            "actions": [
                {"action": f"EVENT_DONE_{title_key}", "title": "✅ Done"},
                {"action": f"EVENT_SKIP_{title_key}", "title": "⏭ Skip"},
                {"action": f"EVENT_SNOOZE_{title_key}", "title": "⏰ Snooze"},
            ],
        },
    }
    if notify_target:
        payload["target"] = notify_target

    return await _call_ha(f"services/notify/{notify_service}", payload)


async def fire_pipeline_event(job_id: int, job_title: str, client: str, stage: str, stage_label: str) -> bool:
    token = _token()
    if not token:
        return False
    payload = {
        "event_type": "coach_pipeline_stage_changed",
        "event_data": {
            "job_id": job_id,
            "title": job_title,
            "client": client or "",
            "stage": stage,
            "stage_label": stage_label,
        },
    }
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(
                f"{_HA_API}/events/coach_pipeline_stage_changed",
                json=payload["event_data"],
                headers={"Authorization": f"Bearer {token}"},
            )
            return r.status_code in (200, 201)
    except Exception as e:
        logger.error(f"Pipeline event fire failed: {e}")
        return False


async def notify_daily_brief() -> bool:
    svc = _service()
    if not svc:
        logger.warning("NOTIFY_SERVICE not configured — daily brief skipped")
        return False

    try:
        from app.ha_calendar import get_today_events
        events = await get_today_events()
    except Exception as e:
        logger.warning(f"Could not fetch calendar events: {e}")
        events = []

    if events:
        lines = []
        for ev in events:
            prefix = f"{ev['time']} " if ev.get("time") else ""
            lines.append(f"• {prefix}{ev['summary']}")
        message = "\n".join(lines)
    else:
        message = "No events scheduled today."

    return await _call_ha(f"services/notify/{svc}", {
        "title": "Good morning, Dave",
        "message": message,
        "data": {
            "tag": "coach_daily_brief",
            "actions": [
                {"action": "coach_brief_ack", "title": "Got it"},
            ],
        },
    })
