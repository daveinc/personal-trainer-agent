import logging
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, get_current_user, redirect_to, tctx
from app.models import User, Slot

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)

HEALTH_METRICS_OPTIONS = [
    ("weight",     "Weight"),
    ("sleep",      "Sleep"),
    ("bp",         "Blood Pressure"),
    ("resting_hr", "Resting HR"),
    ("medication", "Medication"),
]

CATEGORIES = [
    ("fitness",       "Fitness"),
    ("health",        "Health"),
    ("schedule",      "Schedule / Career"),
    ("finances",      "Finances"),
    ("learning",      "Learning"),
    ("relationships", "Relationships"),
    ("checkins",      "Check-ins"),
    ("milestones",    "Milestones"),
    ("challenges",    "Challenges"),
]


@router.get("/ui/onboarding")
async def onboarding_get(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    if user.onboarding_complete:
        return RedirectResponse(url=redirect_to(request, "ui/dashboard"), status_code=302)
    return templates.TemplateResponse(request, "onboarding.html", tctx(
        request, user=user, categories=CATEGORIES,
        health_metrics_options=HEALTH_METRICS_OPTIONS,
    ))


@router.post("/ui/onboarding/save")
async def onboarding_save(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    form = await request.form()
    display_name = (form.get("display_name") or "").strip()
    if not display_name:
        return RedirectResponse(url=redirect_to(request, "ui/onboarding"), status_code=303)
    user.display_name = display_name
    user.unit_distance = form.get("unit_distance", "km")
    user.unit_weight = form.get("unit_weight", "kg")
    user.week_start = form.get("week_start", "Mon")
    user.currency = (form.get("currency") or "$").strip() or "$"
    selected_metrics = form.getlist("health_metrics")
    user.health_metrics = ",".join(selected_metrics)
    selected = form.getlist("categories")
    for slug, label in CATEGORIES:
        if slug in selected:
            existing = (await db.execute(
                select(Slot).where(Slot.user_id == user.id, Slot.category == slug)
            )).scalar_one_or_none()
            if not existing:
                db.add(Slot(user_id=user.id, category=slug, label=label, schedule_type="free"))
    user.onboarding_complete = True
    await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/schedule"), status_code=303)


@router.post("/ui/onboarding/dismiss")
async def onboarding_dismiss(
    request: Request,
    user_id: int = Form(...),
    db: AsyncSession = Depends(get_db),
):
    current = await get_current_user(request, db)
    if not current:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    target = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if target:
        target.onboarding_complete = True
        await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/settings"), status_code=303)
