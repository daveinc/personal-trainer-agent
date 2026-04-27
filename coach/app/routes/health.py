import logging
from datetime import date
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, get_current_user, redirect_to, tctx
from app.models import HealthEntry, Appointment

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)

METRIC_LABELS = {
    "weight":     "Weight",
    "sleep":      "Sleep",
    "bp":         "Blood Pressure",
    "resting_hr": "Resting HR",
    "medication": "Medication",
}


@router.get("/ui/health")
async def health_page(request: Request, expand: str = None, edit_appt: int = None,
                      db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)

    metrics = [m.strip() for m in (user.health_metrics or "").split(",") if m.strip()]
    today_str = date.today().strftime("%Y-%m-%d")

    latest = {}
    history = {}
    today_logged = {}
    for metric in metrics:
        entries = (await db.execute(
            select(HealthEntry)
            .where(HealthEntry.user_id == user.id, HealthEntry.metric == metric)
            .order_by(HealthEntry.logged_at.desc())
            .limit(10)
        )).scalars().all()
        history[metric] = entries
        latest[metric] = entries[0] if entries else None
        today_logged[metric] = next((e for e in entries if e.log_date == today_str), None)

    appointments = (await db.execute(
        select(Appointment)
        .where(Appointment.user_id == user.id)
        .order_by(Appointment.appt_date)
    )).scalars().all()

    edit_appt_obj = next((a for a in appointments if a.id == edit_appt), None) if edit_appt else None

    return templates.TemplateResponse(request, "health.html", tctx(
        request, user=user, active="health",
        metrics=metrics, metric_labels=METRIC_LABELS,
        latest=latest, history=history, today_logged=today_logged,
        today_str=today_str,
        appointments=appointments, edit_appt=edit_appt_obj,
        unit_weight=getattr(user, "unit_weight", "kg") or "kg",
        expand=expand,
    ))


@router.post("/ui/health/entry/log")
async def entry_log(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    form = await request.form()
    metric = form.get("metric", "")
    today_str = date.today().strftime("%Y-%m-%d")
    try:
        value = float(form.get("value") or 0)
    except ValueError:
        value = 0.0
    value2 = None
    try:
        v2 = form.get("value2", "")
        if v2:
            value2 = float(v2)
    except ValueError:
        pass
    db.add(HealthEntry(user_id=user.id, metric=metric, value=value,
                       value2=value2, log_date=today_str))
    await db.commit()
    return RedirectResponse(url=redirect_to(request, f"ui/health?expand={metric}"), status_code=303)


@router.post("/ui/health/entry/{entry_id}/delete")
async def entry_delete(entry_id: int, request: Request,
                       metric: str = Form(""), db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    await db.execute(delete(HealthEntry).where(
        HealthEntry.id == entry_id, HealthEntry.user_id == user.id
    ))
    await db.commit()
    return RedirectResponse(url=redirect_to(request, f"ui/health?expand={metric}"), status_code=303)


@router.post("/ui/health/appointment/add")
async def appt_add(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    form = await request.form()
    db.add(Appointment(
        user_id=user.id,
        title=(form.get("title") or "").strip(),
        doctor=(form.get("doctor") or "").strip() or None,
        location=(form.get("location") or "").strip() or None,
        appt_date=form.get("appt_date", ""),
        appt_time=form.get("appt_time") or None,
        notes=(form.get("notes") or "").strip() or None,
    ))
    await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/health"), status_code=303)


@router.post("/ui/health/appointment/{appt_id}/save")
async def appt_save(appt_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    appt = (await db.execute(
        select(Appointment).where(Appointment.id == appt_id, Appointment.user_id == user.id)
    )).scalar_one_or_none()
    if appt:
        form = await request.form()
        appt.title = (form.get("title") or appt.title).strip()
        appt.doctor = (form.get("doctor") or "").strip() or None
        appt.location = (form.get("location") or "").strip() or None
        appt.appt_date = form.get("appt_date", appt.appt_date)
        appt.appt_time = form.get("appt_time") or None
        appt.notes = (form.get("notes") or "").strip() or None
        await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/health"), status_code=303)


@router.post("/ui/health/appointment/{appt_id}/delete")
async def appt_delete(appt_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    await db.execute(delete(Appointment).where(
        Appointment.id == appt_id, Appointment.user_id == user.id
    ))
    await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/health"), status_code=303)
