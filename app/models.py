from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

class Child(Base):
    __tablename__ = "children"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)

    sessions: Mapped[list["Session"]] = relationship(back_populates="child", cascade="all, delete-orphan")

class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("children.id"), nullable=False)

    mode: Mapped[str] = mapped_column(String(32), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(16), default="normal", nullable=False)
    theme_id: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    exposure_ms: Mapped[int] = mapped_column(Integer, default=1200, nullable=False)
    items_total: Mapped[int] = mapped_column(Integer, default=7, nullable=False)

    child: Mapped["Child"] = relationship(back_populates="sessions")
    attempts: Mapped[list["Attempt"]] = relationship(back_populates="session", cascade="all, delete-orphan")

class Attempt(Base):
    __tablename__ = "attempts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), nullable=False)

    item_id: Mapped[str] = mapped_column(String(64), nullable=False)  # идентификатор задания
    correct: Mapped[int] = mapped_column(Integer, nullable=False)     # 0/1
    reaction_ms: Mapped[int] = mapped_column(Integer, nullable=False) # время ответа
    shown_ms: Mapped[int] = mapped_column(Integer, nullable=False)    # сколько показывали стимул

    session: Mapped["Session"] = relationship(back_populates="attempts")