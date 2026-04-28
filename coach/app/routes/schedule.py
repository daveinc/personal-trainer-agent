import logging
import re
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, get_current_user, redirect_to, tctx
from app.models import Slot, SlotAttribute
from app.routes.onboarding import CATEGORIES
from app.ha_calendar import get_week_events

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)

CATEGORY_MAP = dict(CATEGORIES)
_KNOWN_CATEGORIES = set(CATEGORY_MAP.keys())


def _prep_cal_events(raw: list) -> dict:
    """Filter out checkins, extract useful fields, group by date string."""
    by_date = {}
    for e in raw:
        desc = (e.get("description") or "").lower()
        if "[checkin]" in desc:
            continue
        dt = e.get("start", {}).get("dateTime", "") or e.get("start", {}).get("date", "")
        day = dt[:10]
        if not day:
            continue
        category = next(
            (t for t in re.findall(r'\[([^\]]+)\]', desc) if t in _KNOWN_CATEGORIES), ""
        )
        by_date.setdefault(day, []).append({
            "summary": e.get("summary", "Event"),
            "time": dt[11:16] if len(dt) > 10 else "",
            "category": category,
        })
    return by_date
_DAYS_MON = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
_DAYS_SUN = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

def _get_days(week_start: str) -> list:
    return _DAYS_SUN if week_start == "Sun" else _DAYS_MON

CATEGORY_ATTRIBUTES = {
    "fitness":       ["duration", "distance", "heart_rate", "pace", "calories", "notes"],
    "health":        ["weight", "sleep_hours", "mood", "energy", "blood_pressure", "notes"],
    "schedule":      ["task", "outcome", "priority", "notes"],
    "finances":      ["amount", "category", "balance", "notes"],
    "learning":      ["topic", "duration", "progress", "notes"],
    "relationships": ["person", "activity", "mood", "notes"],
    "checkins":      ["score", "highlights", "blockers", "notes"],
    "milestones":    ["milestone", "status", "notes"],
    "challenges":    ["challenge", "result", "notes"],
}


def _get_week(ref: date, week_start: str = "Mon"):
    if week_start == "Sun":
        start = ref - timedelta(days=(ref.weekday() + 1) % 7)
    else:
        start = ref - timedelta(days=ref.weekday())
    return [start + timedelta(days=i) for i in range(7)]


def _today_or_next(slots, ref: date):
    today_name = ref.strftime("%a")
    today_slots = [s for s in slots if s.days and today_name in s.days.split(",")]
    if today_slots:
        return today_slots, today_name, ref
    for offset in range(1, 8):
        next_date = ref + timedelta(days=offset)
        next_name = next_date.strftime("%a")
        next_slots = [s for s in slots if s.days and next_name in s.days.split(",")]
        if next_slots:
            return next_slots, next_name, next_date
    return [], None, None


@router.get("/ui/schedule")
async def schedule_page(request: Request, selected: int = None, edit: int = None,
                        db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)

    slots = (await db.execute(
        select(Slot).where(Slot.user_id == user.id).order_by(Slot.category, Slot.start_time)
    )).scalars().all()

    today = date.today()
    week_start = getattr(user, "week_start", "Mon") or "Mon"
    days = _get_days(week_start)
    week_dates = _get_week(today, week_start)
    upcoming_slots, upcoming_day, upcoming_date = _today_or_next(slots, today)

    week_data = []
    for d in week_dates:
        day_name = d.strftime("%a")
        day_slots = sorted(
            [s for s in slots if s.days and day_name in s.days.split(",")],
            key=lambda s: s.start_time or ""
        )
        week_data.append({"date": d, "day_name": day_name, "slots": day_slots, "is_today": d == today})

    try:
        cal_by_date = _prep_cal_events(await get_week_events())
    except Exception:
        cal_by_date = {}

    selected_slot = None
    if selected:
        selected_slot = next((s for s in slots if s.id == selected), None)

    edit_slot = None
    if edit:
        edit_slot = next((s for s in slots if s.id == edit), None)

    attrs_by_slot = {}
    for slot in slots:
        attrs_by_slot[slot.id] = (await db.execute(
            select(SlotAttribute).where(SlotAttribute.slot_id == slot.id)
        )).scalars().all()

    return templates.TemplateResponse(request, "schedule_new.html", tctx(
        request, user=user, active="schedule",
        slots=slots, week_data=week_data, cal_by_date=cal_by_date,
        upcoming_slots=upcoming_slots, upcoming_day=upcoming_day, upcoming_date=upcoming_date,
        today_cal=cal_by_date.get(today.strftime("%Y-%m-%d"), []),
        selected_slot=selected_slot, edit_slot=edit_slot,
        categories=CATEGORIES, category_map=CATEGORY_MAP,
        category_attributes=CATEGORY_ATTRIBUTES,
        days=days, today=today, attrs_by_slot=attrs_by_slot,
        week_start=week_start,
    ))


