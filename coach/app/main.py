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
from app.routes.admin import router as admin_router

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
app.include_router(admin_router)
