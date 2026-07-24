"""BaseService：通用 CRUD 与软删过滤 helper。

一个业务动作 = 一个事务。子类通过 `model` 类属性绑定实体，复用这里的
增删改查与软删过滤；跨域取数必须调对方域的 service，禁止直连他域 model。
"""
from typing import Generic, TypeVar

from ezgym.core.database import db
from ezgym.core.errors import NotFound

T = TypeVar("T")

__all__ = ["BaseService"]


class BaseService(Generic[T]):
    """通用服务基类。

    约定：所有写操作在方法内自行 commit（一个方法 = 一个事务边界）；
    调用方无需再管理事务。异常时回滚由调用处或全局 handler 兜底，
    这里的 commit 前不吞异常。
    """

    model: type = None  # 子类必须覆盖

    # ---------- 查询 ----------
    @classmethod
    def base_query(cls, include_deleted: bool = False):
        """返回已过滤软删的基础 query。"""
        q = cls.model.query
        if not include_deleted and hasattr(cls.model, "is_deleted"):
            q = q.filter(cls.model.is_deleted.is_(False))
        return q

    @classmethod
    def get(cls, obj_id: int, include_deleted: bool = False):
        """按 id 取，未命中返回 None。"""
        return cls.base_query(include_deleted=include_deleted).filter(
            cls.model.id == obj_id
        ).first()

    @classmethod
    def get_or_404(cls, obj_id: int, message: str = "资源不存在"):
        obj = cls.get(obj_id)
        if obj is None:
            raise NotFound(message)
        return obj

    # ---------- 写入 ----------
    @classmethod
    def create(cls, **kwargs) -> T:
        obj = cls.model(**kwargs)
        db.session.add(obj)
        db.session.commit()
        return obj

    @classmethod
    def update(cls, obj, **kwargs) -> T:
        for key, value in kwargs.items():
            setattr(obj, key, value)
        db.session.commit()
        return obj

    @classmethod
    def soft_delete(cls, obj) -> None:
        """软删：置 is_deleted=True。"""
        obj.is_deleted = True
        db.session.commit()

    @classmethod
    def hard_delete(cls, obj) -> None:
        db.session.delete(obj)
        db.session.commit()
