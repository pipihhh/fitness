"""interaction 域模型：Comment + Reply。

去掉冗余 nick_name（原表冗余存储导致改昵称需级联更新，CR #14）：
昵称改由 service 层 JOIN user_info 实时取。
"""
from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ezgym.core.database import PkMixin, SoftDeleteMixin, TimestampMixin, db

__all__ = ["Comment", "Reply"]


class Comment(PkMixin, TimestampMixin, SoftDeleteMixin, db.Model):
    """评论，多对一 blog。"""

    __tablename__ = "comment"

    blog_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("blog.id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id"), nullable=False
    )
    content: Mapped[str | None] = mapped_column(Text)

    replies: Mapped[list["Reply"]] = relationship(
        back_populates="comment", cascade="all, delete-orphan"
    )


class Reply(PkMixin, TimestampMixin, SoftDeleteMixin, db.Model):
    """楼中楼回复，多对一 comment。reply_id 可空：为空=直接回评论，否则回某条 reply。"""

    __tablename__ = "reply"

    comment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("comment.id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id"), nullable=False
    )
    reply_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("reply.id"))
    content: Mapped[str | None] = mapped_column(Text)

    comment: Mapped["Comment"] = relationship(back_populates="replies")
