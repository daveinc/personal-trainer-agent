import logging
import os
from datetime import datetime, timezone, timedelta

from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase

logger = logging.getLogger(__name__)

LOCAL_DB_URL = "sqlite+aiosqlite:////data/coach.db"

local_engine = create_async_engine(LOCAL_DB_URL, echo=False)
LocalSession = sessionmaker(local_engine, class_=AsyncSession, expire_on_commit=False)

ext_engine = None
ExtSession = None


class Base(DeclarativeBase):
    pass


class ExtBase(DeclarativeBase):
    pass


def _ext_db_url() -> str:
    host = os.getenv("DB_HOST", "").strip()
    if not host:
        return ""
    port = os.getenv("DB_PORT", "3306").strip() or "3306"
    name = os.getenv("DB_NAME", "").strip() or "homeassistant"
    user = os.getenv("DB_USER", "").strip()
    password = os.getenv("DB_PASSWORD", "").strip()
    return f"mysql+aiomysql://{user}:{password}@{host}:{port}/{name}"


def setup_ext_engine():
    global ext_engine, ExtSession
    url = _ext_db_url()
    if not url:
        return
    try:
        ext_engine = create_async_engine(url, echo=False, pool_pre_ping=True)
        ExtSession = sessionmaker(ext_engine, class_=AsyncSession, expire_on_commit=False)
        logger.info(f"External DB configured: {os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME', 'coach')}")
    except Exception as e:
        logger.error(f"External DB setup failed: {e}")


async def _maybe_create_ext_db():
    name = os.getenv("DB_NAME", "").strip()
    if not name or name == "homeassistant":
        return
    host = os.getenv("DB_HOST", "").strip()
    port = int(os.getenv("DB_PORT", "3306") or "3306")
    user = os.getenv("DB_USER", "").strip()
    password = os.getenv("DB_PASSWORD", "").strip()
    try:
        import aiomysql
        conn = await aiomysql.connect(host=host, port=port, user=user, password=password)
        async with conn.cursor() as cur:
            await cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{name}` "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.close()
        logger.info(f"External DB '{name}' ready")
    except Exception as e:
        logger.warning(f"Could not create '{name}', will try connecting anyway: {e}")


async def _migrate_local(conn):
    migrations = [
        "ALTER TABLE users ADD COLUMN onboarding_complete BOOLEAN DEFAULT 0",
        "ALTER TABLE users ADD COLUMN unit_distance VARCHAR(8) DEFAULT 'km'",
        "ALTER TABLE slots ADD COLUMN notify_before INTEGER",
        "ALTER TABLE users ADD COLUMN week_start VARCHAR(3) DEFAULT 'Mon'",
        "ALTER TABLE users ADD COLUMN currency VARCHAR(8) DEFAULT '$'",
        "ALTER TABLE users ADD COLUMN savings_target REAL DEFAULT 0.0",
        "ALTER TABLE users ADD COLUMN health_metrics VARCHAR(256) DEFAULT ''",
        "ALTER TABLE users ADD COLUMN unit_weight VARCHAR(4) DEFAULT 'kg'",
        "ALTER TABLE users ADD COLUMN steps_entity VARCHAR(128)",
    ]
    for sql in migrations:
        try:
            await conn.execute(text(sql))
        except Exception:
            pass


async def init_db():
    async with local_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _migrate_local(conn)

    if ext_engine:
        await _maybe_create_ext_db()
        try:
            async with ext_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                await conn.run_sync(ExtBase.metadata.create_all)
            logger.info("External DB tables ready")
        except Exception as e:
            logger.error(f"External DB init failed: {e}")

    await _prune_local()


async def _prune_local():
    from app.models import WorkoutLog
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    async with LocalSession() as session:
        await session.execute(delete(WorkoutLog).where(WorkoutLog.event_date < cutoff))
        await session.commit()
