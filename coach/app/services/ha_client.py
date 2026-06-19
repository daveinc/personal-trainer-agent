import logging
import os
from datetime import datetime, timezone, timedelta

import httpx

logger = logging.getLogger(__name__)
_HA_API = "http://supervisor/core/api"

_TZ_OFFSET = timedelta(hours=3)  # Asia/Jerusalem (UTC+3)


async def get_ha_state(entity_id: str) -> dict | None:
    token = os.getenv("SUPERVISOR_TOKEN", "")
    if not token or not entity_id:
        return None
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(
                f"{_HA_API}/states/{entity_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            if r.status_code == 200:
                return r.json()
    except Exception as e:
        logger.debug(f"HA state fetch failed for {entity_id}: {e}")
    return None


async def append_to_calendar_event(
    event_uid: str,
    calendar_entity: str,
    note: str,
) -> bool:
    """
    Append a Dave field-response line to a calendar event description.

    Format appended: \\n---\\n📲 Dave @ HH:MM: {note}
    If the separator already exists (from a previous tap), only appends the new line.

    Uses GET /api/calendars/{calendar_entity}/{event_uid} to fetch current data,
    then PUT to update the description.

    calendar_entity: e.g. "calendar.coach"
    event_uid: the HA calendar event uid (stored on JobStep.calendar_event_uid)
    note: the human-readable label for the button tapped
    """
    token = os.getenv("SUPERVISOR_TOKEN", "")
    if not token:
        logger.warning("SUPERVISOR_TOKEN not set — skipping calendar write-back")
        return False

    # Time in Asia/Jerusalem (UTC+3)
    now_local = datetime.now(timezone.utc) + _TZ_OFFSET
    time_str = now_local.strftime("%H:%M")
    append_line = f"📲 Dave @ {time_str}: {note}"

    headers = {"Authorization": f"Bearer {token}"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Fetch current event via /api/calendars/{entity}/{uid}
            get_url = f"{_HA_API}/calendars/{calendar_entity}/{event_uid}"
            r = await client.get(get_url, headers=headers)

            if r.status_code == 200:
                event_data = r.json()
            elif r.status_code == 404:
                # HA may not support GET by UID — fall back to a no-op with a warning
                logger.warning(
                    f"Calendar event {event_uid} not found on {calendar_entity} "
                    f"(404) — write-back skipped. Note: {append_line}"
                )
                return False
            else:
                logger.error(
                    f"Calendar event fetch failed {r.status_code}: {r.text}"
                )
                return False

            current_desc = event_data.get("description") or ""

            # Build updated description
            if "\n---\n" in current_desc:
                new_desc = current_desc + f"\n{append_line}"
            else:
                new_desc = current_desc + f"\n---\n{append_line}"

            # Patch the event back — HA REST API uses PATCH or PUT on the same endpoint
            update_payload = {"description": new_desc}
            p = await client.patch(get_url, json=update_payload, headers=headers)
            if p.status_code not in (200, 201, 204):
                # Try PUT as fallback
                p = await client.put(get_url, json={**event_data, "description": new_desc}, headers=headers)
                if p.status_code not in (200, 201, 204):
                    logger.error(
                        f"Calendar write-back failed {p.status_code}: {p.text}"
                    )
                    return False

            logger.info(
                f"Calendar write-back OK: {calendar_entity}/{event_uid} ← {append_line}"
            )
            return True

    except Exception as e:
        logger.error(f"Calendar write-back error: {e}")
        return False


async def create_calendar_event(
    calendar_entity: str,
    summary: str,
    start_dt: datetime,
    end_dt: datetime,
    description: str = "",
) -> bool:
    """
    Create a new calendar event on calendar_entity.
    start_dt and end_dt must be timezone-aware datetimes.
    Returns True on success.
    """
    token = os.getenv("SUPERVISOR_TOKEN", "")
    if not token:
        logger.warning("SUPERVISOR_TOKEN not set — skipping calendar event creation")
        return False

    payload = {
        "summary": summary,
        "dtstart": start_dt.isoformat(),
        "dtend": end_dt.isoformat(),
        "description": description,
    }
    headers = {"Authorization": f"Bearer {token}"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                f"{_HA_API}/calendars/{calendar_entity}",
                json=payload,
                headers=headers,
            )
            if r.status_code in (200, 201):
                logger.info(f"Calendar event created: {calendar_entity} — {summary}")
                return True
            else:
                logger.error(f"Calendar event creation failed {r.status_code}: {r.text}")
                return False
    except Exception as e:
        logger.error(f"Calendar event creation error: {e}")
        return False
