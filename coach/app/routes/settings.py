import json
import logging
import os
import re
import shutil
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, get_ext_db, get_current_user, redirect_to, tctx
from app.ha_calendar import CATEGORY, create_event, delete_event, get_all_events, update_event
from app.models import User, WorkoutLog

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)

SQLITE_PATH = "/data/coach.db"


def _event_user(event: dict) -> str:
    desc = (event.get("description") or "").lower()
    for tag in re.findall(r'\[([^\]]+)\]', desc):
        if tag != CATEGORY.lower():
            return tag
    return "unknown"


# ── Main page ──────────────────────────────────────────────────────────────

@router.get("/ui/settings")
async def settings_page(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    return templates.TemplateResponse(
        request, "settings.html",
        tctx(request, user=user, active="settings")
    )


# ── Database tab ───────────────────────────────────────────────────────────

@router.get("/ui/settings/db")
async def settings_db(
    request: Request,
    db: AsyncSession = Depends(get_db),
    ext_db: Optional[AsyncSession] = Depends(get_ext_db),
):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)

    sqlite_size_mb = round(os.path.getsize(SQLITE_PATH) / 1024 / 1024, 2) if os.path.exists(SQLITE_PATH) else 0
    local_log_count = (await db.execute(select(func.count(WorkoutLog.id)))).scalar() or 0
    local_last = (await db.execute(select(func.max(WorkoutLog.logged_at)))).scalar()
    rows = (await db.execute(
        select(User, func.count(WorkoutLog.id).label("log_count"))
        .outerjoin(WorkoutLog, WorkoutLog.user_id == User.id)
        .group_by(User.id).order_by(User.username)
    )).all()
    users_data = [{"user": r[0], "log_count": r[1]} for r in rows]

    ext_stats = None
    if ext_db:
        try:
            ext_log_count = (await ext_db.execute(select(func.count(WorkoutLog.id)))).scalar() or 0
            ext_last = (await ext_db.execute(select(func.max(WorkoutLog.logged_at)))).scalar()
            size_row = (await ext_db.execute(text(
                "SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) "
                "FROM information_schema.tables WHERE table_schema = DATABASE() "
                "AND table_name IN ('users', 'workout_logs')"
            ))).scalar()
            ext_stats = {"log_count": ext_log_count, "last": ext_last, "size_mb": size_row or 0}
        except Exception:
            pass

    return templates.TemplateResponse(
        request, "_settings_db.html",
        tctx(request, sqlite_size_mb=sqlite_size_mb, local_log_count=local_log_count,
             local_last=local_last, users_data=users_data, ext_stats=ext_stats)
    )


@router.post("/ui/settings/delete-user-logs")
async def delete_user_logs(
    request: Request, user_id: int = Form(...),
    db: AsyncSession = Depends(get_db), ext_db: Optional[AsyncSession] = Depends(get_ext_db),
):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    await db.execute(delete(WorkoutLog).where(WorkoutLog.user_id == user_id))
    await db.commit()
    if ext_db:
        try:
            await ext_db.execute(delete(WorkoutLog).where(WorkoutLog.user_id == user_id))
            await ext_db.commit()
        except Exception: pass
    return RedirectResponse(url=redirect_to(request, "ui/settings"), status_code=302)


@router.post("/ui/settings/delete-user")
async def delete_user_entry(
    request: Request, user_id: int = Form(...),
    db: AsyncSession = Depends(get_db), ext_db: Optional[AsyncSession] = Depends(get_ext_db),
):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    await db.execute(delete(WorkoutLog).where(WorkoutLog.user_id == user_id))
    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()
    if ext_db:
        try:
            await ext_db.execute(delete(WorkoutLog).where(WorkoutLog.user_id == user_id))
            await ext_db.execute(delete(User).where(User.id == user_id))
            await ext_db.commit()
        except Exception: pass
    return RedirectResponse(url=redirect_to(request, "ui/settings"), status_code=302)


@router.post("/ui/settings/wipe-logs")
async def wipe_logs(
    request: Request,
    db: AsyncSession = Depends(get_db), ext_db: Optional[AsyncSession] = Depends(get_ext_db),
):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    await db.execute(delete(WorkoutLog))
    await db.commit()
    if ext_db:
        try:
            await ext_db.execute(delete(WorkoutLog))
            await ext_db.commit()
        except Exception: pass
    return RedirectResponse(url=redirect_to(request, "ui/settings"), status_code=302)


