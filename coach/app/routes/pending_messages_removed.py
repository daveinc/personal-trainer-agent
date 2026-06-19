import logging
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from app.database import LocalSession
from app.models import PendingMessage, PipelineJob, JobStep

router = APIRouter(prefix="/api/v1")
logger = logging.getLogger(__name__)


class MarkReadRequest(BaseModel):
    ids: List[int]


@router.get("/pending-messages")
async def get_pending_messages():
    """Return all unread PendingMessage rows joined with job title and step label."""
    async with LocalSession() as db:
        rows = (await db.execute(
            select(PendingMessage)
            .where(PendingMessage.read == False)  # noqa: E712
            .order_by(PendingMessage.created_at.asc())
        )).scalars().all()

        result = []
        for msg in rows:
            job_title = None
            if msg.job_id:
                job = await db.get(PipelineJob, msg.job_id)
                job_title = job.title if job else None

            step_label = None
            step_stage = None
            if msg.step_id:
                step = await db.get(JobStep, msg.step_id)
                if step:
                    step_label = step.label
                    step_stage = step.stage

            result.append({
                "id": msg.id,
                "job": job_title,
                "stage": step_stage,
                "step": step_label,
                "action": msg.action,
                "notes": msg.notes,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
            })

    return result


@router.post("/pending-messages/mark-read")
async def mark_messages_read(body: MarkReadRequest):
    """Mark the given message IDs as read."""
    if not body.ids:
        return {"marked": 0}

    async with LocalSession() as db:
        rows = (await db.execute(
            select(PendingMessage).where(PendingMessage.id.in_(body.ids))
        )).scalars().all()

        for msg in rows:
            msg.read = True

        await db.commit()
        logger.info(f"Marked {len(rows)} pending messages as read: {body.ids}")

    return {"marked": len(rows)}
