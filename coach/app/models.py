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
    currency: Mapped[str] = mapped_column(String(8), default="$")
    savings_target: Mapped[float] = mapped_column(default=0.0)
    health_metrics: Mapped[str] = mapped_column(String(256), default="")
    unit_weight: Mapped[str] = mapped_column(String(4), default="kg")
    steps_entity: Mapped[str] = mapped_column(String(128), nullable=True)
    notify_service: Mapped[str] = mapped_column(String(128), nullable=True)
    notify_target: Mapped[str] = mapped_column(String(128), nullable=True)
    notification_lead_minutes: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class UserCategorySchedule(Base):
    __tablename__ = "user_category_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    schedule_type: Mapped[str] = mapped_column(String(8), nullable=False, default="skip")
    days: Mapped[str] = mapped_column(String(32), nullable=True)
    start_time: Mapped[str] = mapped_column(String(5), nullable=True)
    end_time: Mapped[str] = mapped_column(String(5), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


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


class HealthEntry(Base):
    __tablename__ = "health_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    metric: Mapped[str] = mapped_column(String(32), nullable=False)
    value: Mapped[float] = mapped_column(nullable=True)
    value2: Mapped[float] = mapped_column(nullable=True)
    log_date: Mapped[str] = mapped_column(String(10), nullable=False)
    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    doctor: Mapped[str] = mapped_column(String(128), nullable=True)
    location: Mapped[str] = mapped_column(String(128), nullable=True)
    appt_date: Mapped[str] = mapped_column(String(10), nullable=False)
    appt_time: Mapped[str] = mapped_column(String(5), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class CheckIn(Base):
    __tablename__ = "checkins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    mood: Mapped[int] = mapped_column(Integer, nullable=False)
    energy: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    log_date: Mapped[str] = mapped_column(String(10), nullable=False)
    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class FinanceLine(Base):
    __tablename__ = "finance_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    line_type: Mapped[str] = mapped_column(String(8), nullable=False)  # "income" | "expense"
    amount: Mapped[float] = mapped_column(default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class LearningItem(Base):
    __tablename__ = "learning_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    item_type: Mapped[str] = mapped_column(String(16), nullable=False)  # "course"|"book"|"skill"
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    meta: Mapped[str] = mapped_column(String(256), nullable=True)       # platform / author
    progress: Mapped[int] = mapped_column(Integer, nullable=True)       # 0-100 for courses
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    current_level: Mapped[str] = mapped_column(String(64), nullable=True)
    target_level: Mapped[str] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Person(Base):
    __tablename__ = "people"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    relationship: Mapped[str] = mapped_column(String(64), nullable=True)
    last_contact: Mapped[str] = mapped_column(String(10), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


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


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    metric: Mapped[str] = mapped_column(String(64), nullable=True)       # links to category metric for auto-progress
    target_value: Mapped[float] = mapped_column(nullable=True)
    target_unit: Mapped[str] = mapped_column(String(32), nullable=True)
    start_value: Mapped[float] = mapped_column(nullable=True)
    total_steps: Mapped[int] = mapped_column(Integer, nullable=True)     # for step-based goals
    start_date: Mapped[str] = mapped_column(String(10), nullable=True)
    deadline: Mapped[str] = mapped_column(String(10), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    achieved_at: Mapped[str] = mapped_column(String(10), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class GoalProgress(Base):
    __tablename__ = "goal_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    goal_id: Mapped[int] = mapped_column(Integer, ForeignKey("goals.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    steps_added: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    note: Mapped[str] = mapped_column(String(256), nullable=True)
    logged_at: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


# ── Daily Standup ─────────────────────────────────────────────
class StandupEntry(Base):
    __tablename__ = "standup_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    log_date: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD
    done_items: Mapped[str] = mapped_column(Text, nullable=True)
    new_items: Mapped[str] = mapped_column(Text, nullable=True)
    blockers: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


# ── Calendar Config ───────────────────────────────────────────
class CalendarConfig(Base):
    __tablename__ = "calendar_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(256), nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=True)
    default_category: Mapped[str] = mapped_column(String(64), nullable=True)
    ignore_keywords: Mapped[str] = mapped_column(Text, nullable=True)  # comma-separated
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


# ── Business Pipeline ──────────────────────────────────────────
PIPELINE_STAGES = ["marketing", "offer", "design", "install", "paid"]
PIPELINE_STAGE_LABELS = {
    "marketing": "Marketing",
    "offer":     "Price Offer",
    "design":    "Design",
    "install":   "Install",
    "paid":      "Cash In",
}


class PipelineJob(Base):
    __tablename__ = "pipeline_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    client: Mapped[str] = mapped_column(String(128), nullable=True)
    location: Mapped[str] = mapped_column(String(256), nullable=True)
    stage: Mapped[str] = mapped_column(String(32), nullable=False, default="marketing")
    value: Mapped[float] = mapped_column(nullable=True)
    due_date: Mapped[str] = mapped_column(String(10), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class PipelineNote(Base):
    __tablename__ = "pipeline_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("pipeline_jobs.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
