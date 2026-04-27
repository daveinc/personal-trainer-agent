import logging
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, get_current_user, redirect_to, tctx
from app.models import ScoringRule, TrendObservation, TrendPeriod, User, WorkoutLog

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)

SAFE_BUILTINS = {"round": round, "abs": abs, "max": max, "min": min, "int": int, "float": float}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


async def _get_or_create_rule(db: AsyncSession) -> ScoringRule:
    rule = (await db.execute(select(ScoringRule))).scalar_one_or_none()
    if not rule:
        rule = ScoringRule()
        db.add(rule)
        await db.commit()
        await db.refresh(rule)
    return rule


def _eval_formula(formula: str, completed: int, skipped: int, missed: int,
                  total: int, period_days: int = 30):
    variables = {
        "completed": completed, "skipped": skipped,
        "missed": missed, "total": total, "period_days": period_days,
    }
    try:
        result = eval(formula, {"__builtins__": {}}, {**SAFE_BUILTINS, **variables})
        return str(result), None
    except Exception as e:
        return None, str(e)


# ── Main page ──────────────────────────────────────────────────────────────

@router.get("/ui/trends")
async def trends_page(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    return templates.TemplateResponse(request, "trends.html",
                                      tctx(request, user=user, active="trends"))


# ── Scoring tab ────────────────────────────────────────────────────────────

@router.get("/ui/trends/scoring")
async def trends_scoring(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    rule = await _get_or_create_rule(db)

    # Pull real counts from WorkoutLog
    completed = (await db.execute(
        select(func.count(WorkoutLog.id)).where(WorkoutLog.status == "completed")
    )).scalar() or 0
    skipped = (await db.execute(
        select(func.count(WorkoutLog.id)).where(WorkoutLog.status == "skipped")
    )).scalar() or 0
    missed = (await db.execute(
        select(func.count(WorkoutLog.id)).where(WorkoutLog.status == "missed")
    )).scalar() or 0
    total = completed + skipped + missed

    preview_result = preview_error = None
    if rule.formula_enabled and rule.formula:
        preview_result, preview_error = _eval_formula(rule.formula, completed, skipped, missed, total)

    return templates.TemplateResponse(request, "_trends_scoring.html",
                                      tctx(request, rule=rule,
                                           completed=completed, skipped=skipped,
                                           missed=missed, total=total,
                                           preview_result=preview_result,
                                           preview_error=preview_error))


@router.post("/ui/trends/scoring/save")
async def trends_scoring_save(
    request: Request,
    formula: str = Form(""),
    formula_enabled: bool = Form(False),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    rule = await _get_or_create_rule(db)
    rule.formula = formula.strip()
    rule.formula_enabled = formula_enabled
    await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/trends?tab=scoring"), status_code=302)


@router.post("/ui/trends/scoring/test")
async def trends_scoring_test(
    request: Request,
    formula: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    if not user:
        return HTMLResponse("Unauthorized", status_code=401)

    completed = (await db.execute(
        select(func.count(WorkoutLog.id)).where(WorkoutLog.status == "completed")
    )).scalar() or 0
    skipped = (await db.execute(
        select(func.count(WorkoutLog.id)).where(WorkoutLog.status == "skipped")
    )).scalar() or 0
    missed = (await db.execute(
        select(func.count(WorkoutLog.id)).where(WorkoutLog.status == "missed")
    )).scalar() or 0
    total = completed + skipped + missed

    result, error = _eval_formula(formula.strip(), completed, skipped, missed, total)
    if error:
        return HTMLResponse(
            f'<span style="color:var(--error)">Error: {error}</span>'
        )
    return HTMLResponse(
        f'<span style="color:var(--success)">{result}</span>'
        f'<span style="color:var(--text-muted);font-size:11px;margin-left:8px;">'
        f'(from {completed} completed, {skipped} skipped, {missed} missed, {total} total)</span>'
    )


# ── Periods tab ────────────────────────────────────────────────────────────

@router.get("/ui/trends/periods")
async def trends_periods(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    periods = (await db.execute(select(TrendPeriod).order_by(TrendPeriod.start_month))).scalars().all()
    return templates.TemplateResponse(request, "_trends_periods.html",
                                      tctx(request, periods=periods, months=MONTHS))


@router.post("/ui/trends/periods/add")
async def trends_periods_add(
    request: Request,
    name: str = Form(...),
    start_month: int = Form(...),
    end_month: int = Form(...),
    description: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    db.add(TrendPeriod(name=name, start_month=start_month,
                        end_month=end_month, description=description or None))
    await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/trends?tab=periods"), status_code=302)


@router.post("/ui/trends/periods/delete")
async def trends_periods_delete(
    request: Request,
    period_id: int = Form(...),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    await db.execute(delete(TrendPeriod).where(TrendPeriod.id == period_id))
    await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/trends?tab=periods"), status_code=302)


# ── Observations tab ───────────────────────────────────────────────────────

@router.get("/ui/trends/observations")
async def trends_observations(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    rows = (await db.execute(
        select(TrendObservation, User)
        .outerjoin(User, User.id == TrendObservation.user_id)
        .order_by(TrendObservation.observed_at.desc())
    )).all()
    observations = [{"obs": r[0], "user": r[1]} for r in rows]
    users = (await db.execute(select(User).order_by(User.username))).scalars().all()
    periods = (await db.execute(select(TrendPeriod).order_by(TrendPeriod.name))).scalars().all()
    return templates.TemplateResponse(request, "_trends_observations.html",
                                      tctx(request, observations=observations,
                                           users=users, periods=periods))


@router.post("/ui/trends/observations/add")
async def trends_observations_add(
    request: Request,
    period_name: str = Form(...),
    category: str = Form(...),
    score: str = Form(""),
    notes: str = Form(""),
    user_id: Optional[int] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    db.add(TrendObservation(
        period_name=period_name, category=category,
        score=score or None, notes=notes or None,
        user_id=user_id or None,
    ))
    await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/trends?tab=observations"), status_code=302)


@router.post("/ui/trends/observations/delete")
async def trends_observations_delete(
    request: Request,
    obs_id: int = Form(...),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    await db.execute(delete(TrendObservation).where(TrendObservation.id == obs_id))
    await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/trends?tab=observations"), status_code=302)
