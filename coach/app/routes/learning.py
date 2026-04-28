import logging
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, get_current_user, redirect_to, tctx
from app.models import LearningItem

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)


@router.get("/ui/learning")
async def learning_page(request: Request, edit: int = None, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)

    items = (await db.execute(
        select(LearningItem)
        .where(LearningItem.user_id == user.id)
        .order_by(LearningItem.item_type, LearningItem.created_at)
    )).scalars().all()

    courses = [i for i in items if i.item_type == "course"]
    books   = [i for i in items if i.item_type == "book"]
    skills  = [i for i in items if i.item_type == "skill"]

    active_courses  = sum(1 for c in courses if c.status in ("active", "paused"))
    reading_books   = sum(1 for b in books if b.status == "reading")
    queue_books     = sum(1 for b in books if b.status == "queue")

    edit_item = next((i for i in items if i.id == edit), None) if edit else None

    return templates.TemplateResponse(request, "learning.html", tctx(
        request, user=user, active="learning",
        courses=courses, books=books, skills=skills,
        active_courses=active_courses, reading_books=reading_books,
        queue_books=queue_books, skills_count=len(skills),
        edit_item=edit_item,
    ))


@router.post("/ui/learning/item/add")
async def item_add(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    form = await request.form()
    item_type = form.get("item_type", "course")
    try:
        progress = int(form.get("progress") or 0)
    except ValueError:
        progress = 0

    db.add(LearningItem(
        user_id=user.id,
        item_type=item_type,
        title=(form.get("title") or "").strip(),
        meta=(form.get("meta") or "").strip() or None,
        progress=progress if item_type == "course" else None,
        status=form.get("status", "active"),
        current_level=(form.get("current_level") or "").strip() or None,
        target_level=(form.get("target_level") or "").strip() or None,
    ))
    await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/learning"), status_code=303)


@router.post("/ui/learning/item/{item_id}/save")
async def item_save(item_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    item = (await db.execute(
        select(LearningItem).where(LearningItem.id == item_id, LearningItem.user_id == user.id)
    )).scalar_one_or_none()
    if item:
        form = await request.form()
        item.title = (form.get("title") or item.title).strip()
        item.meta = (form.get("meta") or "").strip() or None
        item.status = form.get("status", item.status)
        item.current_level = (form.get("current_level") or "").strip() or None
        item.target_level = (form.get("target_level") or "").strip() or None
        if item.item_type == "course":
            try:
                item.progress = int(form.get("progress") or item.progress or 0)
            except ValueError:
                pass
        await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/learning"), status_code=303)


@router.post("/ui/learning/item/{item_id}/delete")
async def item_delete(item_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    await db.execute(delete(LearningItem).where(
        LearningItem.id == item_id, LearningItem.user_id == user.id
    ))
    await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/learning"), status_code=303)
