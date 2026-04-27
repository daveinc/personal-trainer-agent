import logging
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, get_current_user, redirect_to, tctx
from app.models import Slot, SlotAttribute
from app.routes.onboarding import CATEGORIES

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)

CATEGORY_MAP = dict(CATEGORIES)
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


@router.get("/ui/profile")
async def profile_page(request: Request, edit: int = None, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)

    slots = (await db.execute(
        select(Slot).where(Slot.user_id == user.id).order_by(Slot.category, Slot.label)
    )).scalars().all()

    attrs_by_slot = {}
    for slot in slots:
        attrs_by_slot[slot.id] = (await db.execute(
            select(SlotAttribute).where(SlotAttribute.slot_id == slot.id)
        )).scalars().all()

    grouped = {}
    for slug, label in CATEGORIES:
        grouped[slug] = {"label": label, "slots": [s for s in slots if s.category == slug]}

    edit_slot = None
    if edit:
        edit_slot = (await db.execute(select(Slot).where(Slot.id == edit, Slot.user_id == user.id))).scalar_one_or_none()

    return templates.TemplateResponse(request, "profile.html", tctx(
        request, user=user, active="profile",
        grouped=grouped, attrs_by_slot=attrs_by_slot,
        categories=CATEGORIES, category_map=CATEGORY_MAP,
        days=DAYS, edit_slot=edit_slot,
    ))


@router.post("/ui/profile/slot/add")
async def slot_add(
    request: Request,
    category: str = Form(...),
    label: str = Form(...),
    schedule_type: str = Form("free"),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    form = await request.form()
    days = ",".join(form.getlist("days")) or None
    start_time = form.get("start_time") or None
    end_time = form.get("end_time") or None
    db.add(Slot(
        user_id=user.id, category=category, label=label.strip(),
        schedule_type=schedule_type, days=days,
        start_time=start_time, end_time=end_time,
    ))
    await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/profile"), status_code=303)


@router.post("/ui/profile/slot/{slot_id}/save")
async def slot_save(
    slot_id: int,
    request: Request,
    label: str = Form(...),
    schedule_type: str = Form("free"),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    slot = (await db.execute(select(Slot).where(Slot.id == slot_id, Slot.user_id == user.id))).scalar_one_or_none()
    if slot:
        form = await request.form()
        slot.label = label.strip()
        slot.schedule_type = schedule_type
        slot.days = ",".join(form.getlist("days")) or None
        slot.start_time = form.get("start_time") or None
        slot.end_time = form.get("end_time") or None
        await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/profile"), status_code=303)


@router.post("/ui/profile/slot/{slot_id}/delete")
async def slot_delete(slot_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    await db.execute(delete(SlotAttribute).where(SlotAttribute.slot_id == slot_id))
    await db.execute(delete(Slot).where(Slot.id == slot_id, Slot.user_id == user.id))
    await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/profile"), status_code=303)


@router.get("/ui/profile/slot/{slot_id}/attributes")
async def slot_attributes(slot_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    slot = (await db.execute(select(Slot).where(Slot.id == slot_id, Slot.user_id == user.id))).scalar_one_or_none()
    if not slot:
        return RedirectResponse(url=redirect_to(request, "ui/profile"), status_code=302)
    attrs = (await db.execute(select(SlotAttribute).where(SlotAttribute.slot_id == slot_id))).scalars().all()
    return templates.TemplateResponse(request, "profile_slot.html", tctx(
        request, user=user, active="profile", slot=slot, attrs=attrs,
        category_map=CATEGORY_MAP,
    ))


@router.post("/ui/profile/slot/{slot_id}/attribute/add")
async def attribute_add(
    slot_id: int,
    request: Request,
    attribute_name: str = Form(...),
    unit: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    slot = (await db.execute(select(Slot).where(Slot.id == slot_id, Slot.user_id == user.id))).scalar_one_or_none()
    if slot:
        db.add(SlotAttribute(slot_id=slot_id, attribute_name=attribute_name.strip(), unit=unit.strip() or None))
        await db.commit()
    return RedirectResponse(url=redirect_to(request, f"ui/profile/slot/{slot_id}/attributes"), status_code=303)


@router.post("/ui/profile/slot/{slot_id}/attribute/{attr_id}/delete")
async def attribute_delete(
    slot_id: int, attr_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    await db.execute(delete(SlotAttribute).where(SlotAttribute.id == attr_id, SlotAttribute.slot_id == slot_id))
    await db.commit()
    return RedirectResponse(url=redirect_to(request, f"ui/profile/slot/{slot_id}/attributes"), status_code=303)
