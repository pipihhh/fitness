"""social 域模型：Follow。补软删 + (from,to) 唯一约束防重复关注（CR）。"""
from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ezgym.core.database import PkMixin, SoftDeleteMixin, TimestampMixin, db

__all__ = ["Follow"]


class Follow(PkMixin, TimestampMixin, SoftDeleteMixin, db.Model):
    """关注关系：from_user 关注 to_user。(from, to) 唯一。"""

    __tablename__ = "follow"
    __table_args__ = (
        UniqueConstraint("from_user_id", "to_user_id", name="uq_follow_from_to"),
    )

    from_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id"), nullable=False
    )
    to_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id"), nullable=False
    )
