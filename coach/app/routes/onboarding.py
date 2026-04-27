import logging
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, get_current_user, redirect_to, tctx
from app.models import User, UserCategorySchedule

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)

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
async def onboarding_get(request: Request, step: int = 1, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    if user.onboarding_complete:
        return RedirectResponse(url=redirect_to(request, "ui/dashboard"), status_code=302)
    existing = {
        r.category: r for r in
        (await db.execute(select(UserCategorySchedule).where(UserCategorySchedule.user_id == user.id))).scalars().all()
    }
    return templates.TemplateResponse(request, "onboarding.html", tctx(
        request, user=user, step=step, categories=CATEGORIES, existing=existing
    ))


@router.post("/ui/onboarding/name")
async def onboarding_name(
    request: Request,
    display_name: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    user.display_name = display_name.strip()
    await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/onboarding?step=2"), status_code=303)


@router.post("/ui/onboarding/categories")
async def onboarding_categories(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    form = await request.form()
    await db.execute(delete(UserCategorySchedule).where(UserCategorySchedule.user_id == user.id))
    for slug, _ in CATEGORIES:
        stype = form.get(f"type_{slug}", "skip")
        days = ",".join(form.getlist(f"days_{slug}")) if stype != "skip" else ""
        start_time = form.get(f"start_{slug}", "") if stype != "skip" else ""
        end_time = form.get(f"end_{slug}", "") if stype != "skip" else ""
        db.add(UserCategorySchedule(
            user_id=user.id,
            category=slug,
            schedule_type=stype,
            days=days or None,
            start_time=start_time or None,
            end_time=end_time or None,
        ))
    user.onboarding_complete = True
    await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/dashboard"), status_code=303)


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
