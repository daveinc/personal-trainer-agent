import logging
from datetime import datetime, timezone

from sqlalchemy import select, update

from app.database import LocalSession, ExtSession
from app.models import Slot, NotificationLog, Session

logger = logging.getLogger(__name__)


async def handle_action(slot_id: int, verb: str):
    today_str = datetime.now().strftime("%Y-%m-%d")
    notif_type = "pre" if verb in ("start", "skip") else "post"

    async with LocalSession() as db:
        slot = (await db.execute(
            select(Slot).where(Slot.id == slot_id)
        )).scalar_one_or_none()
        if not slot:
            logger.warning(f"Action '{verb}' for unknown slot {slot_id}")
            return

        await db.execute(
            update(NotificationLog)
            .where(
                NotificationLog.slot_id == slot_id,
                NotificationLog.notif_type == notif_type,
                NotificationLog.log_date == today_str,
            )
            .values(action_taken=verb)
        )
        await db.commit()

    logger.info(f"Slot {slot_id} ({slot.label}): {verb}")

    if verb == "done":
        await _log_session(slot_id)


async def handle_event_action(event_title: str, verb: str):
    """Handle Done/Skip/Snooze tapped on a calendar event notification."""
    logger.info(f"Calendar event '{event_title}' action: {verb}")
    from app.routes.event_log import save_event_log
    from app.models import User
    from sqlalchemy import select
    async with LocalSession() as db:
        user = (await db.execute(select(User).order_by(User.id).limit(1))).scalar_one_or_none()
        if user:
            await save_event_log(user.id, event_title, verb)


async def _log_session(slot_id: int):
    if not ExtSession:
        logger.info(f"No MariaDB — session for slot {slot_id} not persisted")
        return
    try:
        async with ExtSession() as db:
            session = Session(slot_id=slot_id, occurred_at=datetime.now(timezone.utc))
            db.add(session)
            await db.commit()
            logger.info(f"Session logged: slot={slot_id}")
    except Exception as e:
        logger.error(f"Session log failed for slot {slot_id}: {e}")