@router.post("/ui/schedule/slot/add")
async def slot_add(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    form = await request.form()
    days = ",".join(form.getlist("days")) or None
    db.add(Slot(
        user_id=user.id,
        category=form.get("category", "fitness"),
        label=(form.get("label") or "").strip(),
        schedule_type=form.get("schedule_type", "free"),
        days=days,
        start_time=form.get("start_time") or None,
        end_time=form.get("end_time") or None,
        notify_before=int(form.get("notify_before")) if form.get("notify_before") else None,
    ))
    await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/schedule"), status_code=303)


@router.post("/ui/schedule/slot/{slot_id}/save")
async def slot_save(slot_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    slot = (await db.execute(select(Slot).where(Slot.id == slot_id, Slot.user_id == user.id))).scalar_one_or_none()
    if slot:
        form = await request.form()
        slot.label = (form.get("label") or "").strip()
        slot.schedule_type = form.get("schedule_type", "free")
        slot.days = ",".join(form.getlist("days")) or None
        slot.start_time = form.get("start_time") or None
        slot.end_time = form.get("end_time") or None
        slot.notify_before = int(form.get("notify_before")) if form.get("notify_before") else None
        await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/schedule"), status_code=303)


@router.post("/ui/schedule/slot/{slot_id}/delete")
async def slot_delete(slot_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    await db.execute(delete(SlotAttribute).where(SlotAttribute.slot_id == slot_id))
    await db.execute(delete(Slot).where(Slot.id == slot_id, Slot.user_id == user.id))
    await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/schedule"), status_code=303)


@router.post("/ui/schedule/slot/{slot_id}/attribute/add")
async def attribute_add(slot_id: int, request: Request,
                        attribute_name: str = Form(...), unit: str = Form(""),
                        db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    slot = (await db.execute(select(Slot).where(Slot.id == slot_id, Slot.user_id == user.id))).scalar_one_or_none()
    if slot:
        db.add(SlotAttribute(slot_id=slot_id, attribute_name=attribute_name.strip(), unit=unit.strip() or None))
        await db.commit()
    return RedirectResponse(url=redirect_to(request, f"ui/schedule?selected={slot_id}"), status_code=303)


@router.post("/ui/schedule/slot/{slot_id}/attribute/{attr_id}/delete")
async def attribute_delete(slot_id: int, attr_id: int, request: Request,
                           db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    await db.execute(delete(SlotAttribute).where(SlotAttribute.id == attr_id, SlotAttribute.slot_id == slot_id))
    await db.commit()
    return RedirectResponse(url=redirect_to(request, f"ui/schedule?selected={slot_id}"), status_code=303)


@router.post("/ui/schedule/category/{category}/set-reminder")
async def category_set_reminder(category: str, request: Request,
                                notify_before: int = Form(...),
                                db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    await db.execute(
        update(Slot).where(Slot.user_id == user.id, Slot.category == category)
        .values(notify_before=notify_before)
    )
    await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/schedule"), status_code=303)


@router.post("/ui/schedule/category/{category}/clear-reminders")
async def category_clear_reminders(category: str, request: Request,
                                   db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    await db.execute(
        update(Slot).where(Slot.user_id == user.id, Slot.category == category)
        .values(notify_before=None)
    )
    await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/schedule"), status_code=303)
