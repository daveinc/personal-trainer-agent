import calendar as cal
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, get_current_user, tctx
from app.ha_calendar import create_event, get_today_events, get_week_events, get_month_events
from app.models import WorkoutLog

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

CATEGORY = "fitness"


def _is_user_fitness(event: dict, username: str) -> bool:
    desc = (event.get("description") or "").lower()
    return f"[{CATEGORY}]" in desc and f"[{username.lower()}]" in desc


def _event_date(event: dict) -> str:
    start = event.get("start", {}).get("dateTime", "")
    return start[:10] if start else ""


def _group_by_date(events: list) -> dict:
    grouped: dict = {}
    for e in events:
        d = _event_date(e)
        grouped.setdefault(d, []).append(e)
    return grouped


async def _get_logs(db: AsyncSession, user_id: int, date_from: str, date_to: str) -> dict:
    result = await db.execute(
        select(WorkoutLog).where(
            WorkoutLog.user_id == user_id,
            WorkoutLog.event_date >= date_from,
            WorkoutLog.event_date <= date_to,
        )
    )
    return {log.calendar_uid: log for log in result.scalars().all()}


# ── Today ──────────────────────────────────────────────────────────────────

async def _today_events_response(request: Request, db: AsyncSession, target: str):
    user = await get_current_user(request, db)
    if not user:
        return templates.TemplateResponse(
            request, "_fitness_today.html",
            tctx(request, events=[], logs={}, target=target)
        )
    try:
        raw = await get_today_events()
        events = [e for e in raw if _is_user_fitness(e, user.username)]
    except Exception:
        events = []

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    logs = await _get_logs(db, user.id, today_str, today_str)

    return templates.TemplateResponse(
        request, "_fitness_today.html",
        tctx(request, events=events, logs=logs, target=target)
    )


@router.get("/ui/fitness/today")
async def today_events(request: Request, db: AsyncSession = Depends(get_db)):
    source = request.query_params.get("from", "fitness")
    target = "dash-fitness" if source == "dashboard" else "fitness-content"
    return await _today_events_response(request, db, target)


# ── This Week ──────────────────────────────────────────────────────────────

async def _week_events_response(request: Request, db: AsyncSession, target: str):
    user = await get_current_user(request, db)
    if not user:
        return templates.TemplateResponse(
            request, "_fitness_range.html",
            tctx(request, grouped={}, logs={}, target=target, view="week")
        )
    try:
        raw = await get_week_events()
        events = [e for e in raw if _is_user_fitness(e, user.username)]
    except Exception:
        events = []

    now = datetime.now(timezone.utc)
    week_start = now.strftime("%Y-%m-%d")
    week_end = (now + timedelta(days=6)).strftime("%Y-%m-%d")
    logs = await _get_logs(db, user.id, week_start, week_end)

    return templates.TemplateResponse(
        request, "_fitness_range.html",
        tctx(request, grouped=_group_by_date(events), logs=logs, target=target, view="week")
    )


@router.get("/ui/fitness/week")
async def week_events(request: Request, db: AsyncSession = Depends(get_db)):
    return await _week_events_response(request, db, "fitness-content")


# ── This Month ─────────────────────────────────────────────────────────────

async def _month_events_response(request: Request, db: AsyncSession, target: str):
    user = await get_current_user(request, db)
    if not user:
        return templates.TemplateResponse(
            request, "_fitness_range.html",
            tctx(request, grouped={}, logs={}, target=target, view="month")
        )
    try:
        raw = await get_month_events()
        events = [e for e in raw if _is_user_fitness(e, user.username)]
    except Exception:
        events = []

    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1).strftime("%Y-%m-%d")
    last_day = cal.monthrange(now.year, now.month)[1]
    month_end = now.replace(day=last_day).strftime("%Y-%m-%d")
    logs = await _get_logs(db, user.id, month_start, month_end)

    return templates.TemplateResponse(
        request, "_fitness_range.html",
        tctx(request, grouped=_group_by_date(events), logs=logs, target=target, view="month")
    )


@router.get("/ui/fitness/month")
async def month_events(request: Request, db: AsyncSession = Depends(get_db)):
    return await _month_events_response(request, db, "fitness-content")


# ── Schedule ───────────────────────────────────────────────────────────────

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
        return templates.TemplateResponse(
            request, "_fitness_today.html",
            tctx(request, events=[], logs={}, target="today-events")
        )

    start_dt = datetime.fromisoformat(f"{date}T{start_time}:00")
    end_dt = start_dt + timedelta(minutes=duration)

    try:
        await create_event(
            summary=title,
            start=start_dt,
            end=end_dt,
            description=title,
            category=CATEGORY,
            username=user.username,
        )
    except Exception:
        pass

    return await _today_events_response(request, db, "today-events")


# ── Log ────────────────────────────────────────────────────────────────────

@router.post("/ui/fitness/log")
async def log_event(
    request: Request,
    uid: str = Form(...),
    title: str = Form(...),
    event_date: str = Form(...),
    status: str = Form(...),
    source: str = Form("fitness"),
    view: str = Form("today"),
    notes: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    target = "dash-fitness" if source == "dashboard" else "fitness-content"
    if not user:
        return templates.TemplateResponse(
            request, "_fitness_today.html",
            tctx(request, events=[], logs={}, target=target)
        )

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

    if source == "dashboard":
        return await _today_events_response(request, db, "dash-fitness")
    if view == "week":
        return await _week_events_response(request, db, "fitness-content")
    if view == "month":
        return await _month_events_response(request, db, "fitness-content")
    return await _today_events_response(request, db, "fitness-content")
