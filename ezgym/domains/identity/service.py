"""identity 域 service（业务逻辑 + 事务边界）。

约定：一个方法 = 一个事务；写操作方法内自行 commit（复用 BaseService）。
跨域取数只暴露 get_user_public / get_users_public / user_exists 三个函数，
禁止他域直连 identity 的 model。
"""
import uuid
from datetime import datetime, timedelta

from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from ezgym.core.database import db
from ezgym.core.errors import BadRequest, Conflict, NotFound, Unauthorized
from ezgym.core.pagination import Page, cursor_paginate
from ezgym.core.security import (
    Permission,
    hash_password,
    verify_password,
)
from ezgym.domains.identity.models import User, UserInfo

# 发信函数：notification 域尚未实现该函数时降级为 no-op（记日志），
# password-reset 端点仍可用；测试通过 monkeypatch 本模块该名字替换掉。
try:  # pragma: no cover - 取决于 notification 域实现进度
    from ezgym.support.notification.service import send_password_reset_email
except (ImportError, AttributeError):  # pragma: no cover

    def send_password_reset_email(email, reset_link=None):
        current_app.logger.warning(
            "notification.send_password_reset_email 不可用，跳过发信: %s", email
        )
        return False


__all__ = [
    "UserService",
    "ProfileService",
    "get_user_public",
    "get_users_public",
    "user_exists",
]

_MAX_STATS_SPAN_DAYS = 30

_RESET_TOKEN_SALT = "identity.password-reset"


def _public_dict(user: User) -> dict:
    """从 User(+info) 组装公开信息 {id, nick_name, avatar}。"""
    info = user.info
    return {
        "id": user.id,
        "nick_name": info.nick_name if info else None,
        "avatar": info.avatar if info else None,
    }


