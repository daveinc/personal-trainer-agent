import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.ha_calendar import delete_event, update_event
from app.services.ha_client import append_to_calendar_event

logger = logging.getLogger(__name__)
router = APIRouter()

CALENDAR_ENTITY = "calendar.coach"


class CalendarActionRequest(BaseModel):
    uid: str
    action: str          # "done" | "cancel" | "delay"
    summary: str = ""
    start_raw: str = ""
    end_raw: str = ""
    delay_minutes: int = 60


@router.post("/ui/calendar/event/action")
async def calendar_event_action(req: CalendarActionRequest):
    try:
        if req.action == "done":
            await append_to_calendar_event(req.uid, CALENDAR_ENTITY, "Done ✓")
            return JSONResponse({"ok": True, "action": "done"})

        elif req.action == "cancel":
            await delete_event(req.uid)
            return JSONResponse({"ok": True, "action": "cancel"})

        elif req.action == "delay":
            if not req.start_raw or not req.end_raw:
                return JSONResponse({"ok": False, "error": "missing start/end"}, status_code=400)

            start_dt = datetime.fromisoformat(req.start_raw.rstrip("Z").replace("+00:00", ""))
            end_dt = datetime.fromisoformat(req.end_raw.rstrip("Z").replace("+00:00", ""))
            delta = timedelta(minutes=req.delay_minutes)
            await update_event(
                req.uid,
                req.summary,
                start_dt + delta,
                end_dt + delta,
            )
            await append_to_calendar_event(
                req.uid, CALENDAR_ENTITY,
                f"Delayed +{req.delay_minutes}m"
            )
            return JSONResponse({"ok": True, "action": "delay", "minutes": req.delay_minutes})

        else:
            return JSONResponse({"ok": False, "error": "unknown action"}, status_code=400)

    except Exception as e:
        logger.error(f"calendar_event_action error: {e}")
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)
