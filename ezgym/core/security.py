"""密码哈希、JWT 签发与鉴权装饰器。

- 密码：bcrypt，每用户随机盐（修 CR：MD5+固定盐弱哈希）。
- JWT：基于 flask-jwt-extended，identity=str(user.id)，permission 放 additional_claims。
- 权限：IntEnum 位掩码，admin_required 每次从 DB 实时加载 user 校验（修 CR #10）。
"""
from enum import IntEnum
from functools import wraps

import bcrypt
from flask import current_app
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
    verify_jwt_in_request,
)

from ezgym.core.errors import Forbidden, Unauthorized
from ezgym.core.response import make_body

__all__ = [
    "Permission",
    "hash_password",
    "verify_password",
    "create_token",
    "login_required",
    "admin_required",
    "current_user_id",
    "has_permission",
    "register_jwt_error_handlers",
]


class Permission(IntEnum):
    """权限位掩码。ADMIN 覆盖 NORMAL（按位与判定）。"""

    NORMAL = 0b00000001  # 1
    ADMIN = 0b11111111  # 255


# ---------------- 密码 ----------------

def hash_password(raw: str) -> str:
    """bcrypt 哈希（含随机盐），返回可存库的 str。"""
    rounds = current_app.config.get("BCRYPT_ROUNDS", 12) if current_app else 12
    salt = bcrypt.gensalt(rounds=rounds)
    return bcrypt.hashpw(raw.encode("utf-8"), salt).decode("utf-8")


def verify_password(raw: str, hashed: str) -> bool:
    """校验明文与 bcrypt 哈希。任何异常（如哈希格式错误）都视为不匹配。"""
    if not raw or not hashed:
        return False
    try:
        return bcrypt.checkpw(raw.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# ---------------- JWT ----------------

def create_token(user) -> str:
    """为 user 签发 access token。identity=str(user.id)，claims 带 permission。"""
    return create_access_token(
        identity=str(user.id),
        additional_claims={"permission": int(user.permission)},
    )


def current_user_id() -> int | None:
    """取当前登录用户 id（int）。未登录返回 None。"""
    identity = get_jwt_identity()
    return int(identity) if identity is not None else None


def has_permission(user_permission: int, required: Permission) -> bool:
    """按位与判定：user 是否拥有 required 权限。"""
    return (int(user_permission) & int(required)) == int(required)


# ---------------- 装饰器 ----------------

def login_required(fn):
    """需要有效 token（任意登录用户）。等价 jwt_required 的语义封装。"""

    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)

    return wrapper


def register_jwt_error_handlers(jwt_manager) -> None:
    """让 flask-jwt-extended 的鉴权失败也走统一 {errno,code,data} 信封 + 401。

    默认 flask-jwt-extended 返回 {"msg": ...}，与全站响应契约不一致；这里统一接管
    缺失/无效/过期 token 三种情形，全部映射为 401 + 契约 body。
    """

    @jwt_manager.unauthorized_loader
    def _missing_token(reason):  # 无 Authorization 头
        return make_body(data="缺少或无效的认证凭证", code=401, errno=1), 401

    @jwt_manager.invalid_token_loader
    def _invalid_token(reason):  # 签名/格式错误
        return make_body(data="无效的认证凭证", code=401, errno=1), 401

    @jwt_manager.expired_token_loader
    def _expired_token(header, payload):  # 过期
        return make_body(data="登录已过期，请重新登录", code=401, errno=1), 401


def admin_required(fn):
    """需要 ADMIN 权限。从 DB 实时加载 user 校验 permission（修 CR #10）。"""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        # 延迟 import 避免 core 依赖 domain（仅在运行期读取，不产生模块级循环）
        from ezgym.domains.identity.models import User

        uid = current_user_id()
        user = User.query.filter_by(id=uid, is_deleted=False).first() if uid else None
        if user is None:
            raise Unauthorized("用户不存在或已失效")
        if not has_permission(user.permission, Permission.ADMIN):
            raise Forbidden("需要管理员权限")
        return fn(*args, **kwargs)

    return wrapper