@router.get("/ui/settings/backup")
async def backup_db(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    if not os.path.exists(SQLITE_PATH):
        return RedirectResponse(url=redirect_to(request, "ui/settings"), status_code=302)
    return FileResponse(SQLITE_PATH, filename="coach_backup.db", media_type="application/octet-stream")


@router.post("/ui/settings/restore")
async def restore_db(
    request: Request, file: UploadFile = File(...), db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    try:
        tmp = "/data/coach_restore_tmp.db"
        with open(tmp, "wb") as f:
            f.write(await file.read())
        shutil.move(tmp, SQLITE_PATH)
        from app.database import local_engine
        await local_engine.dispose()
        logger.info("SQLite database restored")
    except Exception as e:
        logger.error(f"DB restore failed: {e}")
    return RedirectResponse(url=redirect_to(request, "ui/settings"), status_code=302)


# ── Preferences tab ────────────────────────────────────────────────────────

@router.get("/ui/settings/preferences")
async def settings_preferences(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    return templates.TemplateResponse(request, "_settings_preferences.html", tctx(request, user=user))


@router.post("/ui/settings/preferences/save")
async def settings_preferences_save(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    form = await request.form()
    user.display_name = (form.get("display_name") or "").strip() or user.display_name
    user.currency = (form.get("currency") or "$").strip() or "$"
    user.unit_distance = form.get("unit_distance", "km")
    user.unit_weight = form.get("unit_weight", "kg")
    user.week_start = form.get("week_start", "Mon")
    steps_entity = (form.get("steps_entity") or "").strip()
    user.steps_entity = steps_entity or None
    selected_metrics = form.getlist("health_metrics")
    user.health_metrics = ",".join(selected_metrics)
    await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/settings?tab=preferences"), status_code=303)


# ── Notifications tab ──────────────────────────────────────────────────────

@router.get("/ui/settings/notifications")
async def settings_notifications(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    return templates.TemplateResponse(
        request, "_settings_notifications.html",
        tctx(request, user=user, notify_service=os.getenv("NOTIFY_SERVICE", ""))
    )


# ── Skills tab ─────────────────────────────────────────────────────────────

@router.get("/ui/settings/skills")
async def settings_skills(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    return templates.TemplateResponse(request, "_settings_skills.html", tctx(request, user=user))


# ── Calendar tab ───────────────────────────────────────────────────────────

@router.get("/ui/settings/calendar")
async def settings_calendar(
    request: Request, user_filter: str = "", db: AsyncSession = Depends(get_db),
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
        request, "_settings_calendar.html",
        tctx(request, events=events, all_users=all_users,
             user_filter=user_filter, event_user=_event_user)
    )


@router.get("/ui/settings/calendar/edit")
async def calendar_edit_form(
    request: Request, uid: str = "", db: AsyncSession = Depends(get_db),
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
        return RedirectResponse(url=redirect_to(request, "ui/settings?tab=calendar"), status_code=302)

    start_str = event.get("start", {}).get("dateTime", "")
    end_str = event.get("end", {}).get("dateTime", "")
    start_date = start_time = ""
    duration = 60
    try:
        s = datetime.fromisoformat(start_str)
        e2 = datetime.fromisoformat(end_str)
        duration = int((e2 - s).total_seconds() / 60)
        start_date = s.strftime("%Y-%m-%d")
        start_time = s.strftime("%H:%M")
    except Exception:
        pass

    return templates.TemplateResponse(
        request, "calendar_edit.html",
        tctx(request, user=user, active="settings",
             event=event, uid=uid,
             start_date=start_date, start_time=start_time, duration=duration)
    )


@router.post("/ui/settings/calendar/edit")
async def calendar_edit_submit(
    request: Request,
    uid: str = Form(...), title: str = Form(...), date: str = Form(...),
    start_time: str = Form(...), duration: int = Form(60), description: str = Form(""),
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
    return RedirectResponse(url=redirect_to(request, "ui/settings?tab=calendar"), status_code=302)


@router.post("/ui/settings/calendar/delete")
async def calendar_delete(
    request: Request, uid: str = Form(...), db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    try:
        await delete_event(uid)
    except Exception as e:
        logger.error(f"Calendar delete failed: {e}")
    return RedirectResponse(url=redirect_to(request, "ui/settings?tab=calendar"), status_code=302)


@router.get("/ui/settings/calendar/backup")
async def calendar_backup(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    try:
        events = await get_all_events()
    except Exception:
        events = []
    return Response(
        content=json.dumps(events, indent=2, default=str),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=calendar_backup.json"},
    )


@router.post("/ui/settings/calendar/restore")
async def calendar_restore(
    request: Request,
    file: UploadFile = File(...),
    replace: bool = Form(False),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    try:
        content = await file.read()
        to_import = json.loads(content)
        if replace:
            existing = await get_all_events()
            for ev in existing:
                if ev.get("uid"):
                    try: await delete_event(ev["uid"])
                    except Exception: pass
            logger.info(f"Cleared {len(existing)} events before restore")
        imported = 0
        for ev in to_import:
            s = ev.get("start", {}).get("dateTime", "")
            e2 = ev.get("end", {}).get("dateTime", "")
            if not s or not e2:
                continue
            await create_event(
                summary=ev.get("summary", "Event"),
                start=datetime.fromisoformat(s),
                end=datetime.fromisoformat(e2),
                description=ev.get("description"),
            )
            imported += 1
        logger.info(f"Calendar restore: {imported} events imported")
    except Exception as e:
        logger.error(f"Calendar restore failed: {e}")
    return RedirectResponse(url=redirect_to(request, "ui/settings?tab=calendar"), status_code=302)
