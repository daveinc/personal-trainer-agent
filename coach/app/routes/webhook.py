import logging
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/api/webhook")
async def ha_webhook(request: Request):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "invalid json"}, status_code=400)

    action = data.get("action", "")
    logger.info(f"Webhook: action={action!r}")

    if not action.startswith("coach_"):
        return JSONResponse({"ok": True})

    # action format: coach_{slot_id}_{verb}
    parts = action.split("_")
    if len(parts) != 3:
        logger.warning(f"Unexpected action format: {action!r}")
        return JSONResponse({"ok": True})

    try:
        slot_id = int(parts[1])
    except ValueError:
        return JSONResponse({"ok": True})

    verb = parts[2]  # start | skip | done | miss

    from app.routes.action_router import handle_action
    await handle_action(slot_id, verb)

    return JSONResponse({"ok": True})
