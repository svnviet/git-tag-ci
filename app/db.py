from datetime import datetime, timezone

from sqlalchemy import DateTime, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from . import config

engine = create_engine(
    config.DB_URL,
    pool_pre_ping=True,
    connect_args=(
        {"check_same_thread": False} if config.DB_URL.startswith("sqlite") else {}
    ),
)
SessionLocal = sessionmaker(engine, expire_on_commit=False)


def now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Tag(Base):
    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(String(255), primary_key=True)
    commit: Mapped[str] = mapped_column(String(64), default="")
    # pending | building | success | failed | skipped | ignored (prefix mismatch) | invalid (unsafe param)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    params: Mapped[str] = mapped_column(String(512), default="")  # JSON list
    prev_tag: Mapped[str | None] = mapped_column(String(255), default=None)
    output_dir: Mapped[str | None] = mapped_column(String(512), default=None)
    notes_path: Mapped[str | None] = mapped_column(String(512), default=None)
    exit_code: Mapped[int | None] = mapped_column(default=None)
    log_path: Mapped[str | None] = mapped_column(String(512), default=None)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )


def init_db() -> None:
    """Bring the schema up to date by running the Alembic migrations."""
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(config.ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(config.ROOT / "alembic"))
    command.upgrade(cfg, "head")
