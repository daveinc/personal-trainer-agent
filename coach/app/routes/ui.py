from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, get_current_user, redirect_to, tctx
from app.ha_calendar import check_connection

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/ui/login")
async def login(request: Request):
    return templates.TemplateResponse(request, "login.html", tctx(request))


@router.get("/ui/dashboard")
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    ha_ok = await check_connection()
    hour = datetime.now(timezone.utc).hour
    greeting = "morning" if hour < 12 else "afternoon" if hour < 18 else "evening"
    return templates.TemplateResponse(request, "dashboard.html", tctx(request, user=user, ha_ok=ha_ok, greeting=greeting))


@router.get("/ui/fitness")
async def fitness(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    return templates.TemplateResponse(request, "fitness.html", tctx(request, user=user))
