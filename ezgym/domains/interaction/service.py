"""interaction 域 service（评论 comment + 回复 reply，业务逻辑 + 事务边界）。

CommentService / ReplyService 继承 BaseService，查询走 base_query 过滤软删，写操作
方法内 commit（一个方法 = 一个事务）。

关键点：
- 建评论前经 content_service.blog_exists 校验帖子存在（惰性 import 避免模块级循环）。
- 删评论级联软删其 reply，与评论软删在同一事务内完成。
- 展示昵称经 identity.service.get_users_public 批量取，避免 N+1，模型无冗余 nick_name。
- XSS：正文用 markupsafe.escape 统一转义（bleach 未在依赖中，见回复说明）。
"""
from markupsafe import escape

from ezgym.core.database import db
from ezgym.core.errors import Forbidden, NotFound
from ezgym.core.pagination import Page, cursor_paginate
from ezgym.core.service import BaseService
from ezgym.domains.identity import service as identity_service
from ezgym.domains.interaction.models import Comment, Reply

__all__ = [
    "CommentService",
    "ReplyService",
    "count_comments_by_blog",
    "count_comments_by_blogs",
    "count_comments_by_user",
    "list_comments_by_user",
]


def _sanitize(text: str | None) -> str | None:
    """统一 XSS 清洗：HTML 转义（markupsafe.escape）。None 原样返回。"""
    if text is None:
        return None
    return str(escape(text))


class CommentService(BaseService):
    """评论：多对一 blog。"""

    model = Comment

    # ---------- 写入 ----------
    @classmethod
    def create_comment(cls, user_id: int, blog_id: int, content: str):
        """新建评论。先校验帖子存在（否则 NotFound）；正文转义。"""
        # 惰性 import 避免 content <-> interaction 模块级循环
        from ezgym.domains.content import service as content_service
        if not content_service.blog_exists(blog_id):
            raise NotFound("动态不存在")
        return cls.create(
            user_id=user_id, blog_id=blog_id, content=_sanitize(content))

    @classmethod
    def delete_comment(cls, comment_id: int, user_id: int,
                       is_admin: bool = False) -> None:
        """软删评论 + 级联软删其 reply（同一事务）。仅作者或 ADMIN。"""
        comment = cls.get_or_404(comment_id, "评论不存在")
        if comment.user_id != user_id and not is_admin:
            raise Forbidden("只能删除本人的评论")
        comment.is_deleted = True
        # 级联软删未删除的 reply
        Reply.query.filter(
            Reply.comment_id == comment_id,
            Reply.is_deleted.is_(False),
        ).update({Reply.is_deleted: True}, synchronize_session=False)
        db.session.commit()

    # ---------- 列表（带内嵌 reply + 作者信息）----------
    @classmethod
    def list_for_blog(cls, blog_id: int) -> list[dict]:
        """该帖评论列表，每条内嵌其 reply 列表；评论与回复均带作者公开信息。"""
        comments = (
            cls.base_query()
            .filter(cls.model.blog_id == blog_id)
            .order_by(cls.model.id.asc())
            .all()
        )
        if not comments:
            return []
        comment_ids = [c.id for c in comments]
        replies = (
            Reply.query.filter(
                Reply.comment_id.in_(comment_ids),
                Reply.is_deleted.is_(False),
            )
            .order_by(Reply.id.asc())
            .all()
        )
        # 批量取全部涉及作者公开信息，避免 N+1
        author_ids = [c.user_id for c in comments] + [r.user_id for r in replies]
        authors = identity_service.get_users_public(author_ids)

        replies_by_comment: dict[int, list] = {}
        for r in replies:
            replies_by_comment.setdefault(r.comment_id, []).append({
                "id": r.id,
                "comment_id": r.comment_id,
                "reply_id": r.reply_id,
                "user_id": r.user_id,
                "content": r.content,
                "author": authors.get(r.user_id),
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })

        items = []
        for c in comments:
            items.append({
                "id": c.id,
                "blog_id": c.blog_id,
                "user_id": c.user_id,
                "content": c.content,
                "author": authors.get(c.user_id),
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "replies": replies_by_comment.get(c.id, []),
            })
        return items

    # ---------- 供他域消费的计数/列表 ----------
    @classmethod
    def count_comments_by_blog(cls, blog_id: int) -> int:
        return cls.base_query().filter(cls.model.blog_id == blog_id).count()

    @classmethod
    def count_comments_by_blogs(cls, blog_ids: list[int]) -> dict[int, int]:
        """批量：{blog_id: comment_count}，供 content 列表避免 N+1。"""
        if not blog_ids:
            return {}
        rows = (
            db.session.query(cls.model.blog_id, db.func.count(cls.model.id))
            .filter(
                cls.model.blog_id.in_(list(set(blog_ids))),
                cls.model.is_deleted.is_(False),
            )
            .group_by(cls.model.blog_id)
            .all()
        )
        return {blog_id: cnt for blog_id, cnt in rows}

    @classmethod
    def count_comments_by_user(cls, user_id: int) -> int:
        return cls.base_query().filter(cls.model.user_id == user_id).count()

    @classmethod
    def list_comments_by_user(cls, user_id: int, cursor: int | None,
                              limit: int | None) -> Page:
        query = cls.base_query().filter(cls.model.user_id == user_id)
        page = cursor_paginate(query, cursor, limit, cls.model.id)
        page.items = [
            {
                "id": c.id,
                "blog_id": c.blog_id,
                "user_id": c.user_id,
                "content": c.content,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in page.items
        ]
        return page


class ReplyService(BaseService):
    """楼中楼回复：多对一 comment。"""

    model = Reply

    @classmethod
    def create_reply(cls, user_id: int, comment_id: int, content: str,
                     reply_id: int | None = None):
        """新建回复。校验 comment 存在；正文转义。"""
        if CommentService.get(comment_id) is None:
            raise NotFound("评论不存在")
        if reply_id is not None and cls.get(reply_id) is None:
            raise NotFound("被回复的内容不存在")
        return cls.create(
            user_id=user_id,
            comment_id=comment_id,
            reply_id=reply_id,
            content=_sanitize(content),
        )

    @classmethod
    def delete_reply(cls, reply_id: int, user_id: int) -> None:
        """软删回复：仅本人。"""
        reply = cls.get_or_404(reply_id, "回复不存在")
        if reply.user_id != user_id:
            raise Forbidden("只能删除本人的回复")
        cls.soft_delete(reply)


# ============================================================
# 跨域 service 函数（供 content 列表 / profile 聚合消费）
# ============================================================

def count_comments_by_blog(blog_id: int) -> int:
    return CommentService.count_comments_by_blog(blog_id)


def count_comments_by_blogs(blog_ids: list[int]) -> dict[int, int]:
    return CommentService.count_comments_by_blogs(blog_ids)


def count_comments_by_user(user_id: int) -> int:
    return CommentService.count_comments_by_user(user_id)


def list_comments_by_user(user_id: int, cursor: int | None, limit: int | None) -> Page:
    return CommentService.list_comments_by_user(user_id, cursor, limit)
