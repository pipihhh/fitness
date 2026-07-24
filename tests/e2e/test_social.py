"""social 域 e2e：打真实端点，断言 HTTP status + {errno, code, data} 契约。

覆盖：未登录 401、关注自己 400、关注不存在用户 404、重复关注幂等、
取消关注返回明确响应（修 CR #5 回归）、fans/following 列表带对方昵称。
"""


def _assert_contract(body, expected_code):
    assert set(body.keys()) == {"errno", "code", "data"}
    assert body["errno"] == 0
    assert body["code"] == expected_code


# ---------- 鉴权 ----------
def test_follow_requires_login(client, make_user):
    b = make_user()
    resp = client.post("/api/follows", json={"to_id": b.id})
    assert resp.status_code == 401
    assert resp.get_json()["errno"] == 1


def test_list_follows_requires_login(client):
    resp = client.get("/api/follows?type=following")
    assert resp.status_code == 401


# ---------- 关注 ----------
def test_follow_success(client, make_user, auth_headers):
    a = make_user()
    b = make_user()
    resp = client.post("/api/follows", json={"to_id": b.id}, headers=auth_headers(a))
    assert resp.status_code == 201
    body = resp.get_json()
    _assert_contract(body, 201)
    assert body["data"]["from_id"] == a.id
    assert body["data"]["to_id"] == b.id


def test_follow_self_bad_request(client, make_user, auth_headers):
    a = make_user()
    resp = client.post("/api/follows", json={"to_id": a.id}, headers=auth_headers(a))
    assert resp.status_code == 400
    assert resp.get_json()["errno"] == 1


def test_follow_nonexistent_user_not_found(client, make_user, auth_headers):
    a = make_user()
    resp = client.post("/api/follows", json={"to_id": 999999},
                       headers=auth_headers(a))
    assert resp.status_code == 404
    assert resp.get_json()["errno"] == 1


def test_follow_validation_error(client, make_user, auth_headers):
    a = make_user()
    resp = client.post("/api/follows", json={}, headers=auth_headers(a))
    assert resp.status_code == 400
    assert resp.get_json()["errno"] == 1


def test_follow_idempotent(client, make_user, auth_headers):
    a = make_user()
    b = make_user()
    headers = auth_headers(a)
    first = client.post("/api/follows", json={"to_id": b.id}, headers=headers)
    assert first.status_code == 201
    # 重复关注：幂等，返回 200 且不报错
    second = client.post("/api/follows", json={"to_id": b.id}, headers=headers)
    assert second.status_code == 200
    _assert_contract(second.get_json(), 200)
    assert second.get_json()["data"]["to_id"] == b.id


# ---------- 取消关注（修 CR #5 回归）----------
def test_unfollow_returns_explicit_response(client, make_user, auth_headers):
    a = make_user()
    b = make_user()
    headers = auth_headers(a)
    client.post("/api/follows", json={"to_id": b.id}, headers=headers)

    resp = client.delete(f"/api/follows/{b.id}", headers=headers)
    assert resp.status_code == 200
    body = resp.get_json()
    # #5 回归：成功分支必须返回明确 body，而不是空/None
    _assert_contract(body, 200)
    assert body["data"] is not None
    assert body["data"]["to_id"] == b.id
    assert body["data"]["deleted"] is True


def test_unfollow_when_not_following_is_idempotent(client, make_user, auth_headers):
    a = make_user()
    b = make_user()
    resp = client.delete(f"/api/follows/{b.id}", headers=auth_headers(a))
    assert resp.status_code == 200
    _assert_contract(resp.get_json(), 200)
    assert resp.get_json()["data"]["deleted"] is True


def test_refollow_after_unfollow(client, make_user, auth_headers):
    a = make_user()
    b = make_user()
    headers = auth_headers(a)
    client.post("/api/follows", json={"to_id": b.id}, headers=headers)
    client.delete(f"/api/follows/{b.id}", headers=headers)
    # 重新关注恢复
    resp = client.post("/api/follows", json={"to_id": b.id}, headers=headers)
    assert resp.status_code == 201
    _assert_contract(resp.get_json(), 201)


# ---------- 列表 ----------
def test_following_list_carries_nickname(client, make_user, auth_headers):
    a = make_user(nick_name="关注者")
    b = make_user(nick_name="被关注者")
    headers = auth_headers(a)
    client.post("/api/follows", json={"to_id": b.id}, headers=headers)

    resp = client.get("/api/follows?type=following", headers=headers)
    assert resp.status_code == 200
    body = resp.get_json()
    _assert_contract(body, 200)
    items = body["data"]["items"]
    assert len(items) == 1
    assert items[0]["user_id"] == b.id
    assert items[0]["user"]["nick_name"] == "被关注者"


def test_fans_list_carries_nickname(client, make_user, auth_headers):
    a = make_user(nick_name="粉丝甲")
    b = make_user(nick_name="博主")
    client.post("/api/follows", json={"to_id": b.id}, headers=auth_headers(a))

    # b 看自己的粉丝列表（默认 user_id 为当前登录者）
    resp = client.get("/api/follows?type=fans", headers=auth_headers(b))
    assert resp.status_code == 200
    items = resp.get_json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["user_id"] == a.id
    assert items[0]["user"]["nick_name"] == "粉丝甲"


def test_fans_list_of_other_user_via_user_id(client, make_user, auth_headers):
    a = make_user(nick_name="粉A")
    b = make_user(nick_name="博主B")
    viewer = make_user()
    client.post("/api/follows", json={"to_id": b.id}, headers=auth_headers(a))

    # 第三方通过 user_id 查看 b 的粉丝
    resp = client.get(f"/api/follows?type=fans&user_id={b.id}",
                      headers=auth_headers(viewer))
    assert resp.status_code == 200
    items = resp.get_json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["user_id"] == a.id


def test_list_invalid_type_bad_request(client, make_user, auth_headers):
    a = make_user()
    resp = client.get("/api/follows?type=xxx", headers=auth_headers(a))
    assert resp.status_code == 400
    assert resp.get_json()["errno"] == 1
