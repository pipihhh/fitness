"""challenge 域模型：Challenge。"""
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ezgym.core.database import PkMixin, SoftDeleteMixin, TimestampMixin, db

__all__ = ["Challenge"]


class Challenge(PkMixin, TimestampMixin, SoftDeleteMixin, db.Model):
    """健身挑战。number 业务唯一号。pageviews 浏览量（由 service 原子自增）。"""

    __tablename__ = "challenge"

    picture: Mapped[str | None] = mapped_column(String(255))
    content: Mapped[str | None] = mapped_column(Text)
    start_time: Mapped[datetime | None] = mapped_column(DateTime)
    end_time: Mapped[datetime | None] = mapped_column(DateTime)
    pageviews: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
