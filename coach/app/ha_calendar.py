import logging
import os
import re
from datetime import datetime, timezone
from typing import Optional

import httpx

CATEGORY = "fitness"

# Categories Coach knows about — used for tag detection
_KNOWN_CATEGORIES = {
    "fitness", "health", "schedule", "finances", "learning",
    "relationships", "checkins", "milestones", "challenges",
}

# Keywords to infer category when no [tag] is present
_CATEGORY_HINTS = {
    "fitness":       ["gym", "workout", "run", "sport", "exercise", "training"],
    "health":        ["doctor", "clinic", "appointment", "health", "רופא", "תור"],
    "finances":      ["payment", "invoice", "bank", "salary", "תשלום", "חשבון"],
    "learning":      ["course", "lesson", "study", "class", "לימוד"],
    "relationships": ["meeting", "lunch", "call", "visit", "פגישה"],
    "schedule":      ["work", "job", "shift", "עבודה", "משמרת"],
}


def normalize_event(raw: dict) -> dict:
    """
    Convert any HA calendar event format into Coach's internal representation.
    Handles: dateTime vs date fields, timezone offsets, [tag] categories,
    keyword inference, all-day events, Hebrew titles, missing fields.
    """
    summary = (raw.get("summary") or raw.get("title") or "Event").strip()

    start_block = raw.get("start") or {}
    end_block = raw.get("end") or {}
    start_raw = start_block.get("dateTime") or start_block.get("date") or ""
    end_raw = end_block.get("dateTime") or end_block.get("date") or ""

    # Strip timezone offset for simple slicing
    start_clean = re.sub(r"([+-]\d{2}:\d{2}|Z)$", "", start_raw)
    end_clean = re.sub(r"([+-]\d{2}:\d{2}|Z)$", "", end_raw)

    is_all_day = "T" not in start_raw
    date = start_clean[:10] if start_clean else ""
    time = start_clean[11:16] if not is_all_day and len(start_clean) > 10 else ""
    end_time = end_clean[11:16] if not is_all_day and len(end_clean) > 10 else ""

    description = (raw.get("description") or "").strip()
    location = (raw.get("location") or "").strip()

    # Detect category from [tag] in description first, then keyword inference
    category = next(
        (t for t in re.findall(r"\[([^\]]+)\]", description.lower()) if t in _KNOWN_CATEGORIES),
        "",
    )
    if not category:
        combined = (summary + " " + description).lower()
        for cat, hints in _CATEGORY_HINTS.items():
            if any(h in combined for h in hints):
                category = cat
                break

    # Strip internal Coach tags from description before displaying
    clean_desc = re.sub(r"\[[^\]]+\]\s*", "", description).strip()

    return {
        "summary":    summary,
        "date":       date,
        "time":       time,
        "end_time":   end_time,
        "is_all_day": is_all_day,
        "category":   category,
        "description": clean_desc,
        "location":   location,
    }


def _calendar_entity() -> str:
    return os.getenv("CALENDAR_ENTITY", "calendar.coach")


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
            f"{_ha_url()}/api/calendars/{_calendar_entity()}",
            headers=_headers(),
            params=params,
        )
        resp.raise_for_status()
        return resp.json()


async def get_today_events() -> list[dict]:
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = now.replace(hour=23, minute=59, second=59, microsecond=0)
    raw = await get_events(start, end)
    return [normalize_event(e) for e in raw]


async def get_week_events() -> list[dict]:
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = (start + timedelta(days=6)).replace(hour=23, minute=59, second=59, microsecond=0)
    raw = await get_events(start, end)
    return [normalize_event(e) for e in raw]


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
        "entity_id": _calendar_entity(),
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
        "entity_id": _calendar_entity(),
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
    payload = {"entity_id": _calendar_entity(), "uid": uid}
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
