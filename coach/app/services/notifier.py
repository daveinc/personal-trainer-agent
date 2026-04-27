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
