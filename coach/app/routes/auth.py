from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, redirect_to
from app.models import User

router = APIRouter()


@router.post("/auth/login")
async def login(
    request: Request,
    username: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    username = username.strip().lower()
    if not username:
        return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        user = User(username=username, display_name=username.capitalize())
        db.add(user)
        await db.commit()
        await db.refresh(user)

    response = RedirectResponse(url=redirect_to(request, "ui/dashboard"), status_code=302)
    response.set_cookie("uid", str(user.id), httponly=True, samesite="lax")
    return response


@router.get("/auth/logout")
async def logout(request: Request):
    response = RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
    response.delete_cookie("uid")
    return response