class UserService:
    """用户 / 认证 / 资料业务。"""

    model = User

    # ---------- 查询 ----------
    @classmethod
    def base_query(cls, include_deleted: bool = False):
        q = User.query
        if not include_deleted:
            q = q.filter(User.is_deleted.is_(False))
        return q

    @classmethod
    def get(cls, user_id: int, include_deleted: bool = False) -> User | None:
        return cls.base_query(include_deleted=include_deleted).filter(
            User.id == user_id
        ).first()

    @classmethod
    def get_or_404(cls, user_id: int) -> User:
        user = cls.get(user_id)
        if user is None:
            raise NotFound("用户不存在")
        return user

    @classmethod
    def get_by_account(cls, account: str) -> User | None:
        return cls.base_query().filter(User.account == account).first()

    # ---------- 注册 ----------
    @classmethod
    def register(cls, data: dict) -> User:
        """注册新用户。account 冲突 -> Conflict(409)；permission 强制 NORMAL。"""
        account = data["account"]
        if cls.get_by_account(account) is not None:
            raise Conflict("账号已存在")

        user = User(
            account=account,
            password_hash=hash_password(data["password"]),
            permission=int(Permission.NORMAL),
            number=cls._new_number(),
        )
        user.info = UserInfo(
            nick_name=data.get("nick_name"),
            phone=data.get("phone"),
            gender=data.get("gender"),
            age=data.get("age"),
            email=data.get("email"),
            description=data.get("description"),
            avatar=data.get("avatar"),
        )
        db.session.add(user)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise Conflict("账号或编号冲突")
        return user

    @staticmethod
    def _new_number() -> str:
        return uuid.uuid4().hex[:20]

    # ---------- 登录 ----------
    @classmethod
    def authenticate(cls, account: str, password: str) -> User:
        """校验账号密码，成功返回 User，失败抛 Unauthorized。"""
        user = cls.get_by_account(account)
        if user is None or not verify_password(password, user.password_hash):
            raise Unauthorized("账号或密码错误")
        return user

    # ---------- 改密（登录态）----------
    @classmethod
    def change_password(cls, user_id: int, old_password: str, new_password: str) -> None:
        """校验旧密码后改新密。

        修 CR #6：异常必须上抛，禁止用 finally return 吞异常。这里任何异常
        （旧密码错误、commit 失败）都会向上传播。
        """
        user = cls.get_or_404(user_id)
        if not verify_password(old_password, user.password_hash):
            raise BadRequest("旧密码错误")
        user.password_hash = hash_password(new_password)
        db.session.commit()

    # ---------- 改资料 ----------
    @classmethod
    def update_profile(cls, user_id: int, data: dict) -> User:
        """更新本人 UserInfo，仅更新出现的键（修 CR #15：不改头像不报错）。"""
        user = cls.get_or_404(user_id)
        info = user.info
        if info is None:
            info = UserInfo(user_id=user.id)
            user.info = info
        for key in ("nick_name", "phone", "gender", "age", "email",
                    "description", "avatar"):
            if key in data:
                setattr(info, key, data[key])
        db.session.commit()
        return user

    # ---------- 删除（ADMIN）----------
    @classmethod
    def delete_user(cls, user_id: int) -> None:
        """软删 user + user_info（同一事务）。"""
        user = cls.get_or_404(user_id)
        user.is_deleted = True
        if user.info is not None:
            user.info.is_deleted = True
        db.session.commit()

    # ---------- 列表（ADMIN，游标分页）----------
    @classmethod
    def list_users(cls, cursor: int | None, limit: int | None) -> Page:
        page = cursor_paginate(cls.base_query(), cursor, limit, User.id)
        page.items = [
            {
                "id": u.id,
                "account": u.account,
                "nick_name": u.info.nick_name if u.info else None,
                "avatar": u.info.avatar if u.info else None,
                "permission": int(u.permission),
                "created_at": u.created_at,
            }
            for u in page.items
        ]
        return page

    # ---------- 找回密码 ----------
    @staticmethod
    def _serializer() -> URLSafeTimedSerializer:
        return URLSafeTimedSerializer(
            current_app.config["SECRET_KEY"], salt=_RESET_TOKEN_SALT
        )

    @classmethod
    def make_reset_token(cls, user_id: int) -> str:
        return cls._serializer().dumps({"uid": user_id})

    @classmethod
    def parse_reset_token(cls, token: str) -> int:
        """校验 token，返回 user_id；失败/过期 -> BadRequest。"""
        max_age = current_app.config.get("BACK_PASSWORD_EXP", 30 * 60)
        try:
            payload = cls._serializer().loads(token, max_age=max_age)
        except SignatureExpired as exc:
            raise BadRequest("重置链接已过期") from exc
        except BadSignature as exc:
            raise BadRequest("重置链接无效") from exc
        return int(payload["uid"])

    @classmethod
    def request_password_reset(cls, email: str) -> None:
        """发起找回密码。始终成功返回（不暴露邮箱是否存在）。"""
        user = (
            cls.base_query()
            .join(UserInfo, UserInfo.user_id == User.id)
            .filter(UserInfo.email == email, UserInfo.is_deleted.is_(False))
            .first()
        )
        if user is not None:
            token = cls.make_reset_token(user.id)
            base = current_app.config.get("USER_HOST", "").rstrip("/")
            reset_link = f"{base}/reset-password?token={token}" if base else None
            send_password_reset_email(email, reset_link)

    @classmethod
    def confirm_password_reset(cls, token: str, new_password: str) -> None:
        """校验 token 后改密。"""
        user_id = cls.parse_reset_token(token)
        user = cls.get_or_404(user_id)
        user.password_hash = hash_password(new_password)
        db.session.commit()


