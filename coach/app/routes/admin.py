import logging
import os
import shutil
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, get_ext_db, get_current_user, redirect_to, tctx
from app.models import User, WorkoutLog

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)

SQLITE_PATH = "/data/coach.db"


@router.get("/ui/admin")
async def admin_page(
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
        .group_by(User.id)
        .order_by(User.username)
    )).all()
    users_data = [{"user": row[0], "log_count": row[1]} for row in rows]

    ext_stats = None
    if ext_db:
        try:
            ext_log_count = (await ext_db.execute(select(func.count(WorkoutLog.id)))).scalar() or 0
            ext_last = (await ext_db.execute(select(func.max(WorkoutLog.logged_at)))).scalar()
            size_row = (await ext_db.execute(text(
                "SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) "
                "FROM information_schema.tables "
                "WHERE table_schema = DATABASE() "
                "AND table_name IN ('users', 'workout_logs')"
            ))).scalar()
            ext_stats = {"log_count": ext_log_count, "last": ext_last, "size_mb": size_row or 0}
        except Exception:
            pass

    return templates.TemplateResponse(
        request, "admin.html",
        tctx(request, user=user, active="admin",
             sqlite_size_mb=sqlite_size_mb,
             local_log_count=local_log_count,
             local_last=local_last,
             users_data=users_data,
             ext_stats=ext_stats)
    )


@router.post("/ui/admin/delete-user-logs")
async def delete_user_logs(
    request: Request,
    user_id: int = Form(...),
    db: AsyncSession = Depends(get_db),
    ext_db: Optional[AsyncSession] = Depends(get_ext_db),
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
        except Exception:
            pass
    return RedirectResponse(url=redirect_to(request, "ui/admin"), status_code=302)


@router.post("/ui/admin/delete-user")
async def delete_user_entry(
    request: Request,
    user_id: int = Form(...),
    db: AsyncSession = Depends(get_db),
    ext_db: Optional[AsyncSession] = Depends(get_ext_db),
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
        except Exception:
            pass
    return RedirectResponse(url=redirect_to(request, "ui/admin"), status_code=302)


@router.post("/ui/admin/wipe-logs")
async def wipe_logs(
    request: Request,
    db: AsyncSession = Depends(get_db),
    ext_db: Optional[AsyncSession] = Depends(get_ext_db),
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
        except Exception:
            pass
    return RedirectResponse(url=redirect_to(request, "ui/admin"), status_code=302)


@router.get("/ui/admin/backup")
async def backup(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    if not os.path.exists(SQLITE_PATH):
        return RedirectResponse(url=redirect_to(request, "ui/admin"), status_code=302)
    return FileResponse(SQLITE_PATH, filename="coach_backup.db", media_type="application/octet-stream")


@router.post("/ui/admin/restore")
async def restore_db(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
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
    return RedirectResponse(url=redirect_to(request, "ui/admin"), status_code=302)
