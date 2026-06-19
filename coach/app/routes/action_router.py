import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, update

from app.database import LocalSession, ExtSession
from app.models import Slot, NotificationLog, Session, JobStep, User, PipelineJob, PIPELINE_STAGES

logger = logging.getLogger(__name__)

# Maps action verb → human-readable button label for calendar write-back
VERB_LABELS: dict[str, str] = {
    "done":           "Done ✓",
    "blocked":        "Blocked",
    "missing":        "Something missing",
    "snooze":         "Postponed",
    "progress":       "Still going",
    "invoiced":       "Invoice sent, waiting",
    "on_my_way":      "On my way ✓",
    "running_late":   "Running late",
    "cancelled":      "Cancelled today",
    "1_more_day":     "1 more day",
    "2_3_more_days":  "2–3 more days",
    # survey-specific
    "survey_done":    "Survey done — sending quote",
    "need_more_info": "Need more info — follow up",
    "no_show":        "Client no-show — reschedule",
    # billing
    "already_collected": "40% already collected",
    "client_delay":   "Client delay request",
    "submitted":      "Submitted to standards institute + 40% invoiced",
    "problem":        "⚠️ Problem on site",
}


def _verb_to_label(verb: str) -> str:
    """Return the human-readable label for a verb, falling back to the verb itself."""
    return VERB_LABELS.get(verb, verb.replace("_", " ").title())


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


async def handle_step_action(step_id: int, verb: str):
    """Handle a STEP_* action from a job step notification button tap."""
    event_uid: str | None = None
    job_id: int | None = None
    step_label: str = ""
    scheduled_at = None

    async with LocalSession() as db:
        step = await db.get(JobStep, step_id)
        if not step:
            logger.warning(f"Step action '{verb}' for unknown step {step_id}")
            return

        step.status = verb  # done | blocked | missing | progress | invoiced | snoozed
        step.updated_at = datetime.now(timezone.utc)

        # Capture values needed after commit (step object may be detached after session closes)
        event_uid = step.calendar_event_uid
        job_id = step.job_id
        step_label = step.label
        scheduled_at = step.scheduled_at

        await db.commit()
        logger.info(f"Step {step_id} ({step_label}): {verb}")

    # Write button tap back to the calendar event description
    label = _verb_to_label(verb)
    if event_uid:
        from app.services.ha_client import append_to_calendar_event
        await append_to_calendar_event(event_uid, "calendar.coach", label)
    else:
        logger.info(
            f"Step {step_id} has no calendar_event_uid — write-back skipped "
            f"(step label: {step_label!r}, verb: {verb!r})"
        )

    # Auto-advance job stage when step is marked done
    if verb == "done" and job_id is not None:
        await _advance_job_stage(job_id)

    # On-site day continuation: schedule next on-site event
    if verb == "1_more_day" and job_id is not None:
        await _schedule_next_onsite_day(step_id, job_id, scheduled_at, days_ahead=1)
    elif verb == "2_3_more_days" and job_id is not None:
        await _schedule_next_onsite_day(step_id, job_id, scheduled_at, days_ahead=2)


async def _advance_job_stage(job_id: int):
    """Move a PipelineJob to the next stage in sequence."""
    async with LocalSession() as db:
        job = await db.get(PipelineJob, job_id)
        if not job:
            logger.warning(f"_advance_job_stage: job {job_id} not found")
            return

        if job.stage not in PIPELINE_STAGES:
            logger.warning(f"_advance_job_stage: job {job_id} has unknown stage '{job.stage}'")
            return

        idx = PIPELINE_STAGES.index(job.stage)
        if idx < len(PIPELINE_STAGES) - 1:
            new_stage = PIPELINE_STAGES[idx + 1]
            job.stage = new_stage
            job.updated_at = datetime.now(timezone.utc)
            await db.commit()
            logger.info(f"Job {job_id} advanced to stage '{new_stage}'")

            try:
                from app.services.notifier import fire_pipeline_event
                from app.models import PIPELINE_STAGE_LABELS
                await fire_pipeline_event(
                    job.id, job.title, job.client or "",
                    new_stage, PIPELINE_STAGE_LABELS[new_stage],
                )
            except Exception as e:
                logger.warning(f"Pipeline event fire failed after stage advance: {e}")
        else:
            logger.info(f"Job {job_id} already at final stage '{job.stage}' — no advance")


async def _schedule_next_onsite_day(
    step_id: int,
    job_id: int,
    original_scheduled_at,
    days_ahead: int,
) -> None:
    """
    Create a new on-site calendar event on calendar.coach for days_ahead days
    from the original scheduled start time.
    """
    if original_scheduled_at is None:
        logger.warning(
            f"_schedule_next_onsite_day: step {step_id} has no scheduled_at — "
            f"using tomorrow at 08:00 as fallback"
        )
        base_dt = datetime.now(timezone.utc).replace(hour=5, minute=0, second=0, microsecond=0)
        # 08:00 Israel time = 05:00 UTC
    else:
        base_dt = original_scheduled_at
        if base_dt.tzinfo is None:
            base_dt = base_dt.replace(tzinfo=timezone.utc)

    new_start = base_dt + timedelta(days=days_ahead)
    new_end = new_start + timedelta(hours=8)  # default 8-hour on-site day

    # Fetch job title for the event summary
    job_title = f"Job {job_id}"
    try:
        async with LocalSession() as db:
            job = await db.get(PipelineJob, job_id)
            if job:
                job_title = job.title
    except Exception as e:
        logger.warning(f"_schedule_next_onsite_day: could not fetch job title: {e}")

    summary = f"On site — {job_title}"
    description = (
        f"Auto-scheduled by Coach (step {step_id} tapped "
        f"'{days_ahead} more day{'s' if days_ahead > 1 else ''}')"
    )

    try:
        from app.services.ha_client import create_calendar_event
        ok = await create_calendar_event(
            "calendar.coach", summary, new_start, new_end, description
        )
        if ok:
            logger.info(
                f"On-site continuation event created for job {job_id}: "
                f"{new_start.isoformat()}"
            )
        else:
            logger.warning(
                f"On-site continuation event creation returned False for job {job_id}"
            )
    except Exception as e:
        logger.error(f"_schedule_next_onsite_day error: {e}")


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
