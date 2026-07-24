"""interaction 域 HTTP 资源注册入口（flask-restful）。

resource 只做 解析→鉴权→调 service→ok（修 CR #7：一律返回 ok(data, status)）。
"""
from flask import request
from flask_jwt_extended import get_jwt
from flask_restful import Resource

from ezgym.core.response import ok
from ezgym.core.security import (
    Permission,
    current_user_id,
    has_permission,
    login_required,
)
from ezgym.domains.interaction.schemas import (
    CommentCreateSchema,
    ReplyCreateSchema,
)
from ezgym.domains.interaction.service import CommentService, ReplyService

__all__ = ["register"]


def _is_admin() -> bool:
    claims = get_jwt()
    return has_permission(claims.get("permission", 0), Permission.ADMIN)


class BlogCommentListResource(Resource):
    """/api/blogs/<id>/comments —— GET 公开，返回评论（内嵌 reply）列表。"""

    def get(self, blog_id):
        return ok({"items": CommentService.list_for_blog(blog_id)})


class CommentListResource(Resource):
    """/api/comments —— POST login 新建评论。"""

    @login_required
    def post(self):
        data = CommentCreateSchema().load(request.get_json(silent=True) or {})
        user_id = current_user_id()
        comment = CommentService.create_comment(
            user_id=user_id, blog_id=data["blog_id"], content=data["content"])
        return ok(
            {"id": comment.id, "blog_id": comment.blog_id,
             "user_id": comment.user_id, "content": comment.content},
            201,
        )


class CommentResource(Resource):
    """/api/comments/<id> —— DELETE login（作者或 ADMIN），级联软删 reply。"""

    @login_required
    def delete(self, comment_id):
        user_id = current_user_id()
        CommentService.delete_comment(comment_id, user_id, is_admin=_is_admin())
        return ok({"id": comment_id, "deleted": True})


class ReplyListResource(Resource):
    """/api/replies —— POST login 新建回复。"""

    @login_required
    def post(self):
        data = ReplyCreateSchema().load(request.get_json(silent=True) or {})
        user_id = current_user_id()
        reply = ReplyService.create_reply(
            user_id=user_id,
            comment_id=data["comment_id"],
            content=data["content"],
            reply_id=data.get("reply_id"),
        )
        return ok(
            {"id": reply.id, "comment_id": reply.comment_id,
             "reply_id": reply.reply_id, "user_id": reply.user_id,
             "content": reply.content},
            201,
        )


class ReplyResource(Resource):
    """/api/replies/<id> —— DELETE login，仅本人。"""

    @login_required
    def delete(self, reply_id):
        user_id = current_user_id()
        ReplyService.delete_reply(reply_id, user_id)
        return ok({"id": reply_id, "deleted": True})


def register(api):
    """向 flask-restful Api 注册本域 Resource。"""
    api.add_resource(BlogCommentListResource, "/api/blogs/<int:blog_id>/comments")
    api.add_resource(CommentListResource, "/api/comments")
    api.add_resource(CommentResource, "/api/comments/<int:comment_id>")
    api.add_resource(ReplyListResource, "/api/replies")
    api.add_resource(ReplyResource, "/api/replies/<int:reply_id>")
