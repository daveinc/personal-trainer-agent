import logging
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, get_current_user, redirect_to, tctx
from app.models import PipelineJob, PipelineNote, PIPELINE_STAGES, PIPELINE_STAGE_LABELS

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)


@router.get("/ui/pipeline")
async def pipeline_page(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)

    jobs = (await db.execute(
        select(PipelineJob)
        .where(PipelineJob.user_id == user.id, PipelineJob.is_active == True)
        .order_by(PipelineJob.updated_at.desc())
    )).scalars().all()

    by_stage = {s: [] for s in PIPELINE_STAGES}
    total_active_value = 0.0
    for job in jobs:
        by_stage.setdefault(job.stage, []).append(job)
        total_active_value += job.value or 0.0

    return templates.TemplateResponse(request, "pipeline.html", tctx(
        request, user=user, active="pipeline",
        jobs=jobs,
        by_stage=by_stage,
        stages=PIPELINE_STAGES,
        stage_labels=PIPELINE_STAGE_LABELS,
        total_active_value=total_active_value,
    ))


@router.post("/ui/pipeline/add")
async def pipeline_add(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)

    form = await request.form()
    title = (form.get("title") or "").strip()
    if not title:
        return RedirectResponse(url=redirect_to(request, "ui/pipeline"), status_code=303)

    try:
        value = float(form.get("value") or 0) or None
    except ValueError:
        value = None

    job = PipelineJob(
        user_id=user.id,
        title=title,
        client=(form.get("client") or "").strip() or None,
        location=(form.get("location") or "").strip() or None,
        stage=form.get("stage") or "marketing",
        value=value,
        due_date=(form.get("due_date") or "").strip() or None,
        notes=(form.get("notes") or "").strip() or None,
    )
    db.add(job)
    await db.commit()
    return RedirectResponse(url=redirect_to(request, "ui/pipeline"), status_code=303)


@router.post("/ui/pipeline/{job_id}/stage")
async def pipeline_set_stage(job_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)

    job = (await db.execute(
        select(PipelineJob).where(PipelineJob.id == job_id, PipelineJob.user_id == user.id)
    )).scalar_one_or_none()

    if job:
        form = await request.form()
        new_stage = form.get("stage") or job.stage
        if new_stage in PIPELINE_STAGES:
            job.stage = new_stage
            await db.commit()

    return RedirectResponse(url=redirect_to(request, "ui/pipeline"), status_code=303)


@router.post("/ui/pipeline/{job_id}/advance")
async def pipeline_advance(job_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)

    job = (await db.execute(
        select(PipelineJob).where(PipelineJob.id == job_id, PipelineJob.user_id == user.id)
    )).scalar_one_or_none()

    if job:
        idx = PIPELINE_STAGES.index(job.stage) if job.stage in PIPELINE_STAGES else 0
        if idx < len(PIPELINE_STAGES) - 1:
            job.stage = PIPELINE_STAGES[idx + 1]
            await db.commit()

    return RedirectResponse(url=redirect_to(request, "ui/pipeline"), status_code=303)


@router.post("/ui/pipeline/{job_id}/note")
async def pipeline_add_note(job_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)

    form = await request.form()
    body = (form.get("body") or "").strip()
    if body:
        note = PipelineNote(job_id=job_id, user_id=user.id, body=body)
        db.add(note)
        await db.commit()

    return RedirectResponse(url=redirect_to(request, f"ui/pipeline/{job_id}"), status_code=303)


@router.get("/ui/pipeline/{job_id}")
async def pipeline_job_detail(job_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)

    job = (await db.execute(
        select(PipelineJob).where(PipelineJob.id == job_id, PipelineJob.user_id == user.id)
    )).scalar_one_or_none()

    if not job:
        return RedirectResponse(url=redirect_to(request, "ui/pipeline"), status_code=303)

    notes = (await db.execute(
        select(PipelineNote).where(PipelineNote.job_id == job_id).order_by(PipelineNote.created_at)
    )).scalars().all()

    return templates.TemplateResponse(request, "pipeline_job.html", tctx(
        request, user=user, active="pipeline",
        job=job, notes=notes,
        stages=PIPELINE_STAGES,
        stage_labels=PIPELINE_STAGE_LABELS,
    ))


@router.post("/ui/pipeline/{job_id}/archive")
async def pipeline_archive(job_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)

    job = (await db.execute(
        select(PipelineJob).where(PipelineJob.id == job_id, PipelineJob.user_id == user.id)
    )).scalar_one_or_none()

    if job:
        job.is_active = False
        await db.commit()

    return RedirectResponse(url=redirect_to(request, "ui/pipeline"), status_code=303)
