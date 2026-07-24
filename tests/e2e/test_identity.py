"""identity 域 e2e：真实 client 打真实端点，断言 HTTP 状态码 + {errno,code,data}。

覆盖：注册成功/account 重复 409、登录验证码错误 400/密码错误、验证码 PNG、
未登录改资料 401、NORMAL 删用户 403、ADMIN 删成功、改密旧密码错误(CR #6)、
不改头像回传原值不报错(CR #15)。
"""
import pytest


def _assert_body(payload, http_status):
    assert payload["errno"] == 0
    assert payload["code"] == http_status
    assert "data" in payload


def _set_captcha(client, code="ABCDE"):
    """把验证码直接写进 session，模拟 GET /captcha 后的状态。"""
    with client.session_transaction() as sess:
        sess["auth_code"] = code.upper()


# ---------------- 注册 ----------------

def test_register_success(client):
    resp = client.post(
        "/api/auth/register",
        json={"account": "newuser1", "password": "secret123", "nick_name": "Newbie"},
    )
    assert resp.status_code == 201
    body = resp.get_json()
    _assert_body(body, 201)
    assert body["data"]["nick_name"] == "Newbie"
    assert body["data"]["account"] == "newuser1"


def test_register_ignores_permission_escalation(client):
    resp = client.post(
        "/api/auth/register",
        json={
            "account": "sneaky1",
            "password": "secret123",
            "nick_name": "Sneaky",
            "permission": 255,
        },
    )
    assert resp.status_code == 201
    assert body_perm(resp) == 1


def body_perm(resp):
    return resp.get_json()["data"]["permission"]


