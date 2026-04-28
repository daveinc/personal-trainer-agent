import logging
from datetime import date
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, get_current_user, redirect_to, tctx
from app.models import Person

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)


def _days_since(last_contact: str | None) -> int:
    if not last_contact:
        return 9999
    try:
        return (date.today() - date.fromisoformat(last_contact)).days
    except ValueError:
        return 9999


def _status(days: int) -> tuple:
    if days <= 7:
        return "Active", "#dcfce7", "#15803d"
    if days <= 29:
        return "Call soon", "#e0e7ff", "#3730a3"
    if days < 9999:
        return "Overdue", "#fef3c7", "#b45309"
    return "Never contacted", "#fee2e2", "#b91c1c"


@router.get("/ui/relationships")
async def relationships_page(request: Request, edit: int = None, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)

    people = (await db.execute(
        select(Person)
        .where(Person.user_id == user.id)
        .order_by(Person.name)
    )).scalars().all()

    enriched = []
    for p in people:
        days = _days_since(p.last_contact)
        label, bg, color = _status(days)
        enriched.append({"person": p, "days": days, "status_label": label,
                         "status_bg": bg, "status_color": color})

    total = len(people)
    due = sum(1 for e in enriched if e["days"] >= 30)
    call_soon = sum(1 for e in enriched if 7 < e["days"] < 30)
    edit_person = next((p for p in people if p.id == edit), None) if edit else None

    return templates.TemplateResponse(request, "relationships.html", tctx(
        request, user=user, active="relationships",
        enriched=enriched, total=total, due=due, call_soon=call_soon,
        edit_person=edit_person, today=date.today().strftime("%Y-%m-%d"),
    ))


@router.post("/ui/relationships/person/add")
async def person_add(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    form = await request.form()
    db.add(Person(
        user_id=user.id,
        name=(form.get("name") or "").strip(),
        relationship=(form.get("relationship") or "").strip() or None,
        last_contact=form.get("last_contact") or None,
        notes=(form.get("notes") or "").strip() or None,
    ))
    await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/relationships"), status_code=303)


@router.post("/ui/relationships/person/{person_id}/save")
async def person_save(person_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    person = (await db.execute(
        select(Person).where(Person.id == person_id, Person.user_id == user.id)
    )).scalar_one_or_none()
    if person:
        form = await request.form()
        person.name = (form.get("name") or person.name).strip()
        person.relationship = (form.get("relationship") or "").strip() or None
        person.last_contact = form.get("last_contact") or None
        person.notes = (form.get("notes") or "").strip() or None
        await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/relationships"), status_code=303)


@router.post("/ui/relationships/person/{person_id}/contact")
async def person_contact(person_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    person = (await db.execute(
        select(Person).where(Person.id == person_id, Person.user_id == user.id)
    )).scalar_one_or_none()
    if person:
        person.last_contact = date.today().strftime("%Y-%m-%d")
        await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/relationships"), status_code=303)


@router.post("/ui/relationships/person/{person_id}/delete")
async def person_delete(person_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    await db.execute(delete(Person).where(
        Person.id == person_id, Person.user_id == user.id
    ))
    await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/relationships"), status_code=303)
