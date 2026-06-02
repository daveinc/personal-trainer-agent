from datetime import datetime, date, time, timezone

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import LocalSession
from app.deps import get_db, get_current_user, tctx
from app.models import EventLog, User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _today_start() -> datetime:
    d = date.today()
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)


@router.get("/events/log/form", response_class=HTMLResponse)
async def log_form(request: Request, title: str = ""):
    return templates.TemplateResponse(
        request, "partials/event_log_form.html",
        tctx(request, title=title)
    )


@router.post("/events/log", response_class=HTMLResponse)
async def log_event(
    request: Request,
    event_title: str = Form(...),
    action: str = Form(default="note"),
    notes: str = Form(default=""),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    if not user:
        return HTMLResponse("", status_code=401)

    entry = EventLog(
        user_id=user.id,
        event_title=event_title,
        action=action,
        notes=notes.strip() or None,
        logged_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    await db.commit()

    logs = await _get_today_logs(user.id, db)
    return templates.TemplateResponse(
        request, "partials/event_log_list.html",
        tctx(request, logs=logs)
    )


@router.get("/events/log/today", response_class=HTMLResponse)
async def get_today_logs_route(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return HTMLResponse("", status_code=401)
    logs = await _get_today_logs(user.id, db)
    return templates.TemplateResponse(
        request, "partials/event_log_list.html",
        tctx(request, logs=logs)
    )


async def _get_today_logs(user_id: int, db: AsyncSession) -> list:
    result = await db.execute(
        select(EventLog)
        .where(EventLog.user_id == user_id, EventLog.logged_at >= _today_start())
        .order_by(EventLog.logged_at.desc())
    )
    return result.scalars().all()


async def save_event_log(user_id: int, event_title: str, action: str, notes: str = "") -> None:
    """Used by action_router to persist notification button taps."""
    async with LocalSession() as db:
        db.add(EventLog(
            user_id=user_id,
            event_title=event_title,
            action=action,
            notes=notes or None,
            logged_at=datetime.now(timezone.utc),
        ))
        await db.commit()