def test_register_duplicate_account_409(client):
    payload = {"account": "dupuser", "password": "secret123", "nick_name": "Dup"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 409
    body = resp.get_json()
    assert body["errno"] == 1
    assert body["code"] == 409


def test_register_validation_400(client):
    resp = client.post("/api/auth/register", json={"account": "x"})
    assert resp.status_code == 400
    assert resp.get_json()["errno"] == 1


# ---------------- 验证码 ----------------

def test_captcha_returns_png(client):
    resp = client.get("/api/auth/captcha")
    assert resp.status_code == 200
    assert resp.mimetype == "image/png"
    assert resp.data[:8] == b"\x89PNG\r\n\x1a\n"


# ---------------- 登录 ----------------

def _register(client, account="loginer", password="secret123"):
    client.post(
        "/api/auth/register",
        json={"account": account, "password": password, "nick_name": account},
    )


def test_login_success(client):
    _register(client)
    _set_captcha(client, "ABCDE")
    resp = client.post(
        "/api/auth/login",
        json={"account": "loginer", "password": "secret123", "captcha_code": "abcde"},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    _assert_body(body, 200)
    assert "token" in body["data"]
    assert body["data"]["user"]["permission"] == 1


def test_login_wrong_captcha_400(client):
    _register(client)
    _set_captcha(client, "ABCDE")
    resp = client.post(
        "/api/auth/login",
        json={"account": "loginer", "password": "secret123", "captcha_code": "WRONG"},
    )
    assert resp.status_code == 400
    assert resp.get_json()["code"] == 400


def test_login_wrong_password_401(client):
    _register(client)
    _set_captcha(client, "ABCDE")
    resp = client.post(
        "/api/auth/login",
        json={"account": "loginer", "password": "nope", "captcha_code": "ABCDE"},
    )
    assert resp.status_code == 401


# ---------------- 改资料 ----------------

def test_update_profile_requires_login_401(client):
    resp = client.put("/api/users/me", json={"nick_name": "X"})
    assert resp.status_code == 401


def test_update_profile_success(client, make_user, auth_headers):
    user = make_user()
    resp = client.put(
        "/api/users/me", json={"nick_name": "改后的昵称"}, headers=auth_headers(user)
    )
    assert resp.status_code == 200
    body = resp.get_json()
    _assert_body(body, 200)
    assert body["data"]["nick_name"] == "改后的昵称"


def test_update_profile_keep_avatar_no_error(client, make_user, auth_headers):
    """回归 CR #15：回传原头像值不应报错。"""
    user = make_user()
    from ezgym.core.database import db

    user.info.avatar = "/media/images/old.jpg"
    db.session.commit()
    resp = client.put(
        "/api/users/me",
        json={"nick_name": "N", "avatar": "/media/images/old.jpg"},
        headers=auth_headers(user),
    )
    assert resp.status_code == 200


# ---------------- 改密 ----------------

def test_change_password_wrong_old_400(client, make_user, auth_headers):
    """回归 CR #6：旧密码错误必须返回错误（异常上抛），不静默吞。"""
    user = make_user(password="oldpass1")
    resp = client.put(
        "/api/users/me/password",
        json={"old_password": "WRONG", "new_password": "newpass2"},
        headers=auth_headers(user),
    )
    assert resp.status_code == 400
    assert resp.get_json()["errno"] == 1


def test_change_password_success(client, make_user, auth_headers):
    user = make_user(password="oldpass1")
    resp = client.put(
        "/api/users/me/password",
        json={"old_password": "oldpass1", "new_password": "newpass2"},
        headers=auth_headers(user),
    )
    assert resp.status_code == 200


# ---------------- 用户列表（ADMIN）----------------

def test_user_list_requires_admin_403(client, make_user, auth_headers):
    user = make_user()
    resp = client.get("/api/users", headers=auth_headers(user))
    assert resp.status_code == 403


def test_user_list_admin_ok(client, admin_headers, make_user):
    make_user()
    make_user()
    resp = client.get("/api/users", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.get_json()
    _assert_body(body, 200)
    assert "items" in body["data"]
    assert body["data"]["count"] >= 2


# ---------------- 删除用户（ADMIN）----------------

def test_delete_user_normal_forbidden_403(client, make_user, auth_headers):
    normal = make_user()
    victim = make_user()
    resp = client.delete(f"/api/users/{victim.id}", headers=auth_headers(normal))
    assert resp.status_code == 403


def test_delete_user_admin_ok(client, admin_headers, make_user):
    victim = make_user()
    resp = client.delete(f"/api/users/{victim.id}", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.get_json()
    _assert_body(body, 200)
    assert body["data"]["deleted"] is True


def test_delete_missing_user_404(client, admin_headers):
    resp = client.delete("/api/users/999999", headers=admin_headers)
    assert resp.status_code == 404


# ---------------- 找回密码（mock 发信）----------------

def test_password_reset_request_always_ok(client, make_user, monkeypatch):
    sent = {}

    def fake_send(email, reset_link=None):
        sent["email"] = email
        return True

    monkeypatch.setattr(
        "ezgym.domains.identity.service.send_password_reset_email", fake_send
    )
    user = make_user()
    user.info.email = "reset@example.com"
    from ezgym.core.database import db

    db.session.commit()

    resp = client.post("/api/auth/password-reset", json={"email": "reset@example.com"})
    assert resp.status_code == 200
    assert sent["email"] == "reset@example.com"

    # 不存在的邮箱也返回成功，且不发信
    sent.clear()
    resp = client.post("/api/auth/password-reset", json={"email": "nobody@example.com"})
    assert resp.status_code == 200
    assert sent == {}


def test_password_reset_confirm_changes_password(client, make_user):
    from ezgym.domains.identity.service import UserService

    user = make_user(password="oldpass1")
    token = UserService.make_reset_token(user.id)
    resp = client.put(
        "/api/auth/password-reset",
        json={"token": token, "new_password": "brandnew1"},
    )
    assert resp.status_code == 200
    # 用新密码可登录
    _set_captcha(client, "ABCDE")
    login = client.post(
        "/api/auth/login",
        json={"account": user.account, "password": "brandnew1", "captcha_code": "ABCDE"},
    )
    assert login.status_code == 200


def test_password_reset_confirm_bad_token_400(client):
    resp = client.put(
        "/api/auth/password-reset",
        json={"token": "garbage", "new_password": "brandnew1"},
    )
    assert resp.status_code == 400
