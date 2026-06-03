import asyncio
import logging
import os
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database import LocalSession
from app.models import Slot, NotificationLog, User

logger = logging.getLogger(__name__)

_daily_brief_sent: str = ""  # tracks date string of last sent brief
_notified_events: set[str] = set()  # event_key → notified today


def _subtract_minutes(time_str: str, minutes: int) -> str:
    h, m = map(int, time_str.split(":"))
    total = max(0, h * 60 + m - minutes)
    return f"{total // 60:02d}:{total % 60:02d}"


async def _get_user_service_map() -> dict[int, str]:
    """Returns {user_id: notify_service} for all users, using DB setting or env var fallback."""
    async with LocalSession() as db:
        users = (await db.execute(select(User))).scalars().all()
    env_svc = os.getenv("NOTIFY_SERVICE", "")
    return {u.id: (u.notify_service or env_svc) for u in users}


async def _check_daily_brief(now: datetime, today_str: str):
    global _daily_brief_sent
    if _daily_brief_sent == today_str:
        return
    # Weekdays only, fire at 07:00
    if now.weekday() >= 5:  # 5=Sat, 6=Sun
        return
    if now.strftime("%H:%M") != "07:00":
        return
    from app.services.notifier import notify_daily_brief
    user_svcs = await _get_user_service_map()
    svc = next(iter(user_svcs.values()), "") if user_svcs else ""
    sent = await notify_daily_brief(notify_svc=svc or None)
    if sent:
        _daily_brief_sent = today_str
        logger.info(f"Daily brief sent for {today_str}")


async def _check_calendar_notifications(now: datetime, today_str: str):
    global _notified_events
    # Clear yesterday's keys at midnight
    if now.hour == 0 and now.minute == 0:
        _notified_events.clear()

    from app.ha_calendar import get_calendar_events_with_dt
    from app.services.notifier import notify_calendar_event

    try:
        events = await get_calendar_events_with_dt()
    except Exception as e:
        logger.error(f"Calendar notification check failed: {e}")
        return

    async with LocalSession() as db:
        users = (await db.execute(select(User))).scalars().all()
        for user in users:
            svc = user.notify_service or os.getenv("NOTIFY_SERVICE", "")
            if not svc:
                continue
            target = user.notify_target or None
            lead = user.notification_lead_minutes or 30

            for event in events:
                if event.get("all_day"):
                    continue
                event_key = f"{user.id}_{event['title']}_{event['start'].isoformat()}"
                if event_key in _notified_events:
                    continue
                # Normalize event start to naive local time for comparison
                start_local = event["start"].astimezone().replace(tzinfo=None)
                notify_at = start_local - timedelta(minutes=lead)
                diff = abs((now - notify_at).total_seconds())
                if diff <= 60:
                    sent = await notify_calendar_event(event, svc, target)
                    if sent:
                        _notified_events.add(event_key)
                        logger.info(f"Calendar notification sent: {event['title']} for user {user.username}")


async def _tick():
    from app.services.notifier import notify_pre_slot, notify_post_slot

    now = datetime.now()
    today_name = now.strftime("%a")
    today_str = now.strftime("%Y-%m-%d")
    now_hm = now.strftime("%H:%M")

    await _check_daily_brief(now, today_str)
    await _check_calendar_notifications(now, today_str)

    user_svcs = await _get_user_service_map()

    async with LocalSession() as db:
        all_slots = (await db.execute(select(Slot))).scalars().all()
        today_slots = [s for s in all_slots if s.days and today_name in s.days.split(",")]

        for slot in today_slots:
            svc = user_svcs.get(slot.user_id) or ""
            # Pre-slot
            if slot.start_time and slot.notify_before:
                notify_at = _subtract_minutes(slot.start_time, slot.notify_before)
                if now_hm == notify_at:
                    exists = (await db.execute(
                        select(NotificationLog).where(
                            NotificationLog.slot_id == slot.id,
                            NotificationLog.notif_type == "pre",
                            NotificationLog.log_date == today_str,
                        )
                    )).scalar_one_or_none()
                    if not exists:
                        sent = await notify_pre_slot(slot, notify_svc=svc or None)
                        if sent:
                            db.add(NotificationLog(
                                slot_id=slot.id, notif_type="pre", log_date=today_str
                            ))
                            try:
                                await db.commit()
                            except IntegrityError:
                                await db.rollback()

            # Post-slot
            if slot.end_time and now_hm == slot.end_time:
                exists = (await db.execute(
                    select(NotificationLog).where(
                        NotificationLog.slot_id == slot.id,
                        NotificationLog.notif_type == "post",
                        NotificationLog.log_date == today_str,
                    )
                )).scalar_one_or_none()
                if not exists:
                    sent = await notify_post_slot(slot, notify_svc=svc or None)
                    if sent:
                        db.add(NotificationLog(
                            slot_id=slot.id, notif_type="post", log_date=today_str
                        ))
                        try:
                            await db.commit()
                        except IntegrityError:
                            await db.rollback()


async def run_scheduler():
    logger.info("Notification scheduler started")
    while True:
        try:
            await _tick()
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
        await asyncio.sleep(60)
