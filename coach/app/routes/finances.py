import logging
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, get_current_user, redirect_to, tctx
from app.models import FinanceLine, User
from app.services.spent import get_monthly_pulse

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)


@router.get("/ui/finances")
async def finances_page(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)

    lines = (await db.execute(
        select(FinanceLine).where(FinanceLine.user_id == user.id).order_by(FinanceLine.line_type, FinanceLine.created_at)
    )).scalars().all()

    income_lines  = [l for l in lines if l.line_type == "income"]
    expense_lines = [l for l in lines if l.line_type == "expense"]
    total_income  = sum(l.amount for l in income_lines)
    total_expense = sum(l.amount for l in expense_lines)
    net_savings   = total_income - total_expense
    savings_rate  = round(net_savings / total_income * 100, 1) if total_income > 0 else 0.0

    spent_pulse = await get_monthly_pulse()

    return templates.TemplateResponse(request, "finances.html", tctx(
        request, user=user, active="finances",
        income_lines=income_lines, expense_lines=expense_lines,
        total_income=total_income, total_expense=total_expense,
        net_savings=net_savings, savings_rate=savings_rate,
        currency=getattr(user, "currency", "$") or "$",
        savings_target=getattr(user, "savings_target", 0.0) or 0.0,
        spent_pulse=spent_pulse,
    ))


@router.post("/ui/finances/line/add")
async def line_add(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    form = await request.form()
    label = (form.get("label") or "").strip()
    line_type = form.get("line_type", "expense")
    try:
        amount = float(form.get("amount") or 0)
    except ValueError:
        amount = 0.0
    if label:
        db.add(FinanceLine(user_id=user.id, label=label, line_type=line_type, amount=amount))
        await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/finances"), status_code=303)


@router.post("/ui/finances/line/{line_id}/edit")
async def line_edit(line_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    line = (await db.execute(
        select(FinanceLine).where(FinanceLine.id == line_id, FinanceLine.user_id == user.id)
    )).scalar_one_or_none()
    if line:
        form = await request.form()
        line.label = (form.get("label") or "").strip() or line.label
        try:
            line.amount = float(form.get("amount") or 0)
        except ValueError:
            pass
        await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/finances"), status_code=303)


@router.post("/ui/finances/line/{line_id}/delete")
async def line_delete(line_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    await db.execute(delete(FinanceLine).where(FinanceLine.id == line_id, FinanceLine.user_id == user.id))
    await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/finances"), status_code=303)


@router.post("/ui/finances/goal/save")
async def goal_save(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    form = await request.form()
    try:
        user.savings_target = float(form.get("savings_target") or 0)
    except ValueError:
        pass
    await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/finances"), status_code=303)
