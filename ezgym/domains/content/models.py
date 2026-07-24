"""content 域模型：Blog + Like（原 upper_log）。

like_count 为点赞计数冗余，由 service 在单事务内与 Like 明细一致维护（修 CR #12）。
"""
from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ezgym.core.database import PkMixin, SoftDeleteMixin, TimestampMixin, db

__all__ = ["Blog", "Like"]


class Blog(PkMixin, TimestampMixin, SoftDeleteMixin, db.Model):
    """动态帖子。like_count 冗余计数。"""

    __tablename__ = "blog"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id"), nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(255))
    content: Mapped[str | None] = mapped_column(Text)
    picture: Mapped[str | None] = mapped_column(String(255))
    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    likes: Mapped[list["Like"]] = relationship(
        back_populates="blog", cascade="all, delete-orphan"
    )


class Like(PkMixin, TimestampMixin, SoftDeleteMixin, db.Model):
    """点赞明细（原 upper_log）。(blog_id, user_id) 唯一，取消/恢复走软删。"""

    __tablename__ = "like"
    __table_args__ = (
        UniqueConstraint("blog_id", "user_id", name="uq_like_blog_user"),
    )

    blog_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("blog.id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id"), nullable=False
    )

    blog: Mapped["Blog"] = relationship(back_populates="likes")
