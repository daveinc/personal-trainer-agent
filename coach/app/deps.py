from typing import Optional
from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import LocalSession
from app.models import User


async def get_db():
    async with LocalSession() as session:
        yield session


async def get_ext_db():
    from app.database import ExtSession
    if ExtSession is None:
        yield None
        return
    async with ExtSession() as session:
        yield session


async def get_current_user(request: Request, db: AsyncSession) -> Optional[User]:
    ha_username = request.headers.get("X-Remote-User-Name")
    if ha_username:
        ha_display = request.headers.get("X-Remote-User-Display-Name", ha_username)
        result = await db.execute(select(User).where(User.username == ha_username))
        user = result.scalar_one_or_none()
        if not user:
            user = User(username=ha_username, display_name=ha_display)
            db.add(user)
            await db.commit()
            await db.refresh(user)
        return user

    uid = request.cookies.get("uid")
    if not uid:
        return None
    try:
        result = await db.execute(select(User).where(User.id == int(uid)))
        return result.scalar_one_or_none()
    except (ValueError, Exception):
        return None


def redirect_to(request: Request, path: str) -> str:
    root = request.headers.get("X-Ingress-Path", "")
    return f"{root}/{path.lstrip('/')}"


def root_path(request: Request) -> str:
    return request.scope.get("root_path", "")


def tctx(request: Request, **kwargs) -> dict:
    return {"root": root_path(request), **kwargs}
