"""identity 域模型：User + UserInfo（一对一）。"""
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ezgym.core.database import PkMixin, SoftDeleteMixin, TimestampMixin, db
from ezgym.core.security import Permission

__all__ = ["User", "UserInfo"]


class User(PkMixin, TimestampMixin, SoftDeleteMixin, db.Model):
    """账号主表。密码存 bcrypt 哈希；permission 位掩码；number 业务唯一号。"""

    __tablename__ = "user"

    account: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    permission: Mapped[int] = mapped_column(
        Integer, nullable=False, default=int(Permission.NORMAL)
    )
    number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)

    info: Mapped["UserInfo"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class UserInfo(PkMixin, TimestampMixin, SoftDeleteMixin, db.Model):
    """用户资料，user_id 唯一，一对一 User。"""

    __tablename__ = "user_info"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id"), unique=True, nullable=False
    )
    phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(128))
    gender: Mapped[int | None] = mapped_column(Integer)
    avatar: Mapped[str | None] = mapped_column(String(255))
    age: Mapped[int | None] = mapped_column(Integer)
    nick_name: Mapped[str | None] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(Text)

    user: Mapped["User"] = relationship(back_populates="info")
