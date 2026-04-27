from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, get_current_user, redirect_to, tctx

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

PAGES = [
    ("health",        "Health"),
    ("finances",      "Finances"),
    ("learning",      "Learning"),
    ("relationships", "Relationships"),
    ("checkins",      "Check-ins"),
    ("milestones",    "Milestones"),
    ("challenges",    "Challenges"),
]


def _make_route(slug: str):
    async def handler(request: Request, db: AsyncSession = Depends(get_db)):
        user = await get_current_user(request, db)
        if not user:
            return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)
        return templates.TemplateResponse(
            request, f"{slug}.html",
            tctx(request, user=user, active=slug)
        )
    handler.__name__ = f"page_{slug}"
    return handler


for _slug, _label in PAGES:
    router.get(f"/ui/{_slug}")(_make_route(_slug))
