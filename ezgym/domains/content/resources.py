"""content 域 HTTP 资源注册入口（flask-restful）。

resource 只做 解析→鉴权→调 service→ok；错误由 service raise、全局 handler 兜底。
修 CR #7：一律 `return ok(data, status)`，绝不把 Response 对象/model 直接丢给 jsonify。
"""
from flask import request
from flask_jwt_extended import get_jwt, verify_jwt_in_request
from flask_restful import Resource

from ezgym.core.response import ok
from ezgym.core.security import (
    Permission,
    current_user_id,
    has_permission,
    login_required,
)
from ezgym.domains.content.schemas import BlogCreateSchema, BlogListQuerySchema
from ezgym.domains.content.service import ContentService

__all__ = ["register"]


def _page_body(page):
    return {"items": page.items, "next_cursor": page.next_cursor, "count": page.count}


def _is_admin() -> bool:
    """从 JWT claims 读取 permission 判定 ADMIN（无需再查库）。"""
    claims = get_jwt()
    return has_permission(claims.get("permission", 0), Permission.ADMIN)


class BlogListResource(Resource):
    """/api/blogs —— GET 软登录列表；POST login 新建。"""

    def get(self):
        verify_jwt_in_request(optional=True)
        viewer_id = current_user_id()
        args = BlogListQuerySchema().load(request.args)
        page = ContentService.list_blogs(
            scope=args["scope"],
            user_id=args.get("user_id"),
            viewer_id=viewer_id,
            cursor=args.get("cursor"),
            limit=args.get("limit"),
        )
        return ok(_page_body(page))

    @login_required
    def post(self):
        data = BlogCreateSchema().load(request.get_json(silent=True) or {})
        user_id = current_user_id()
        blog = ContentService.create_blog(
            user_id=user_id,
            title=data.get("title"),
            content=data["content"],
            picture=data.get("picture"),
        )
        return ok(ContentService.get_blog_detail(blog.id, user_id), 201)


class BlogResource(Resource):
    """/api/blogs/<id> —— GET 公开单帖；DELETE login（作者或 ADMIN）。"""

    def get(self, blog_id):
        verify_jwt_in_request(optional=True)
        viewer_id = current_user_id()
        return ok(ContentService.get_blog_detail(blog_id, viewer_id))

    @login_required
    def delete(self, blog_id):
        user_id = current_user_id()
        ContentService.delete_blog(blog_id, user_id, is_admin=_is_admin())
        return ok({"id": blog_id, "deleted": True})


class BlogLikeResource(Resource):
    """/api/blogs/<id>/likes —— POST 点赞；DELETE 取消赞。"""

    @login_required
    def post(self, blog_id):
        user_id = current_user_id()
        return ok(ContentService.like_blog(blog_id, user_id), 201)

    @login_required
    def delete(self, blog_id):
        user_id = current_user_id()
        return ok(ContentService.unlike_blog(blog_id, user_id))


def register(api):
    """向 flask-restful Api 注册本域 Resource。"""
    api.add_resource(BlogListResource, "/api/blogs")
    api.add_resource(BlogResource, "/api/blogs/<int:blog_id>")
    api.add_resource(BlogLikeResource, "/api/blogs/<int:blog_id>/likes")
