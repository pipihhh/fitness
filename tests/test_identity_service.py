"""identity 域 service 层单测。

直接调 service，覆盖：注册（成功/去重/提权拦截）、登录校验、改密异常上抛
（回归 CR #6）、跨域 get_user_public / get_users_public / user_exists。
"""
import pytest

from ezgym.core.errors import BadRequest, Conflict, Unauthorized
from ezgym.core.security import Permission, verify_password
from ezgym.domains.identity.models import User
from ezgym.domains.identity.service import (
    UserService,
    get_user_public,
    get_users_public,
    user_exists,
)


def _register_payload(**over):
    data = {
        "account": "alice001",
        "password": "secret123",
        "nick_name": "Alice",
        "email": "alice@example.com",
    }
    data.update(over)
    return data


def test_register_creates_user_and_info(app):
    user = UserService.register(_register_payload())
    assert user.id is not None
    assert user.info.nick_name == "Alice"
    assert user.info.email == "alice@example.com"
    # 密码已哈希，非明文
    assert user.password_hash != "secret123"
    assert verify_password("secret123", user.password_hash)


def test_register_forces_normal_permission(app):
    # 即使入参尝试带 ADMIN，service 也强制 NORMAL
    user = UserService.register(_register_payload(permission=int(Permission.ADMIN)))
    assert user.permission == int(Permission.NORMAL)


def test_register_duplicate_account_conflict(app):
    UserService.register(_register_payload())
    with pytest.raises(Conflict):
        UserService.register(_register_payload(nick_name="Alice2"))


def test_authenticate_success_and_failure(app):
    UserService.register(_register_payload(password="rightpass"))
    user = UserService.authenticate("alice001", "rightpass")
    assert user.account == "alice001"
    with pytest.raises(Unauthorized):
        UserService.authenticate("alice001", "wrongpass")
    with pytest.raises(Unauthorized):
        UserService.authenticate("nobody", "whatever")


def test_change_password_success(app, make_user):
    user = make_user(password="oldpass1")
    from ezgym.core.database import db

    UserService.change_password(user.id, "oldpass1", "newpass2")
    fresh = db.session.get(User, user.id)
    assert verify_password("newpass2", fresh.password_hash)


def test_change_password_wrong_old_raises_not_swallowed(app, make_user):
    """回归 CR #6：旧密码错误必须上抛异常，不得被吞掉返回 None。"""
    user = make_user(password="oldpass1")
    with pytest.raises(BadRequest):
        UserService.change_password(user.id, "WRONG", "newpass2")
    # 密码未被改动
    from ezgym.core.database import db

    fresh = db.session.get(User, user.id)
    assert verify_password("oldpass1", fresh.password_hash)


def test_update_profile_partial_keeps_avatar(app, make_user):
    """回归 CR #15：不传 avatar 只改昵称，不应报错、头像保持原值。"""
    user = make_user()
    user.info.avatar = "/media/images/x.jpg"
    from ezgym.core.database import db

    db.session.commit()
    UserService.update_profile(user.id, {"nick_name": "NewNick"})
    assert user.info.nick_name == "NewNick"
    assert user.info.avatar == "/media/images/x.jpg"


def test_delete_user_soft_deletes_user_and_info(app, make_user):
    user = make_user()
    uid = user.id
    UserService.delete_user(uid)
    assert user.is_deleted is True
    assert user.info.is_deleted is True
    assert user_exists(uid) is False


def test_get_user_public_shape_and_none(app, make_user):
    user = make_user(nick_name="Bob")
    pub = get_user_public(user.id)
    assert pub == {"id": user.id, "nick_name": "Bob", "avatar": user.info.avatar}
    # 软删后返回 None
    UserService.delete_user(user.id)
    assert get_user_public(user.id) is None
    # 不存在返回 None
    assert get_user_public(999999) is None


def test_get_users_public_batch(app, make_user):
    u1 = make_user(nick_name="U1")
    u2 = make_user(nick_name="U2")
    u3 = make_user(nick_name="U3")
    UserService.delete_user(u3.id)
    result = get_users_public([u1.id, u2.id, u3.id, 888888])
    assert set(result.keys()) == {u1.id, u2.id}
    assert result[u1.id]["nick_name"] == "U1"
    assert result[u2.id]["nick_name"] == "U2"


def test_get_users_public_empty(app):
    assert get_users_public([]) == {}


def test_password_reset_token_roundtrip(app, make_user):
    user = make_user()
    token = UserService.make_reset_token(user.id)
    assert UserService.parse_reset_token(token) == user.id
    with pytest.raises(BadRequest):
        UserService.parse_reset_token("garbage-token")