class ProfileService:
    """个人主页聚合 + 注册量统计（wave B）。

    跨域计数/列表一律经他域 service 层函数（模块导入 + 运行时调用），
    禁止 import 他域 model；上游 service 在方法内惰性导入，避免模块级循环依赖。
    注册统计是 identity 自己的数据，直接查 User。
    """

    # ---------- 个人主页聚合 ----------
    @classmethod
    def get_profile(cls, user_id: int, viewer_id: int | None = None) -> dict:
        """聚合公开信息 + 各域计数 + 当前登录者是否已关注该用户。

        用户不存在 -> NotFound。viewer_id 为 None（未登录）时 is_following=False。
        """
        public = get_user_public(user_id)
        if public is None:
            raise NotFound("用户不存在")

        from ezgym.domains.content import service as content_service
        from ezgym.domains.course import service as course_service
        from ezgym.domains.social import service as social_service

        is_following = (
            social_service.is_following(viewer_id, user_id)
            if viewer_id is not None
            else False
        )
        return {
            "user": public,
            "blog_count": content_service.count_blogs_by_user(user_id),
            "fans_count": social_service.count_fans(user_id),
            "following_count": social_service.count_following(user_id),
            "collection_count": course_service.count_collections_by_user(user_id),
            "is_following": is_following,
        }

    # ---------- 子资源列表（游标分页，委托他域 service）----------
    @classmethod
    def list_blogs(cls, user_id: int, cursor: int | None, limit: int | None) -> Page:
        from ezgym.domains.content import service as content_service

        return content_service.list_blogs_by_user(user_id, cursor, limit)

    @classmethod
    def list_comments(cls, user_id: int, cursor: int | None, limit: int | None) -> Page:
        from ezgym.domains.interaction import service as interaction_service

        return interaction_service.list_comments_by_user(user_id, cursor, limit)

    @classmethod
    def list_collections(cls, user_id: int, cursor: int | None,
                         limit: int | None) -> Page:
        from ezgym.domains.course import service as course_service

        return course_service.list_collections_by_user(user_id, cursor, limit)

    @classmethod
    def list_followers(cls, user_id: int, cursor: int | None,
                       limit: int | None) -> Page:
        from ezgym.domains.social import service as social_service

        return social_service.list_followers(user_id, cursor, limit)

    @classmethod
    def list_following(cls, user_id: int, cursor: int | None,
                       limit: int | None) -> Page:
        from ezgym.domains.social import service as social_service

        return social_service.list_following(user_id, cursor, limit)

    # ---------- 注册量按天统计（ADMIN）----------
    @classmethod
    def registration_stats(cls, start: str | None, end: str | None) -> list[dict]:
        """按天统计 user 表注册量，返回 [{date, count}]。

        跨度 > 30 天 -> BadRequest；缺参/日期格式错误 -> BadRequest。
        修 CR #21 类问题：区间内无注册的日期计 0，整体空结果也正常返回
        （返回全 0 的列表），绝不把"无数据"当异常。
        """
        start_date = cls._parse_date(start, "start")
        end_date = cls._parse_date(end, "end")
        if end_date < start_date:
            raise BadRequest("结束日期不能早于开始日期")
        span = (end_date - start_date).days
        if span > _MAX_STATS_SPAN_DAYS:
            raise BadRequest(f"时间跨度不能超过 {_MAX_STATS_SPAN_DAYS} 天")

        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date + timedelta(days=1), datetime.min.time())
        # 注册量统计包含后续被软删的用户（软删不改变"曾注册"这一事实）
        rows = (
            User.query.filter(
                User.created_at >= start_dt, User.created_at < end_dt
            ).all()
        )
        buckets: dict = {}
        for user in rows:
            if user.created_at is None:
                continue
            key = user.created_at.date()
            buckets[key] = buckets.get(key, 0) + 1

        result = []
        for offset in range(span + 1):
            day = start_date + timedelta(days=offset)
            result.append({"date": day.isoformat(), "count": buckets.get(day, 0)})
        return result

    @staticmethod
    def _parse_date(value: str | None, field: str):
        if not value:
            raise BadRequest(f"缺少参数 {field}")
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except (ValueError, TypeError) as exc:
            raise BadRequest(f"{field} 日期格式应为 YYYY-MM-DD") from exc


# ============================================================
# 跨域 service 函数（供 wave B 及他域消费；禁止他域直连 identity model）
# ============================================================

def get_user_public(user_id: int) -> dict | None:
    """{id, nick_name, avatar}；软删/不存在返回 None。"""
    user = UserService.get(user_id)
    if user is None:
        return None
    return _public_dict(user)


def get_users_public(user_ids: list[int]) -> dict[int, dict]:
    """批量取公开信息，key=user_id；软删/不存在的 id 不出现在结果里。"""
    if not user_ids:
        return {}
    users = (
        UserService.base_query()
        .filter(User.id.in_(list(set(user_ids))))
        .all()
    )
    return {u.id: _public_dict(u) for u in users}


def user_exists(user_id: int) -> bool:
    """用户是否存在且未软删。"""
    return UserService.get(user_id) is not None
