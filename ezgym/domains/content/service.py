"""content 域 service（动态 blog + 点赞 like，业务逻辑 + 事务边界）。

ContentService 继承 BaseService，查询走 base_query 过滤软删，写操作方法内 commit
（一个方法 = 一个事务）。跨域取展示信息只调他域 service 暴露的函数，禁止直连他域 model。

关键 CR 修复：
- #12：点赞 like_count 的自增/自减与 Like 明细写入在同一事务内完成，保持一致。
- #17：列表分页参数在 resource/schema 层转 int，service 内逻辑正确、类型安全。
- #18：following scope 用 ORM `Blog.user_id.in_(ids)` 表达式，无 AND/OR 优先级坑。
- #2：search_blogs 用 ORM `Blog.content.like(...)` 参数化绑定，杜绝 SQL 注入。
- XSS：正文用 markupsafe.escape 统一转义（bleach 未在依赖中，见回复说明）。
"""
from markupsafe import escape

from ezgym.core.database import db
from ezgym.core.errors import BadRequest, Forbidden, NotFound
from ezgym.core.pagination import Page, cursor_paginate
from ezgym.core.service import BaseService
from ezgym.domains.content.models import Blog, Like
from ezgym.domains.content.schemas import BlogSchema
from ezgym.domains.identity import service as identity_service

__all__ = [
    "ContentService",
    "get_blog",
    "blog_exists",
    "count_blogs_by_user",
    "list_blogs_by_user",
    "list_blogs_liked_by_user",
    "search_blogs",
]

_blog_schema = BlogSchema()


def _sanitize(text: str | None) -> str | None:
    """统一 XSS 清洗：HTML 转义（markupsafe.escape）。None 原样返回。"""
    if text is None:
        return None
    return str(escape(text))


