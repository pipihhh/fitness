"""interaction 域 e2e：评论/回复真实端点，断言契约。

覆盖：评论需帖子存在→404、删评论级联删回复、鉴权 401/403、
正文 XSS 清洗、回复仅本人删、评论列表内嵌 reply + 作者信息。
"""


def _assert_contract(body, expected_code):
    assert set(body.keys()) == {"errno", "code", "data"}
    assert body["errno"] == 0
    assert body["code"] == expected_code


def _create_blog(client, headers):
    return client.post("/api/blogs", json={"title": "t", "content": "c"},
                       headers=headers).get_json()["data"]


# ---------- 鉴权 ----------
def test_create_comment_requires_login(client):
    resp = client.post("/api/comments", json={"blog_id": 1, "content": "hi"})
    assert resp.status_code == 401


def test_create_reply_requires_login(client):
    resp = client.post("/api/replies", json={"comment_id": 1, "content": "hi"})
    assert resp.status_code == 401


# ---------- 评论 ----------
def test_create_comment_requires_blog(client, make_user, auth_headers):
    u = make_user()
    resp = client.post("/api/comments",
                       json={"blog_id": 999999, "content": "hi"},
                       headers=auth_headers(u))
    assert resp.status_code == 404
    assert resp.get_json()["errno"] == 1


def test_create_comment_success_and_sanitizes(client, make_user, auth_headers):
    author = make_user()
    commenter = make_user()
    blog = _create_blog(client, auth_headers(author))
    resp = client.post("/api/comments",
                       json={"blog_id": blog["id"],
                             "content": "<script>x</script>ok"},
                       headers=auth_headers(commenter))
    assert resp.status_code == 201
    body = resp.get_json()
    _assert_contract(body, 201)
    assert "<script>" not in body["data"]["content"]
    assert "ok" in body["data"]["content"]


def test_create_comment_validation_error(client, make_user, auth_headers):
    u = make_user()
    resp = client.post("/api/comments", json={"blog_id": 1}, headers=auth_headers(u))
    assert resp.status_code == 400


# ---------- 评论列表（公开，内嵌 reply + 作者）----------
def test_comment_list_nests_replies(client, make_user, auth_headers):
    author = make_user(nick_name="评论人")
    replier = make_user(nick_name="回复人")
    blog = _create_blog(client, auth_headers(author))
    comment = client.post("/api/comments",
                          json={"blog_id": blog["id"], "content": "c"},
                          headers=auth_headers(author)).get_json()["data"]
    client.post("/api/replies",
                json={"comment_id": comment["id"], "content": "r"},
                headers=auth_headers(replier))

    resp = client.get(f"/api/blogs/{blog['id']}/comments")  # 公开
    assert resp.status_code == 200
    body = resp.get_json()
    _assert_contract(body, 200)
    items = body["data"]["items"]
    assert len(items) == 1
    assert items[0]["author"]["nick_name"] == "评论人"
    assert len(items[0]["replies"]) == 1
    assert items[0]["replies"][0]["author"]["nick_name"] == "回复人"


# ---------- 删评论级联删回复 ----------
def test_delete_comment_cascades_replies(client, make_user, auth_headers):
    author = make_user()
    blog = _create_blog(client, auth_headers(author))
    comment = client.post("/api/comments",
                          json={"blog_id": blog["id"], "content": "c"},
                          headers=auth_headers(author)).get_json()["data"]
    client.post("/api/replies",
                json={"comment_id": comment["id"], "content": "r"},
                headers=auth_headers(author))

    resp = client.delete(f"/api/comments/{comment['id']}",
                         headers=auth_headers(author))
    assert resp.status_code == 200
    _assert_contract(resp.get_json(), 200)
    # 评论与其 reply 都不再出现
    listed = client.get(f"/api/blogs/{blog['id']}/comments").get_json()["data"]
    assert listed["items"] == []


def test_delete_comment_non_author_forbidden(client, make_user, auth_headers):
    author = make_user()
    other = make_user()
    blog = _create_blog(client, auth_headers(author))
    comment = client.post("/api/comments",
                          json={"blog_id": blog["id"], "content": "c"},
                          headers=auth_headers(author)).get_json()["data"]
    resp = client.delete(f"/api/comments/{comment['id']}",
                         headers=auth_headers(other))
    assert resp.status_code == 403


# ---------- 回复 ----------
def test_create_reply_requires_comment(client, make_user, auth_headers):
    u = make_user()
    resp = client.post("/api/replies",
                       json={"comment_id": 999999, "content": "r"},
                       headers=auth_headers(u))
    assert resp.status_code == 404


def test_delete_reply_only_self(client, make_user, auth_headers):
    author = make_user()
    other = make_user()
    blog = _create_blog(client, auth_headers(author))
    comment = client.post("/api/comments",
                          json={"blog_id": blog["id"], "content": "c"},
                          headers=auth_headers(author)).get_json()["data"]
    reply = client.post("/api/replies",
                        json={"comment_id": comment["id"], "content": "r"},
                        headers=auth_headers(author)).get_json()["data"]
    # 非本人删 -> 403
    bad = client.delete(f"/api/replies/{reply['id']}", headers=auth_headers(other))
    assert bad.status_code == 403
    # 本人删 -> 200
    good = client.delete(f"/api/replies/{reply['id']}", headers=auth_headers(author))
    assert good.status_code == 200
    _assert_contract(good.get_json(), 200)
