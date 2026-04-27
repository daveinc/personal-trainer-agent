import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, get_current_user, redirect_to, tctx
from app.models import RoutineState

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)

ROUTINES = [
    {
        "slug": "onboarding",
        "name": "Onboarding",
        "description": "Get to know the user — current situation, obstacles, and primary goal. Runs once on first login.",
    },
    {
        "slug": "goal_setup",
        "name": "Goal Setup",
        "description": "Guide the user through setting a new goal: what, when, and what success looks like. Requires at least one milestone before activation.",
    },
    {
        "slug": "milestone_breakdown",
        "name": "Milestone & Roadmap Breakdown",
        "description": "Break an active goal into milestones with target dates and weekly actions. Surfaces the next step, not the end goal.",
    },
    {
        "slug": "blocker_identification",
        "name": "Blocker Identification",
        "description": "At each check-in, ask what's getting in the way. Log blockers per goal and flag repeats.",
    },
    {
        "slug": "weekly_checkin",
        "name": "Weekly Check-in",
        "description": "Structured weekly conversation: did you hit last week's action, what's the plan this week, any blockers?",
    },
    {
        "slug": "progress_tracking",
        "name": "Progress Tracking & Reporting",
        "description": "Generate monthly summaries: what was set, what was done, what slipped. Track trend over time.",
    },
    {
        "slug": "accountability_nudges",
        "name": "Accountability Nudges",
        "description": "Send HA notifications for missed check-ins or overdue milestones. Acknowledge consistent wins.",
    },
    {
        "slug": "ongoing_support",
        "name": "Ongoing Support Loop",
        "description": "After each check-in, deliver one focused suggestion for the coming week based on the user's current milestone and blockers.",
    },
    {
        "slug": "reassessment",
        "name": "Reassessment Triggers",
        "description": "If a goal is missed 3 times in a row, prompt a structured reassessment. Reframe as updating the roadmap, not giving up.",
    },
    {
        "slug": "habit_building",
        "name": "Habit & Routine Building",
        "description": "Track daily/weekly habits tied to a goal. Flag habits established after 30 days of consistency.",
    },
]


async def _sync_states(db: AsyncSession) -> dict[str, RoutineState]:
    existing = {r.slug: r for r in (await db.execute(select(RoutineState))).scalars().all()}
    for r in ROUTINES:
        if r["slug"] not in existing:
            state = RoutineState(slug=r["slug"])
            db.add(state)
            existing[r["slug"]] = state
    await db.commit()
    for slug in existing:
        if existing[slug].id is None:
            await db.refresh(existing[slug])
    return existing


@router.get("/ui/routines")
async def routines_page(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    states = await _sync_states(db)
    routines = [{"slug": r["slug"], "name": r["name"], "description": r["description"],
                 "state": states[r["slug"]]} for r in ROUTINES]
    return templates.TemplateResponse(request, "routines.html",
                                      tctx(request, user=user, active="routines", routines=routines))


@router.post("/ui/routines/{slug}/enable")
async def routine_enable(slug: str, request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    states = await _sync_states(db)
    if slug in states:
        states[slug].enabled = True
        await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/routines"), status_code=303)


@router.post("/ui/routines/{slug}/disable")
async def routine_disable(slug: str, request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    states = await _sync_states(db)
    if slug in states:
        states[slug].enabled = False
        states[slug].status = "idle"
        await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/routines"), status_code=303)


@router.post("/ui/routines/{slug}/run")
async def routine_run(slug: str, request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    states = await _sync_states(db)
    if slug in states and states[slug].enabled:
        states[slug].status = "running"
        states[slug].last_run = datetime.now(timezone.utc)
        await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/routines"), status_code=303)


@router.post("/ui/routines/{slug}/stop")
async def routine_stop(slug: str, request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    states = await _sync_states(db)
    if slug in states:
        states[slug].status = "idle"
        await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/routines"), status_code=303)
