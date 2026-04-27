import app.config as _config
_config.load()

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

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_ext_engine()
    await init_db()
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
            not path.startswith("/ui/login")):
        uid = request.cookies.get("uid")
        if uid:
            try:
                from app.database import LocalSession
                from app.models import User
                from sqlalchemy import select
                async with LocalSession() as db:
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
