import app.config as _config
_config.load()

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.database import init_db, setup_ext_engine
from app.deps import redirect_to
from app.routes.auth import router as auth_router
from app.routes.ui import router as ui_router
from app.routes.fitness import router as fitness_router
from app.routes.settings import router as settings_router
from app.routes.categories import router as categories_router
from app.routes.trends import router as trends_router
from app.routes.routines import router as routines_router
from app.routes.onboarding import router as onboarding_router
from app.routes.profile import router as profile_router
from app.routes.schedule import router as schedule_router
from app.routes.checkins import router as checkins_router
from app.routes.finances import router as finances_router
from app.routes.health import router as health_router
from app.routes.learning import router as learning_router
from app.routes.relationships import router as relationships_router
from app.routes.webhook import router as webhook_router
from app.routes.goals import router as goals_router
from app.routes.pipeline import router as pipeline_router
from app.routes.event_log import router as event_log_router
from app.routes.calendar_actions import router as calendar_actions_router
from app.services.scheduler import run_scheduler
from app.services.ha_events import run_event_listener

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_ext_engine()
    await init_db()
    asyncio.create_task(run_scheduler())
    asyncio.create_task(run_event_listener())
    yield


app = FastAPI(title="Coach", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def onboarding_gate(request: Request, call_next):
    path = request.url.path
    if (path.startswith("/ui/") and
            not path.startswith("/ui/onboarding") and
            not path.startswith("/ui/login") and
            not path.startswith("/ui/profile")):
        try:
            from app.database import LocalSession
            from app.models import User
            from sqlalchemy import select
            async with LocalSession() as db:
                user = None
                ha_username = request.headers.get("X-Remote-User-Name")
                if ha_username:
                    user = (await db.execute(select(User).where(User.username == ha_username))).scalar_one_or_none()
                else:
                    uid = request.cookies.get("uid")
                    if uid:
                        user = (await db.execute(select(User).where(User.id == int(uid)))).scalar_one_or_none()
                if user and not user.onboarding_complete:
                    ingress = request.headers.get("X-Ingress-Path", "")
                    from fastapi.responses import RedirectResponse
                    return RedirectResponse(url=f"{ingress}/ui/onboarding", status_code=302)
        except Exception:
            pass
    return await call_next(request)


@app.middleware("http")
async def ingress_root_path(request: Request, call_next):
    ingress_path = request.headers.get("X-Ingress-Path", "")
    if ingress_path:
        request.scope["root_path"] = ingress_path
    return await call_next(request)


@app.get("/")
async def root(request: Request):
    if request.headers.get("X-Remote-User-Name"):
        return RedirectResponse(url=redirect_to(request, "ui/dashboard"), status_code=302)
    return RedirectResponse(url=redirect_to(request, "ui/login"), status_code=302)


app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(auth_router)
app.include_router(ui_router)
app.include_router(fitness_router)
app.include_router(settings_router)
app.include_router(categories_router)
app.include_router(trends_router)
app.include_router(routines_router)
app.include_router(onboarding_router)
app.include_router(profile_router)
app.include_router(schedule_router)
app.include_router(checkins_router)
app.include_router(finances_router)
app.include_router(health_router)
app.include_router(learning_router)
app.include_router(relationships_router)
app.include_router(webhook_router)
app.include_router(goals_router)
app.include_router(pipeline_router)
app.include_router(event_log_router)
app.include_router(calendar_actions_router)
