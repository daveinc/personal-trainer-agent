from typing import Optional
from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import Session
from app.models import User


async def get_db():
    async with Session() as session:
        yield session


async def get_current_user(request: Request, db: AsyncSession) -> Optional[User]:
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
    """Build template context with root injected."""
    return {"root": root_path(request), **kwargs}
