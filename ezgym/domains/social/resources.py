"""social 域 HTTP 资源注册入口（flask-restful）。

resource 只做 解析→鉴权→调 service→ok；错误由 service raise、全局 handler 兜底。
"""
from flask import request
from flask_restful import Resource

from ezgym.core.response import ok
from ezgym.core.security import current_user_id, login_required
from ezgym.domains.social.schemas import FollowCreateSchema, FollowListQuerySchema
from ezgym.domains.social.service import SocialService

__all__ = ["register"]


def _page_body(page):
    return {"items": page.items, "next_cursor": page.next_cursor, "count": page.count}


class FollowListResource(Resource):
    """/api/follows —— POST 关注；GET 粉丝/关注列表。"""

    @login_required
    def post(self):
        data = FollowCreateSchema().load(request.get_json(silent=True) or {})
        from_id = current_user_id()
        follow, created = SocialService.follow(from_id, data["to_id"])
        body = {
            "id": follow.id,
            "from_id": follow.from_user_id,
            "to_id": follow.to_user_id,
        }
        # 新建/恢复返回 201，已在关注（幂等）返回 200
        return ok(body, 201 if created else 200)

    @login_required
    def get(self):
        args = FollowListQuerySchema().load(request.args)
        user_id = args.get("user_id") or current_user_id()
        cursor = args.get("cursor")
        limit = args.get("limit")
        if args["type"] == "fans":
            page = SocialService.list_followers(user_id, cursor, limit)
        else:
            page = SocialService.list_following(user_id, cursor, limit)
        return ok(_page_body(page))


class FollowResource(Resource):
    """/api/follows/<to_id> —— DELETE 取消关注（成功分支必须 return，修 CR #5）。"""

    @login_required
    def delete(self, to_id):
        from_id = current_user_id()
        SocialService.unfollow(from_id, to_id)
        # 修 CR #5：成功分支返回明确响应（幂等，无论此前是否关注均成功）
        return ok({"from_id": from_id, "to_id": to_id, "deleted": True})


def register(api):
    """向 flask-restful Api 注册本域 Resource。"""
    api.add_resource(FollowListResource, "/api/follows")
    api.add_resource(FollowResource, "/api/follows/<int:to_id>")
