import logging
import os
from datetime import datetime, timezone
from typing import Optional

import httpx

CALENDAR_ENTITY = "calendar.coach"
logger = logging.getLogger(__name__)


def _ha_url() -> str:
    user_url = os.getenv("HA_URL", "").rstrip("/")
    if user_url:
        if not user_url.startswith(("http://", "https://")):
            user_url = "http://" + user_url
        return user_url
    if os.getenv("SUPERVISOR_TOKEN"):
        return "http://supervisor/core"
    return "http://homeassistant:8123"


def _token() -> str:
    return os.getenv("HA_TOKEN") or os.getenv("SUPERVISOR_TOKEN", "")


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_token()}",
        "Content-Type": "application/json",
    }


def _fmt(dt: datetime) -> str:
    """Format datetime for HA API. Naive datetimes passed as-is (HA treats as local)."""
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


async def get_events(start: datetime, end: datetime) -> list[dict]:
    params = {"start": _fmt(start), "end": _fmt(end)}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{_ha_url()}/api/calendars/{CALENDAR_ENTITY}",
            headers=_headers(),
            params=params,
        )
        resp.raise_for_status()
        return resp.json()


async def get_today_events() -> list[dict]:
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = now.replace(hour=23, minute=59, second=59, microsecond=0)
    return await get_events(start, end)


async def get_week_events() -> list[dict]:
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = (start + timedelta(days=6)).replace(hour=23, minute=59, second=59, microsecond=0)
    return await get_events(start, end)


async def get_month_events() -> list[dict]:
    import calendar as cal
    now = datetime.now(timezone.utc)
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_day = cal.monthrange(now.year, now.month)[1]
    end = now.replace(day=last_day, hour=23, minute=59, second=59, microsecond=0)
    return await get_events(start, end)


async def get_all_events() -> list[dict]:
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=365)
    end = now + timedelta(days=365)
    return await get_events(start, end)


async def update_event(
    uid: str,
    summary: str,
    start: datetime,
    end: datetime,
    description: Optional[str] = None,
) -> None:
    payload: dict = {
        "entity_id": CALENDAR_ENTITY,
        "uid": uid,
        "summary": summary,
        "start_date_time": _fmt(start),
        "end_date_time": _fmt(end),
    }
    if description is not None:
        payload["description"] = description
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{_ha_url()}/api/services/calendar/update_event",
            headers=_headers(),
            json=payload,
        )
        resp.raise_for_status()


async def create_event(
    summary: str,
    start: datetime,
    end: datetime,
    description: Optional[str] = None,
    category: Optional[str] = None,
    username: Optional[str] = None,
) -> dict:
    tags = ""
    if category:
        tags += f"[{category}]"
    if username:
        tags += f"[{username.lower()}]"
    desc = f"{tags} {description}".strip() if tags else description
    payload: dict = {
        "entity_id": CALENDAR_ENTITY,
        "summary": summary,
        "start_date_time": _fmt(start),
        "end_date_time": _fmt(end),
    }
    if desc:
        payload["description"] = desc
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{_ha_url()}/api/services/calendar/create_event",
            headers=_headers(),
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()


async def delete_event(uid: str) -> None:
    payload = {"entity_id": CALENDAR_ENTITY, "uid": uid}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{_ha_url()}/api/services/calendar/delete_event",
            headers=_headers(),
            json=payload,
        )
        resp.raise_for_status()


async def check_connection() -> bool:
    url = f"{_ha_url()}/api/calendars"
    logger.info(f"HA check → {url} | supervisor: {bool(os.getenv('SUPERVISOR_TOKEN'))} | token: {bool(os.getenv('HA_TOKEN'))}")
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(url, headers=_headers())
            logger.info(f"HA response: {resp.status_code}")
            return resp.status_code == 200
    except Exception as e:
        logger.error(f"HA check failed: {e}")
        return False
