"""social 域 service（关注关系，业务逻辑 + 事务边界）。

SocialService 继承 BaseService，查询走 base_query 过滤软删，写操作方法内 commit。
关注写入采用「唯一索引 + 应用层前置检查 + 捕获唯一键冲突兜底并发」的幂等模式
（Follow 模型已建 uq_follow_from_to 唯一约束）。

跨域取展示信息只调 identity.service 暴露的函数，禁止直连 identity 的 model。
对外（供 content following scope / profile 聚合）暴露的跨域函数见文件末尾。
"""
from sqlalchemy.exc import IntegrityError

from ezgym.core.database import db
from ezgym.core.errors import BadRequest, NotFound
from ezgym.core.pagination import Page, cursor_paginate
from ezgym.core.service import BaseService
from ezgym.domains.identity import service as identity_service
from ezgym.domains.social.models import Follow

__all__ = [
    "SocialService",
    "list_following_ids",
    "count_fans",
    "count_following",
    "is_following",
    "list_followers",
    "list_following",
]


class SocialService(BaseService):
    """关注关系：from_user 关注 to_user。(from, to) 唯一，软删 + 恢复。"""

    model = Follow

    # ---------- 写入 ----------
    @classmethod
    def follow(cls, from_id: int, to_id: int):
        """建立关注。

        :return: (follow, created) —— created 为 True 表示本次新建/恢复，
            False 表示此前已在关注（幂等）。
        - 关注自己 -> BadRequest
        - 对方不存在 -> NotFound（经 identity_service.user_exists）
        - 曾软删则恢复；已在关注则幂等返回原记录
        """
        if from_id == to_id:
            raise BadRequest("不能关注自己")
        if not identity_service.user_exists(to_id):
            raise NotFound("关注的用户不存在")

        existing = cls._find(from_id, to_id, include_deleted=True)
        if existing is not None:
            if existing.is_deleted:
                existing.is_deleted = False
                db.session.commit()
                return existing, True
            return existing, False

        follow = Follow(from_user_id=from_id, to_user_id=to_id)
        db.session.add(follow)
        try:
            db.session.commit()
        except IntegrityError:
            # 并发下唯一键冲突：回滚后重新查一次返回（幂等兜底）
            db.session.rollback()
            existing = cls._find(from_id, to_id, include_deleted=True)
            if existing is None:
                raise
            if existing.is_deleted:
                existing.is_deleted = False
                db.session.commit()
                return existing, True
            return existing, False
        return follow, True

    @classmethod
    def unfollow(cls, from_id: int, to_id: int):
        """取消关注：软删已存在的关注记录。

        未关注时按幂等成功处理（返回 None），不抛 404——DELETE 语义追求
        「结束态一致」，无论此前是否关注，调用后都保证不再关注。
        """
        existing = cls._find(from_id, to_id, include_deleted=False)
        if existing is None:
            return None
        cls.soft_delete(existing)
        return existing

    # ---------- 查询 helper ----------
    @classmethod
    def _find(cls, from_id: int, to_id: int, include_deleted: bool = False):
        return cls.base_query(include_deleted=include_deleted).filter(
            cls.model.from_user_id == from_id,
            cls.model.to_user_id == to_id,
        ).first()

    @classmethod
    def is_following(cls, from_id: int, to_id: int) -> bool:
        return cls._find(from_id, to_id) is not None

    @classmethod
    def list_following_ids(cls, user_id: int) -> list[int]:
        """user_id 关注的所有 to_user_id（未软删）。"""
        rows = cls.base_query().filter(cls.model.from_user_id == user_id).all()
        return [r.to_user_id for r in rows]

    @classmethod
    def count_fans(cls, user_id: int) -> int:
        """粉丝数：关注 user_id 的人数。"""
        return cls.base_query().filter(cls.model.to_user_id == user_id).count()

    @classmethod
    def count_following(cls, user_id: int) -> int:
        """关注数：user_id 关注的人数。"""
        return cls.base_query().filter(cls.model.from_user_id == user_id).count()

    # ---------- 列表（游标分页，带对方公开信息）----------
    @classmethod
    def _paginate_with_public(cls, query, cursor, limit, other_col) -> Page:
        """通用：分页取 Follow 行，批量补对方公开信息，避免 N+1。

        :param other_col: 取「对方 user_id」的列（粉丝取 from_user_id，关注取 to_user_id）
        """
        page = cursor_paginate(query, cursor, limit, cls.model.id)
        rows = page.items
        other_ids = [getattr(r, other_col.key) for r in rows]
        public = identity_service.get_users_public(other_ids)
        items = []
        for r in rows:
            other_id = getattr(r, other_col.key)
            items.append({
                "follow_id": r.id,
                "user_id": other_id,
                "user": public.get(other_id),
            })
        return Page(items=items, count=page.count, next_cursor=page.next_cursor)

    @classmethod
    def list_followers(cls, user_id: int, cursor: int | None,
                       limit: int | None) -> Page:
        """user_id 的粉丝列表：关注了 user_id 的人（对方 = from_user_id）。"""
        query = cls.base_query().filter(cls.model.to_user_id == user_id)
        return cls._paginate_with_public(query, cursor, limit, cls.model.from_user_id)

    @classmethod
    def list_following(cls, user_id: int, cursor: int | None,
                       limit: int | None) -> Page:
        """user_id 的关注列表：user_id 关注的人（对方 = to_user_id）。"""
        query = cls.base_query().filter(cls.model.from_user_id == user_id)
        return cls._paginate_with_public(query, cursor, limit, cls.model.to_user_id)


# ============================================================
# 跨域 service 函数（供 content following scope / profile 聚合消费）
# ============================================================

def list_following_ids(user_id: int) -> list[int]:
    return SocialService.list_following_ids(user_id)


def count_fans(user_id: int) -> int:
    return SocialService.count_fans(user_id)


def count_following(user_id: int) -> int:
    return SocialService.count_following(user_id)


def is_following(from_id: int, to_id: int) -> bool:
    return SocialService.is_following(from_id, to_id)


def list_followers(user_id: int, cursor: int | None, limit: int | None) -> Page:
    return SocialService.list_followers(user_id, cursor, limit)


def list_following(user_id: int, cursor: int | None, limit: int | None) -> Page:
    return SocialService.list_following(user_id, cursor, limit)
