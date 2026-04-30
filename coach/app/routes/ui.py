from datetime import datetime, timezone, date, timedelta

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, get_current_user, redirect_to, tctx
from app.models import Slot, CheckIn
from app.routes.schedule import _get_week, _get_days, _today_or_next, CATEGORY_MAP

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/ui/login")
async def login(request: Request):
    return templates.TemplateResponse(request, "login.html", tctx(request))


@router.get("/ui/dashboard")
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)

    now = datetime.now()
    hour = now.hour
    greeting = "morning" if hour < 12 else "afternoon" if hour < 18 else "evening"

    slots = (await db.execute(
        select(Slot).where(Slot.user_id == user.id).order_by(Slot.start_time)
    )).scalars().all()

    today = date.today()
    week_start = getattr(user, "week_start", "Mon") or "Mon"
    days = _get_days(week_start)
    week_dates = _get_week(today, week_start)
    upcoming_slots, upcoming_day, upcoming_date = _today_or_next(slots, today)

    today_name = today.strftime("%a")
    today_slots = sorted(
        [s for s in slots if s.days and today_name in s.days.split(",")],
        key=lambda s: s.start_time or ""
    )
    active_categories = list(dict.fromkeys(s.category for s in today_slots))

    week_data = []
    for d in week_dates:
        day_name = d.strftime("%a")
        day_slots = sorted(
            [s for s in slots if s.days and day_name in s.days.split(",")],
            key=lambda s: s.start_time or ""
        )
        week_data.append({"date": d, "day_name": day_name, "slots": day_slots, "is_today": d == today})

    # Check-in data for dashboard
    seven_days_ago = today - timedelta(days=6)
    checkins_query = select(CheckIn).where(
        CheckIn.user_id == user.id,
        CheckIn.log_date >= seven_days_ago.strftime("%Y-%m-%d"),
        CheckIn.log_date <= today.strftime("%Y-%m-%d")
    ).order_by(CheckIn.log_date)
    checkins = (await db.execute(checkins_query)).scalars().all()

    mood_avg = round(sum([c.mood for c in checkins]) / len(checkins), 1) if checkins else 0
    energy_avg = round(sum([c.energy for c in checkins]) / len(checkins), 1) if checkins else 0

    has_checkin_today = any(c.log_date == today.strftime("%Y-%m-%d") for c in checkins)

    # Calculate streak
    streak = 0
    if checkins:
        # Get unique dates of checkins within the 7-day window
        checked_in_dates = sorted(list(set([datetime.strptime(c.log_date, "%Y-%m-%d").date() for c in checkins])), reverse=True)
        
        current_day = today
        if not has_checkin_today:
             # If no checkin today, check streak ending yesterday
            current_day = today - timedelta(days=1)
            
        for _ in range(7):  # Check for up to 7 consecutive days
            if current_day in checked_in_dates:
                streak += 1
                current_day -= timedelta(days=1)
            else:
                break
    
    return templates.TemplateResponse(request, "dashboard.html", tctx(
        request, user=user, greeting=greeting,
        today_slots=today_slots, upcoming_slots=upcoming_slots,
        upcoming_day=upcoming_day, upcoming_date=upcoming_date,
        active_categories=active_categories, category_map=CATEGORY_MAP,
        week_data=week_data, days=days, today=today, week_start=week_start,
        mood_avg=mood_avg, energy_avg=energy_avg, streak=streak,
        has_checkin_today=has_checkin_today,
    ))



@router.get("/ui/ha-status")
async def ha_status(request: Request):
    from app.ha_calendar import check_connection
    ha_ok = await check_connection()
    dot = "ok" if ha_ok else "error"
    label = "Connected" if ha_ok else "Not reachable"
    return templates.TemplateResponse(request, "_ha_status.html", tctx(request, dot=dot, label=label))


@router.get("/ui/fitness")
async def fitness(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    return templates.TemplateResponse(request, "fitness.html", tctx(request, user=user))
