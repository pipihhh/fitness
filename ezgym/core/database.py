"""数据库对象与通用 Mixin。

- 暴露 extensions.db 作为 core.database.db，各域模型统一从这里 import。
- 提供 SQLAlchemy 2.0 风格（Mapped/mapped_column）的三个 Mixin。
- 全部使用 DB 无关类型（Integer/String/DateTime/Boolean），保证 SQLite（测试）
  与 MySQL（生产）都能 create_all。
"""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, func
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from ezgym.extensions import db

__all__ = ["db", "PkMixin", "TimestampMixin", "SoftDeleteMixin"]


class PkMixin:
    """自增整型主键。"""

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)


class TimestampMixin:
    """创建/更新时间戳，插入与更新时由 DB 侧自动填充。"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class SoftDeleteMixin:
    """软删标志，默认未删除。查询过滤统一走 BaseService。"""

    @declared_attr
    def is_deleted(cls) -> Mapped[bool]:  # noqa: N805
        return mapped_column(Boolean, nullable=False, default=False, server_default="0")