class ContentService(BaseService):
    """动态帖子 + 点赞。like_count 冗余计数由本类在单事务内维护。"""

    model = Blog

    # ---------- 序列化辅助 ----------
    @classmethod
    def _serialize(cls, blog, author=None, comment_count=0, is_liked=None) -> dict:
        data = _blog_schema.dump(blog)
        data["author"] = author
        data["comment_count"] = comment_count
        data["like_count"] = blog.like_count
        if is_liked is not None:
            data["is_liked"] = is_liked
        return data

    # ---------- 列表 ----------
    @classmethod
    def list_blogs(cls, scope: str, user_id: int | None, viewer_id: int | None,
                   cursor: int | None, limit: int | None) -> Page:
        """游标分页动态列表。

        scope:
        - latest（默认）：全部动态
        - following：viewer 关注的人的动态（调 social_service.list_following_ids）
        - user：指定 user_id 的动态（缺 user_id -> BadRequest）
        """
        query = cls.base_query()
        if scope == "user":
            if not user_id:
                raise BadRequest("user scope 需要 user_id")
            query = query.filter(cls.model.user_id == user_id)
        elif scope == "following":
            if not viewer_id:
                # 未登录/无关注：following 列表为空
                return Page(items=[], count=0, next_cursor=None)
            from ezgym.domains.social import service as social_service
            following_ids = social_service.list_following_ids(viewer_id)
            if not following_ids:
                return Page(items=[], count=0, next_cursor=None)
            # 修 CR #18：用 ORM in_ 表达式，无 AND/OR 优先级坑
            query = query.filter(cls.model.user_id.in_(following_ids))

        page = cursor_paginate(query, cursor, limit, cls.model.id)
        page.items = cls._enrich(page.items, viewer_id)
        return page

    @classmethod
    def _enrich(cls, blogs: list, viewer_id: int | None) -> list[dict]:
        """批量补作者信息 / comment_count / is_liked，避免 N+1。"""
        if not blogs:
            return []
        blog_ids = [b.id for b in blogs]
        author_ids = [b.user_id for b in blogs]
        authors = identity_service.get_users_public(author_ids)

        # 惰性 import 避免模块级循环依赖
        from ezgym.domains.interaction import service as interaction_service
        comment_counts = interaction_service.count_comments_by_blogs(blog_ids)

        liked_ids: set[int] = set()
        if viewer_id:
            rows = (
                Like.query.filter(
                    Like.blog_id.in_(blog_ids),
                    Like.user_id == viewer_id,
                    Like.is_deleted.is_(False),
                ).all()
            )
            liked_ids = {r.blog_id for r in rows}

        items = []
        for b in blogs:
            items.append(cls._serialize(
                b,
                author=authors.get(b.user_id),
                comment_count=comment_counts.get(b.id, 0),
                is_liked=(b.id in liked_ids) if viewer_id else None,
            ))
        return items

    # ---------- 单帖 ----------
    @classmethod
    def get_blog_detail(cls, blog_id: int, viewer_id: int | None = None) -> dict:
        blog = cls.get_or_404(blog_id, "动态不存在")
        author = identity_service.get_user_public(blog.user_id)
        from ezgym.domains.interaction import service as interaction_service
        comment_count = interaction_service.count_comments_by_blog(blog_id)
        is_liked = None
        if viewer_id:
            is_liked = (
                Like.query.filter_by(
                    blog_id=blog_id, user_id=viewer_id, is_deleted=False
                ).first() is not None
            )
        return cls._serialize(blog, author=author,
                              comment_count=comment_count, is_liked=is_liked)

    # ---------- 写入 ----------
    @classmethod
    def create_blog(cls, user_id: int, title: str | None,
                    content: str, picture: str | None = None):
        """新建动态；正文用 markupsafe.escape 清洗 XSS。"""
        return cls.create(
            user_id=user_id,
            title=_sanitize(title),
            content=_sanitize(content),
            picture=picture,
        )

    @classmethod
    def delete_blog(cls, blog_id: int, user_id: int, is_admin: bool = False) -> None:
        """软删动态：仅作者或 ADMIN 可删。"""
        blog = cls.get_or_404(blog_id, "动态不存在")
        if blog.user_id != user_id and not is_admin:
            raise Forbidden("只能删除本人的动态")
        cls.soft_delete(blog)

    # ---------- 点赞（单事务保证 like_count 与 Like 明细一致，修 CR #12）----------
    @classmethod
    def like_blog(cls, blog_id: int, user_id: int) -> dict:
        """点赞。曾软删则恢复并 +1；从未点过则新建并 +1；已点赞则幂等不重复 +1。"""
        blog = cls.get_or_404(blog_id, "动态不存在")
        existing = (
            Like.query.filter_by(blog_id=blog_id, user_id=user_id).first()
        )
        if existing is not None:
            if existing.is_deleted:
                # 恢复：明细恢复 + 计数 +1，同一事务
                existing.is_deleted = False
                blog.like_count = blog.like_count + 1
                db.session.commit()
            # else: 已点赞，幂等，不重复 +1
            like = existing
        else:
            like = Like(blog_id=blog_id, user_id=user_id)
            db.session.add(like)
            blog.like_count = blog.like_count + 1
            db.session.commit()
        return {"blog_id": blog_id, "like_id": like.id,
                "like_count": blog.like_count, "is_liked": True}

    @classmethod
    def unlike_blog(cls, blog_id: int, user_id: int) -> dict:
        """取消赞：软删 Like 明细 + like_count-1（不小于 0），同一事务。"""
        blog = cls.get_or_404(blog_id, "动态不存在")
        existing = (
            Like.query.filter_by(
                blog_id=blog_id, user_id=user_id, is_deleted=False
            ).first()
        )
        if existing is not None:
            existing.is_deleted = True
            blog.like_count = max(0, blog.like_count - 1)
            db.session.commit()
        return {"blog_id": blog_id, "like_count": blog.like_count,
                "is_liked": False}

    # ---------- 供他域消费的查询 ----------
    @classmethod
    def count_blogs_by_user(cls, user_id: int) -> int:
        return cls.base_query().filter(cls.model.user_id == user_id).count()

    @classmethod
    def list_blogs_by_user(cls, user_id: int, cursor: int | None,
                           limit: int | None) -> Page:
        query = cls.base_query().filter(cls.model.user_id == user_id)
        page = cursor_paginate(query, cursor, limit, cls.model.id)
        page.items = cls._enrich(page.items, None)
        return page

    @classmethod
    def list_blogs_liked_by_user(cls, user_id: int, cursor: int | None,
                                 limit: int | None) -> Page:
        """user_id 点赞过（未取消）的动态列表，游标基于 Like.id。"""
        query = (
            db.session.query(Blog)
            .join(Like, Like.blog_id == Blog.id)
            .filter(
                Like.user_id == user_id,
                Like.is_deleted.is_(False),
                Blog.is_deleted.is_(False),
            )
        )
        page = cursor_paginate(query, cursor, limit, Blog.id)
        page.items = cls._enrich(page.items, user_id)
        return page

    @classmethod
    def search_blogs(cls, q: str, cursor: int | None, limit: int | None) -> Page:
        """按关键词搜索动态。修 CR #2：ORM `like` 参数化绑定，绝不字符串拼接。"""
        query = cls.base_query()
        if q:
            pattern = f"%{q}%"
            # SQLAlchemy 的 like() 生成绑定参数，q 作为值传入，不进入 SQL 文本
            query = query.filter(cls.model.content.like(pattern))
        page = cursor_paginate(query, cursor, limit, cls.model.id)
        page.items = cls._enrich(page.items, None)
        return page


# ============================================================
# 跨域 service 函数（供 interaction / search / profile 消费）
# ============================================================

def get_blog(blog_id: int) -> Blog | None:
    return ContentService.get(blog_id)


def blog_exists(blog_id: int) -> bool:
    return ContentService.get(blog_id) is not None


def count_blogs_by_user(user_id: int) -> int:
    return ContentService.count_blogs_by_user(user_id)


def list_blogs_by_user(user_id: int, cursor: int | None, limit: int | None) -> Page:
    return ContentService.list_blogs_by_user(user_id, cursor, limit)


def list_blogs_liked_by_user(user_id: int, cursor: int | None,
                             limit: int | None) -> Page:
    return ContentService.list_blogs_liked_by_user(user_id, cursor, limit)


def search_blogs(q: str, cursor: int | None, limit: int | None) -> Page:
    return ContentService.search_blogs(q, cursor, limit)
