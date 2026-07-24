"""content 域 e2e：打真实端点，断言 HTTP status + {errno, code, data} 契约。

覆盖：软登录列表三种 scope、点赞事务一致（#12 回归）、鉴权 401/403、
正文 XSS 清洗、删帖权限、响应契约。
"""


def _assert_contract(body, expected_code):
    assert set(body.keys()) == {"errno", "code", "data"}
    assert body["errno"] == 0
    assert body["code"] == expected_code


def _create_blog(client, headers, content="hello", title="t"):
    resp = client.post("/api/blogs",
                       json={"title": title, "content": content},
                       headers=headers)
    return resp


# ---------- 鉴权 ----------
def test_create_blog_requires_login(client):
    resp = client.post("/api/blogs", json={"title": "t", "content": "c"})
    assert resp.status_code == 401
    assert resp.get_json()["errno"] == 1


def test_like_requires_login(client, make_user):
    resp = client.post("/api/blogs/1/likes")
    assert resp.status_code == 401


# ---------- 新建 + 契约 + XSS ----------
def test_create_blog_success_and_sanitizes(client, make_user, auth_headers):
    u = make_user()
    resp = _create_blog(client, auth_headers(u), content="<script>evil</script>hi")
    assert resp.status_code == 201
    body = resp.get_json()
    _assert_contract(body, 201)
    assert "<script>" not in body["data"]["content"]
    assert "hi" in body["data"]["content"]


def test_create_blog_validation_error(client, make_user, auth_headers):
    u = make_user()
    resp = client.post("/api/blogs", json={"title": "t"}, headers=auth_headers(u))
    assert resp.status_code == 400
    assert resp.get_json()["errno"] == 1


# ---------- 单帖 ----------
def test_get_blog_public(client, make_user, auth_headers):
    u = make_user(nick_name="楼主")
    created = _create_blog(client, auth_headers(u)).get_json()["data"]
    resp = client.get(f"/api/blogs/{created['id']}")  # 公开，无 token
    assert resp.status_code == 200
    body = resp.get_json()
    _assert_contract(body, 200)
    assert body["data"]["author"]["nick_name"] == "楼主"
    assert body["data"]["comment_count"] == 0
    assert body["data"]["like_count"] == 0


def test_get_blog_not_found(client):
    resp = client.get("/api/blogs/999999")
    assert resp.status_code == 404


# ---------- 删除权限 ----------
def test_delete_blog_non_author_forbidden(client, make_user, auth_headers):
    author = make_user()
    other = make_user()
    created = _create_blog(client, auth_headers(author)).get_json()["data"]
    resp = client.delete(f"/api/blogs/{created['id']}", headers=auth_headers(other))
    assert resp.status_code == 403
    assert resp.get_json()["errno"] == 1


def test_delete_blog_author_ok(client, make_user, auth_headers):
    author = make_user()
    created = _create_blog(client, auth_headers(author)).get_json()["data"]
    resp = client.delete(f"/api/blogs/{created['id']}", headers=auth_headers(author))
    assert resp.status_code == 200
    _assert_contract(resp.get_json(), 200)


def test_delete_blog_admin_ok(client, make_user, auth_headers):
    author = make_user()
    admin = make_user(admin=True)
    created = _create_blog(client, auth_headers(author)).get_json()["data"]
    resp = client.delete(f"/api/blogs/{created['id']}", headers=auth_headers(admin))
    assert resp.status_code == 200


# ---------- 点赞事务一致（#12 回归）----------
def test_like_flow_transaction_consistency(client, make_user, auth_headers):
    author = make_user()
    liker = make_user()
    lh = auth_headers(liker)
    created = _create_blog(client, auth_headers(author)).get_json()["data"]
    bid = created["id"]

    r = client.post(f"/api/blogs/{bid}/likes", headers=lh)
    assert r.status_code == 201
    body = r.get_json()
    _assert_contract(body, 201)
    assert body["data"]["like_count"] == 1
    assert body["data"]["is_liked"] is True

    # 重复点赞幂等不叠加
    r2 = client.post(f"/api/blogs/{bid}/likes", headers=lh)
    detail = client.get(f"/api/blogs/{bid}").get_json()["data"]
    assert detail["like_count"] == 1

    # 取消赞 -1
    r3 = client.delete(f"/api/blogs/{bid}/likes", headers=lh)
    assert r3.status_code == 200
    assert r3.get_json()["data"]["like_count"] == 0
    assert r3.get_json()["data"]["is_liked"] is False


def test_is_liked_reflects_viewer(client, make_user, auth_headers):
    author = make_user()
    liker = make_user()
    created = _create_blog(client, auth_headers(author)).get_json()["data"]
    bid = created["id"]
    client.post(f"/api/blogs/{bid}/likes", headers=auth_headers(liker))
    # liker 登录看列表 is_liked True
    resp = client.get("/api/blogs", headers=auth_headers(liker))
    item = next(i for i in resp.get_json()["data"]["items"] if i["id"] == bid)
    assert item["is_liked"] is True


# ---------- 列表三种 scope ----------
def test_list_scope_latest_anonymous(client, make_user, auth_headers):
    a = make_user()
    _create_blog(client, auth_headers(a), content="a1")
    resp = client.get("/api/blogs")  # 软登录，匿名
    assert resp.status_code == 200
    body = resp.get_json()
    _assert_contract(body, 200)
    assert body["data"]["count"] >= 1
    # 匿名无 is_liked 字段（None 未附加）
    assert "is_liked" not in body["data"]["items"][0]


def test_list_scope_user(client, make_user, auth_headers):
    a = make_user()
    b = make_user()
    _create_blog(client, auth_headers(a), content="a1")
    _create_blog(client, auth_headers(b), content="b1")
    resp = client.get(f"/api/blogs?scope=user&user_id={a.id}")
    assert resp.status_code == 200
    items = resp.get_json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["user_id"] == a.id


def test_list_scope_user_missing_user_id(client, make_user, auth_headers):
    a = make_user()
    resp = client.get("/api/blogs?scope=user", headers=auth_headers(a))
    assert resp.status_code == 400


def test_list_scope_following(client, make_user, auth_headers):
    viewer = make_user()
    followed = make_user()
    stranger = make_user()
    vh = auth_headers(viewer)
    client.post("/api/follows", json={"to_id": followed.id}, headers=vh)
    _create_blog(client, auth_headers(followed), content="f1")
    _create_blog(client, auth_headers(stranger), content="s1")
    resp = client.get("/api/blogs?scope=following", headers=vh)
    assert resp.status_code == 200
    items = resp.get_json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["user_id"] == followed.id


def test_list_invalid_scope(client):
    resp = client.get("/api/blogs?scope=xxx")
    assert resp.status_code == 400
