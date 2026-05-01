from datetime import date
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, get_current_user, redirect_to, tctx
from app.models import Goal, GoalProgress

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _steps_done(progress: list) -> int:
    return sum(p.steps_added for p in progress)


@router.get("/ui/goals")
async def goals_page(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)

    goals = (await db.execute(
        select(Goal)
        .where(Goal.user_id == user.id)
        .order_by(Goal.is_active.desc(), Goal.created_at.desc())
    )).scalars().all()

    progress_map = {}
    for goal in goals:
        entries = (await db.execute(
            select(GoalProgress)
            .where(GoalProgress.goal_id == goal.id)
            .order_by(GoalProgress.created_at.desc())
        )).scalars().all()
        progress_map[goal.id] = entries

    return templates.TemplateResponse(request, "goals.html", tctx(
        request, user=user, active="goals",
        goals=goals, progress_map=progress_map,
        steps_done=_steps_done,
    ))


@router.post("/ui/goals/add")
async def goals_add(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)

    form = await request.form()
    today = date.today().strftime("%Y-%m-%d")

    try:
        target_value = float(form.get("target_value")) if form.get("target_value") else None
    except ValueError:
        target_value = None
    try:
        start_value = float(form.get("start_value")) if form.get("start_value") else None
    except ValueError:
        start_value = None
    try:
        total_steps = int(form.get("total_steps")) if form.get("total_steps") else None
    except ValueError:
        total_steps = None

    db.add(Goal(
        user_id=user.id,
        title=(form.get("title") or "").strip(),
        category=(form.get("category") or "").strip(),
        metric=(form.get("metric") or "").strip() or None,
        target_value=target_value,
        target_unit=(form.get("target_unit") or "").strip() or None,
        start_value=start_value,
        total_steps=total_steps,
        start_date=form.get("start_date") or today,
        deadline=form.get("deadline") or None,
        notes=(form.get("notes") or "").strip() or None,
    ))
    await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/goals"), status_code=303)


@router.post("/ui/goals/{goal_id}/progress")
async def goals_progress(goal_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)

    goal = (await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == user.id)
    )).scalar_one_or_none()
    if not goal:
        return RedirectResponse(url=redirect_to(request, "ui/goals"), status_code=303)

    form = await request.form()
    try:
        steps = max(1, int(form.get("steps", 1)))
    except ValueError:
        steps = 1
    note = (form.get("note") or "").strip() or None
    today = date.today().strftime("%Y-%m-%d")

    db.add(GoalProgress(
        goal_id=goal.id,
        user_id=user.id,
        steps_added=steps,
        note=note,
        logged_at=today,
    ))

    # auto-complete if steps done >= total_steps
    if goal.total_steps:
        existing = (await db.execute(
            select(GoalProgress).where(GoalProgress.goal_id == goal.id)
        )).scalars().all()
        if _steps_done(existing) + steps >= goal.total_steps:
            goal.achieved_at = today
            goal.is_active = False

    await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/goals"), status_code=303)


@router.post("/ui/goals/{goal_id}/complete")
async def goals_complete(goal_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)

    goal = (await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == user.id)
    )).scalar_one_or_none()
    if goal:
        goal.achieved_at = date.today().strftime("%Y-%m-%d")
        goal.is_active = False
        await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/goals"), status_code=303)


@router.post("/ui/goals/{goal_id}/reopen")
async def goals_reopen(goal_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)

    goal = (await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == user.id)
    )).scalar_one_or_none()
    if goal:
        goal.achieved_at = None
        goal.is_active = True
        await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/goals"), status_code=303)


@router.post("/ui/goals/{goal_id}/delete")
async def goals_delete(goal_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)

    await db.execute(delete(GoalProgress).where(GoalProgress.goal_id == goal_id))
    await db.execute(delete(Goal).where(Goal.id == goal_id, Goal.user_id == user.id))
    await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/goals"), status_code=303)
