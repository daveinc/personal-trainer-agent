from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base, ExtBase


def _now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(128), nullable=True)
    onboarding_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    unit_distance: Mapped[str] = mapped_column(String(8), default="km")
    week_start: Mapped[str] = mapped_column(String(3), default="Mon")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Slot(Base):
    __tablename__ = "slots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    schedule_type: Mapped[str] = mapped_column(String(8), nullable=False, default="free")
    days: Mapped[str] = mapped_column(String(32), nullable=True)
    start_time: Mapped[str] = mapped_column(String(5), nullable=True)
    end_time: Mapped[str] = mapped_column(String(5), nullable=True)
    notify_before: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class SlotAttribute(Base):
    __tablename__ = "slot_attributes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slot_id: Mapped[int] = mapped_column(Integer, ForeignKey("slots.id"), nullable=False)
    attribute_name: Mapped[str] = mapped_column(String(64), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=True)


class Session(ExtBase):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slot_id: Mapped[int] = mapped_column(Integer, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class SessionValue(ExtBase):
    __tablename__ = "session_values"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(Integer, nullable=False)
    attribute_name: Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=True)


class NotificationLog(Base):
    __tablename__ = "notification_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slot_id: Mapped[int] = mapped_column(Integer, ForeignKey("slots.id"), nullable=False)
    notif_type: Mapped[str] = mapped_column(String(8), nullable=False)   # "pre" | "post"
    log_date: Mapped[str] = mapped_column(String(10), nullable=False)    # "YYYY-MM-DD"
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    action_taken: Mapped[str] = mapped_column(String(16), nullable=True)


class WorkoutLog(Base):
    __tablename__ = "workout_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    calendar_uid: Mapped[str] = mapped_column(String(255), nullable=True)
    event_date: Mapped[str] = mapped_column(String(10), nullable=False)
    event_title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class ScoringRule(Base):
    __tablename__ = "scoring_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    formula: Mapped[str] = mapped_column(Text, nullable=False,
        default="round(completed / total * 100, 1) if total > 0 else 0")
    formula_enabled: Mapped[bool] = mapped_column(default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class TrendPeriod(Base):
    __tablename__ = "trend_periods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    start_month: Mapped[int] = mapped_column(Integer, nullable=False)
    end_month: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class RoutineState(Base):
    __tablename__ = "routine_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    enabled: Mapped[bool] = mapped_column(default=False)
    status: Mapped[str] = mapped_column(String(16), default="idle")
    last_run: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)


class TrendObservation(Base):
    __tablename__ = "trend_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    period_name: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    score: Mapped[str] = mapped_column(String(64), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
