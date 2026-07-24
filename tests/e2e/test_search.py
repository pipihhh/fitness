"""search 域 e2e：/api/search 真实端点，断言契约 + SQL 注入回归（#2）。"""


def _assert_contract(body, expected_code):
    assert set(body.keys()) == {"errno", "code", "data"}
    assert body["errno"] == 0
    assert body["code"] == expected_code


def _create_blog(client, headers, content):
    return client.post("/api/blogs", json={"title": "t", "content": content},
                       headers=headers).get_json()["data"]


def test_search_public_no_login(client, make_user, auth_headers):
    a = make_user()
    _create_blog(client, auth_headers(a), "apple pie recipe")
    resp = client.get("/api/search?type=blog&q=apple")  # 公开，无 token
    assert resp.status_code == 200
    body = resp.get_json()
    _assert_contract(body, 200)
    assert body["data"]["count"] == 1
    assert "apple" in body["data"]["items"][0]["content"]


def test_search_carries_author_info(client, make_user, auth_headers):
    a = make_user(nick_name="搜索作者")
    _create_blog(client, auth_headers(a), "banana bread")
    resp = client.get("/api/search?type=blog&q=banana")
    item = resp.get_json()["data"]["items"][0]
    assert item["author"]["nick_name"] == "搜索作者"


def test_search_sql_injection_returns_nothing(client, make_user, auth_headers):
    """#2 回归：注入 payload 不返回全表、不报错。"""
    a = make_user()
    _create_blog(client, auth_headers(a), "hello world")
    _create_blog(client, auth_headers(a), "another post")
    resp = client.get("/api/search", query_string={"type": "blog", "q": "' OR '1'='1"})
    assert resp.status_code == 200
    body = resp.get_json()
    _assert_contract(body, 200)
    # 注入未生效：payload 作为字面量匹配，无命中
    assert body["data"]["count"] == 0


def test_search_invalid_type(client):
    resp = client.get("/api/search?type=user&q=x")
    assert resp.status_code == 400
    assert resp.get_json()["errno"] == 1


def test_search_empty_query_returns_all(client, make_user, auth_headers):
    a = make_user()
    _create_blog(client, auth_headers(a), "one")
    _create_blog(client, auth_headers(a), "two")
    resp = client.get("/api/search?type=blog&q=")
    assert resp.status_code == 200
    assert resp.get_json()["data"]["count"] == 2
