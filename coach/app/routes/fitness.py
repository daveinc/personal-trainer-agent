from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, get_current_user
from app.ha_calendar import create_event, get_today_events
from app.models import WorkoutLog

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

CATEGORY = "fitness"


def _is_fitness(event: dict) -> bool:
    desc = (event.get("description") or "").lower()
    return f"[{CATEGORY}]" in desc


@router.get("/ui/fitness/today")
async def today_events(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return templates.TemplateResponse(request, "_fitness_today.html", {"events": [], "logs": {}})

    try:
        raw = await get_today_events()
        events = [e for e in raw if _is_fitness(e)]
    except Exception:
        events = []

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    result = await db.execute(
        select(WorkoutLog).where(
            WorkoutLog.user_id == user.id,
            WorkoutLog.event_date == today_str,
        )
    )
    logs_today = result.scalars().all()
    logs = {log.calendar_uid: log for log in logs_today}

    return templates.TemplateResponse(
        request, "_fitness_today.html", {"events": events, "logs": logs}
    )


@router.post("/ui/fitness/schedule")
async def schedule(
    request: Request,
    title: str = Form(...),
    date: str = Form(...),
    start_time: str = Form(...),
    duration: int = Form(60),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    if not user:
        return templates.TemplateResponse(request, "_fitness_today.html", {"events": [], "logs": {}})

    start_dt = datetime.fromisoformat(f"{date}T{start_time}:00").replace(tzinfo=timezone.utc)
    end_dt = start_dt + timedelta(minutes=duration)

    try:
        await create_event(
            summary=title,
            start=start_dt,
            end=end_dt,
            description=title,
            category=CATEGORY,
        )
    except Exception:
        pass

    return await today_events(request, db)


@router.post("/ui/fitness/log")
async def log_event(
    request: Request,
    uid: str = Form(...),
    title: str = Form(...),
    event_date: str = Form(...),
    status: str = Form(...),
    notes: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    if not user:
        return templates.TemplateResponse(request, "_fitness_today.html", {"events": [], "logs": {}})

    result = await db.execute(
        select(WorkoutLog).where(
            WorkoutLog.user_id == user.id,
            WorkoutLog.calendar_uid == uid,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.status = status
        existing.notes = notes
    else:
        db.add(WorkoutLog(
            user_id=user.id,
            calendar_uid=uid,
            event_date=event_date,
            event_title=title,
            status=status,
            notes=notes,
        ))
    await db.commit()

    return await today_events(request, db)
