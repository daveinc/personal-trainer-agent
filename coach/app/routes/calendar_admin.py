import json
import logging
import re
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, get_current_user, redirect_to, tctx
from app.ha_calendar import (
    CATEGORY, create_event, delete_event, get_all_events, update_event,
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)


def _event_user(event: dict) -> str:
    desc = (event.get("description") or "").lower()
    for tag in re.findall(r'\[([^\]]+)\]', desc):
        if tag != CATEGORY.lower():
            return tag
    return "unknown"


def _parse_times(event: dict):
    start_str = event.get("start", {}).get("dateTime", "")
    end_str = event.get("end", {}).get("dateTime", "")
    try:
        start_dt = datetime.fromisoformat(start_str)
        end_dt = datetime.fromisoformat(end_str)
        duration = int((end_dt - start_dt).total_seconds() / 60)
        return start_dt.strftime("%Y-%m-%d"), start_dt.strftime("%H:%M"), duration
    except Exception:
        return "", "", 60


@router.get("/ui/admin/calendar")
async def calendar_admin(
    request: Request,
    user_filter: str = "",
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)

    try:
        events = await get_all_events()
    except Exception:
        events = []

    all_users = sorted(set(_event_user(e) for e in events))
    if user_filter:
        events = [e for e in events if _event_user(e) == user_filter]
    events.sort(key=lambda e: e.get("start", {}).get("dateTime", ""))

    return templates.TemplateResponse(
        request, "calendar_admin.html",
        tctx(request, user=user, active="calendar_admin",
             events=events, all_users=all_users, user_filter=user_filter,
             event_user=_event_user)
    )


@router.get("/ui/admin/calendar/edit")
async def calendar_edit_form(
    request: Request,
    uid: str = "",
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)

    try:
        events = await get_all_events()
        event = next((e for e in events if e.get("uid") == uid), None)
    except Exception:
        event = None

    if not event:
        return RedirectResponse(url=redirect_to(request, "ui/admin/calendar"), status_code=302)

    start_date, start_time, duration = _parse_times(event)

    return templates.TemplateResponse(
        request, "calendar_edit.html",
        tctx(request, user=user, active="calendar_admin",
             event=event, uid=uid,
             start_date=start_date, start_time=start_time, duration=duration)
    )


@router.post("/ui/admin/calendar/edit")
async def calendar_edit_submit(
    request: Request,
    uid: str = Form(...),
    title: str = Form(...),
    date: str = Form(...),
    start_time: str = Form(...),
    duration: int = Form(60),
    description: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)

    start_dt = datetime.fromisoformat(f"{date}T{start_time}:00")
    end_dt = start_dt + timedelta(minutes=duration)

    try:
        await update_event(uid=uid, summary=title, start=start_dt, end=end_dt,
                           description=description or None)
    except Exception as e:
        logger.error(f"Calendar update failed: {e}")

    return RedirectResponse(url=redirect_to(request, "ui/admin/calendar"), status_code=302)


@router.post("/ui/admin/calendar/delete")
async def calendar_delete(
    request: Request,
    uid: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    try:
        await delete_event(uid)
    except Exception as e:
        logger.error(f"Calendar delete failed: {e}")
    return RedirectResponse(url=redirect_to(request, "ui/admin/calendar"), status_code=302)


@router.get("/ui/admin/calendar/backup")
async def calendar_backup(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    try:
        events = await get_all_events()
    except Exception:
        events = []
    content = json.dumps(events, indent=2, default=str)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=calendar_backup.json"},
    )


@router.post("/ui/admin/calendar/restore")
async def calendar_restore(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    try:
        content = await file.read()
        events = json.loads(content)
        imported = 0
        for event in events:
            summary = event.get("summary", "Workout")
            start_str = event.get("start", {}).get("dateTime", "")
            end_str = event.get("end", {}).get("dateTime", "")
            description = event.get("description")
            if not start_str or not end_str:
                continue
            await create_event(
                summary=summary,
                start=datetime.fromisoformat(start_str),
                end=datetime.fromisoformat(end_str),
                description=description,
            )
            imported += 1
        logger.info(f"Calendar restore: imported {imported} events")
    except Exception as e:
        logger.error(f"Calendar restore failed: {e}")
    return RedirectResponse(url=redirect_to(request, "ui/admin/calendar"), status_code=302)
