"""identity 域 HTTP 资源注册入口（flask-restful）。

Resource 只做：解析 -> 鉴权 -> 调 service -> ok；业务与事务在 service 层。
"""
from flask import Response, request
from flask_jwt_extended import verify_jwt_in_request
from flask_restful import Resource

from ezgym.core import captcha
from ezgym.core.errors import BadRequest
from ezgym.core.response import ok
from ezgym.core.security import admin_required, current_user_id, login_required
from ezgym.domains.identity.schemas import (
    ChangePasswordSchema,
    LoginSchema,
    PasswordResetConfirmSchema,
    PasswordResetRequestSchema,
    RegisterSchema,
    UpdateProfileSchema,
)
from ezgym.domains.identity.service import (
    ProfileService,
    UserService,
    get_user_public,
)


def _json_body() -> dict:
    """取 JSON body（缺省空 dict，交给 schema 报必填错）。"""
    return request.get_json(silent=True) or {}


class RegisterResource(Resource):
    def post(self):
        data = RegisterSchema().load(_json_body())
        user = UserService.register(data)
        payload = get_user_public(user.id)
        payload["account"] = user.account
        payload["permission"] = int(user.permission)
        return ok(payload, 201)


class LoginResource(Resource):
    def post(self):
        data = LoginSchema().load(_json_body())
        # 先验证码后密码
        if not captcha.verify_code(data["captcha_code"]):
            raise BadRequest("验证码错误")
        user = UserService.authenticate(data["account"], data["password"])
        from ezgym.core.security import create_token

        token = create_token(user)
        public = get_user_public(user.id)
        return ok(
            {
                "token": token,
                "user": {
                    "id": user.id,
                    "nick_name": public["nick_name"],
                    "avatar": public["avatar"],
                    "permission": int(user.permission),
                },
            },
            200,
        )


class CaptchaResource(Resource):
    def get(self):
        text, png_bytes = captcha.generate()
        captcha.store_code(text)
        return Response(png_bytes, mimetype="image/png")


class PasswordResetResource(Resource):
    def post(self):
        """发起找回密码：始终返回成功（不暴露邮箱是否存在）。"""
        data = PasswordResetRequestSchema().load(_json_body())
        UserService.request_password_reset(data["email"])
        return ok({"message": "若邮箱存在，重置邮件已发送"}, 200)

    def put(self):
        """token 改密。"""
        data = PasswordResetConfirmSchema().load(_json_body())
        UserService.confirm_password_reset(data["token"], data["new_password"])
        return ok({"message": "密码已重置"}, 200)


class UserListResource(Resource):
    method_decorators = [admin_required]

    def get(self):
        cursor = request.args.get("cursor", type=int)
        limit = request.args.get("limit", type=int)
        page = UserService.list_users(cursor, limit)
        return ok(
            {
                "items": page.items,
                "next_cursor": page.next_cursor,
                "count": page.count,
            },
            200,
        )


class UserMeResource(Resource):
    method_decorators = [login_required]

    def put(self):
        data = UpdateProfileSchema().load(_json_body())
        user = UserService.update_profile(current_user_id(), data)
        info = user.info
        return ok(
            {
                "id": user.id,
                "nick_name": info.nick_name if info else None,
                "avatar": info.avatar if info else None,
                "phone": info.phone if info else None,
                "gender": info.gender if info else None,
                "age": info.age if info else None,
                "email": info.email if info else None,
                "description": info.description if info else None,
            },
            200,
        )


class UserMePasswordResource(Resource):
    method_decorators = [login_required]

    def put(self):
        data = ChangePasswordSchema().load(_json_body())
        UserService.change_password(
            current_user_id(), data["old_password"], data["new_password"]
        )
        return ok({"message": "密码已更新"}, 200)


class UserResource(Resource):
    method_decorators = [admin_required]

    def delete(self, user_id: int):
        UserService.delete_user(user_id)
        return ok({"id": user_id, "deleted": True}, 200)


def _cursor_args() -> tuple[int | None, int | None]:
    return (
        request.args.get("cursor", type=int),
        request.args.get("limit", type=int),
    )


def _page_body(page) -> dict:
    return {"items": page.items, "next_cursor": page.next_cursor, "count": page.count}


class UserProfileResource(Resource):
    """个人主页聚合（软登录）。"""

    def get(self, user_id: int):
        verify_jwt_in_request(optional=True)
        data = ProfileService.get_profile(user_id, current_user_id())
        return ok(data, 200)


class UserBlogsResource(Resource):
    """某用户的动态列表（软登录，游标分页）。"""

    def get(self, user_id: int):
        verify_jwt_in_request(optional=True)
        cursor, limit = _cursor_args()
        return ok(_page_body(ProfileService.list_blogs(user_id, cursor, limit)), 200)


class UserCommentsResource(Resource):
    def get(self, user_id: int):
        verify_jwt_in_request(optional=True)
        cursor, limit = _cursor_args()
        return ok(_page_body(ProfileService.list_comments(user_id, cursor, limit)), 200)


class UserCollectionsResource(Resource):
    def get(self, user_id: int):
        verify_jwt_in_request(optional=True)
        cursor, limit = _cursor_args()
        return ok(
            _page_body(ProfileService.list_collections(user_id, cursor, limit)), 200
        )


class UserFollowersResource(Resource):
    def get(self, user_id: int):
        verify_jwt_in_request(optional=True)
        cursor, limit = _cursor_args()
        return ok(
            _page_body(ProfileService.list_followers(user_id, cursor, limit)), 200
        )


class UserFollowingResource(Resource):
    def get(self, user_id: int):
        verify_jwt_in_request(optional=True)
        cursor, limit = _cursor_args()
        return ok(
            _page_body(ProfileService.list_following(user_id, cursor, limit)), 200
        )


class RegistrationStatsResource(Resource):
    """按天注册量统计（ADMIN）。"""

    method_decorators = [admin_required]

    def get(self):
        data = ProfileService.registration_stats(
            request.args.get("start"), request.args.get("end")
        )
        return ok(data, 200)


def register(api):
    """向 flask-restful Api 注册本域 Resource。"""
    api.add_resource(RegisterResource, "/api/auth/register")
    api.add_resource(LoginResource, "/api/auth/login")
    api.add_resource(CaptchaResource, "/api/auth/captcha")
    api.add_resource(PasswordResetResource, "/api/auth/password-reset")
    api.add_resource(UserListResource, "/api/users")
    api.add_resource(UserMeResource, "/api/users/me")
    api.add_resource(UserMePasswordResource, "/api/users/me/password")
    api.add_resource(UserResource, "/api/users/<int:user_id>")
    api.add_resource(UserProfileResource, "/api/users/<int:user_id>/profile")
    api.add_resource(UserBlogsResource, "/api/users/<int:user_id>/blogs")
    api.add_resource(UserCommentsResource, "/api/users/<int:user_id>/comments")
    api.add_resource(UserCollectionsResource, "/api/users/<int:user_id>/collections")
    api.add_resource(UserFollowersResource, "/api/users/<int:user_id>/followers")
    api.add_resource(UserFollowingResource, "/api/users/<int:user_id>/following")
    api.add_resource(RegistrationStatsResource, "/api/stats/registrations")
