import logging
from datetime import date, timedelta, datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, get_current_user, redirect_to, tctx
from app.models import CheckIn
from app.ha_calendar import create_event
from app.routes.schedule import _get_week, _get_days

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)


def _compute_streak(dates: set, today: str) -> int:
    streak = 0
    check = date.today() if today in dates else date.today() - timedelta(days=1)
    while check.strftime("%Y-%m-%d") in dates:
        streak += 1
        check -= timedelta(days=1)
    return streak


@router.get("/ui/checkins")
async def checkins_page(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)

    today_str = date.today().strftime("%Y-%m-%d")
    week_start = getattr(user, "week_start", "Mon") or "Mon"

    entries = (await db.execute(
        select(CheckIn)
        .where(CheckIn.user_id == user.id)
        .order_by(CheckIn.log_date.desc())
        .limit(60)
    )).scalars().all()

    dates = {e.log_date for e in entries}
    today_entry = next((e for e in entries if e.log_date == today_str), None)
    streak = _compute_streak(dates, today_str)

    week_days = _get_week(date.today(), week_start)
    week_data = [
        (d.strftime("%a")[0], d.strftime("%Y-%m-%d") in dates)
        for d in week_days
    ]

    return templates.TemplateResponse(request, "checkins.html", tctx(
        request, user=user, active="checkins",
        today_entry=today_entry, today_str=today_str,
        entries=entries[:30], streak=streak,
        week_data=week_data,
    ))


@router.post("/ui/checkins/log")
async def checkins_log(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)

    form = await request.form()
    today_str = date.today().strftime("%Y-%m-%d")

    try:
        mood = int(form.get("mood", 5))
        energy = int(form.get("energy", 5))
    except ValueError:
        mood, energy = 5, 5
    notes = (form.get("notes") or "").strip() or None

    existing = (await db.execute(
        select(CheckIn).where(CheckIn.user_id == user.id, CheckIn.log_date == today_str)
    )).scalar_one_or_none()

    if existing:
        existing.mood = mood
        existing.energy = energy
        existing.notes = notes
    else:
        db.add(CheckIn(user_id=user.id, mood=mood, energy=energy,
                       notes=notes, log_date=today_str))
        try:
            now = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            desc = f"mood:{mood} energy:{energy}" + (f" — {notes}" if notes else "")
            await create_event(
                summary="Daily Check-in",
                start=now,
                end=now.replace(hour=0, minute=30),
                description=desc,
                category="checkin",
                username=user.username,
            )
        except Exception as e:
            logger.warning(f"Check-in calendar event failed: {e}")

    await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/checkins"), status_code=303)


@router.post("/ui/checkins/{entry_id}/delete")
async def checkins_delete(entry_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    await db.execute(delete(CheckIn).where(
        CheckIn.id == entry_id, CheckIn.user_id == user.id
    ))
    await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/checkins"), status_code=303)
