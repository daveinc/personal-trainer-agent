from datetime import datetime, timezone, date, timedelta
import random

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, get_current_user, redirect_to, tctx
from app.models import Slot, CheckIn, HealthEntry, StandupEntry
from app.routes.schedule import _get_week, _get_days, _today_or_next, CATEGORY_MAP
from app.ha_calendar import get_today_events

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


async def get_mood_trend(db: AsyncSession, user_id: int, days: int = 7):
    query = select(CheckIn).where(
        CheckIn.user_id == user_id,
        CheckIn.log_date >= (date.today() - timedelta(days=days)).strftime("%Y-%m-%d")
    ).order_by(CheckIn.log_date)
    results = (await db.execute(query)).scalars().all()
    return [(c.log_date, c.mood) for c in results]


async def get_sleep_average(db: AsyncSession, user_id: int, days: int = 7):
    query = select(HealthEntry).where(
        HealthEntry.user_id == user_id,
        HealthEntry.metric == "sleep",
        HealthEntry.log_date >= (date.today() - timedelta(days=days)).strftime("%Y-%m-%d")
    )
    results = (await db.execute(query)).scalars().all()
    if results:
        return sum(e.value for e in results) / len(results)
    return 0.0


async def get_active_streaks(db: AsyncSession, user_id: int):
    return []  # Placeholder - would need a Streak model


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
        checked_in_dates = sorted(list(set([datetime.strptime(c.log_date, "%Y-%m-%d").date() for c in checkins])), reverse=True)

        current_day = today
        if not has_checkin_today:
             current_day = today - timedelta(days=1)

        for _ in range(7):
            if current_day in checked_in_dates:
                streak += 1
                current_day -= timedelta(days=1)
            else:
                break

    mood_trend = await get_mood_trend(db, user.id)
    sleep_average = await get_sleep_average(db, user.id)
    active_streaks = await get_active_streaks(db, user.id)

    today_str = today.strftime("%Y-%m-%d")
    standup_done = (await db.execute(
        select(StandupEntry).where(StandupEntry.user_id == user.id, StandupEntry.log_date == today_str)
    )).scalar_one_or_none() is not None

    try:
        ha_events = await get_today_events()
    except Exception:
        ha_events = []

    return templates.TemplateResponse(request, "dashboard.html", tctx(
        request, user=user, greeting=greeting,
        today_slots=today_slots, upcoming_slots=upcoming_slots,
        upcoming_day=upcoming_day, upcoming_date=upcoming_date,
        active_categories=active_categories, category_map=CATEGORY_MAP,
        week_data=week_data, days=days, today=today, week_start=week_start,
        mood_avg=mood_avg, energy_avg=energy_avg, streak=streak,
        has_checkin_today=has_checkin_today,
        mood_trend=mood_trend, sleep_average=sleep_average, active_streaks=active_streaks,
        standup_done=standup_done,
        ha_events=ha_events,
    ))


@router.post("/log/quick")
async def quick_log(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return {"error": "Not authenticated"}, 401

    data = await request.json()

    if "mood" in data:
        today_str = date.today().strftime("%Y-%m-%d")
        existing = (await db.execute(
            select(CheckIn).where(CheckIn.user_id == user.id, CheckIn.log_date == today_str)
        )).scalar_one_or_none()
        if existing:
            existing.mood = data["mood"]
        else:
            db.add(CheckIn(user_id=user.id, mood=data["mood"], energy=5, notes="", log_date=today_str))
        await db.commit()
        return {"success": True}

    if "weight" in data:
        today_str = date.today().strftime("%Y-%m-%d")
        db.add(HealthEntry(user_id=user.id, metric="weight", value=data["weight"], log_date=today_str))
        await db.commit()
        return {"success": True}

    return {"error": "Invalid data"}, 400


@router.post("/ui/standup/submit")
async def standup_submit(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)

    form = await request.form()
    today_str = date.today().strftime("%Y-%m-%d")
    existing = (await db.execute(
        select(StandupEntry).where(StandupEntry.user_id == user.id, StandupEntry.log_date == today_str)
    )).scalar_one_or_none()

    if not existing:
        entry = StandupEntry(
            user_id=user.id,
            log_date=today_str,
            done_items=(form.get("done") or "").strip() or None,
            new_items=(form.get("new") or "").strip() or None,
            blockers=(form.get("blockers") or "").strip() or None,
        )
        db.add(entry)
        await db.commit()

    return RedirectResponse(url=redirect_to(request, "ui/dashboard"), status_code=303)


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
