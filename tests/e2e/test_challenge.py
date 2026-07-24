"""challenge 域 e2e：公开列表/详情、GET 不改 pageviews(#20)、views 自增、鉴权、软删。

断言 HTTP 状态码 + body {errno, code, data} 契约。
"""
import pytest

from ezgym.domains.challenge.service import ChallengeService


@pytest.fixture()
def seed_challenge(app):
    def _seed(content="健身挑战内容超过十个字的正文用于截取标题"):
        return ChallengeService.create_challenge(
            content=content, start_time="2026-01-01", end_time="2026-01-07"
        )

    return _seed


def _assert_body(payload, http_status):
    assert payload["errno"] == 0
    assert payload["code"] == http_status
    assert "data" in payload


# ---------------- 公开读取 ----------------

def test_public_list(client, seed_challenge):
    seed_challenge()
    seed_challenge()
    resp = client.get("/api/challenges")
    assert resp.status_code == 200
    body = resp.get_json()
    _assert_body(body, 200)
    data = body["data"]
    assert data["count"] == 2
    assert len(data["items"]) == 2
    # 每项带截取的 title
    assert all("title" in item for item in data["items"])


def test_public_list_title_truncation(app, client, seed_challenge):
    length = app.config["TITLE_LENGTH"]
    content = "标" * (length + 8)
    seed_challenge(content=content)
    resp = client.get("/api/challenges")
    item = resp.get_json()["data"]["items"][0]
    assert item["title"] == content[:length]


def test_public_detail(client, seed_challenge):
    ch = seed_challenge()
    resp = client.get(f"/api/challenges/{ch.id}")
    assert resp.status_code == 200
    body = resp.get_json()
    _assert_body(body, 200)
    assert body["data"]["id"] == ch.id


def test_detail_missing_returns_404(client):
    resp = client.get("/api/challenges/999999")
    assert resp.status_code == 404
    assert resp.get_json()["errno"] == 1


# ---------------- CR #20 回归：GET 不改 pageviews ----------------

def test_get_detail_does_not_increment_pageviews(client, seed_challenge):
    ch = seed_challenge()
    assert ch.pageviews == 0
    client.get(f"/api/challenges/{ch.id}")
    client.get(f"/api/challenges/{ch.id}")
    resp = client.get(f"/api/challenges/{ch.id}")
    assert resp.get_json()["data"]["pageviews"] == 0


# ---------------- POST views 原子自增 ----------------

def test_post_views_increments(client, seed_challenge):
    ch = seed_challenge()
    r1 = client.post(f"/api/challenges/{ch.id}/views")
    assert r1.status_code == 200
    _assert_body(r1.get_json(), 200)
    assert r1.get_json()["data"]["pageviews"] == 1
    r2 = client.post(f"/api/challenges/{ch.id}/views")
    assert r2.get_json()["data"]["pageviews"] == 2


def test_post_views_missing_returns_404(client):
    resp = client.post("/api/challenges/999999/views")
    assert resp.status_code == 404


# ---------------- 写入鉴权 ----------------

def test_create_requires_auth(client):
    resp = client.post("/api/challenges", json={
        "content": "x", "start_time": "2026-01-01", "end_time": "2026-01-07",
    })
    assert resp.status_code == 401


def test_create_normal_user_forbidden(user_client):
    client, headers = user_client
    resp = client.post("/api/challenges", headers=headers, json={
        "content": "x", "start_time": "2026-01-01", "end_time": "2026-01-07",
    })
    assert resp.status_code == 403
    assert resp.get_json()["errno"] == 1


def test_create_admin_success(admin_client):
    client, headers = admin_client
    resp = client.post("/api/challenges", headers=headers, json={
        "picture": "/media/images/a.jpg",
        "content": "管理员创建的挑战",
        "start_time": "2026-01-01",
        "end_time": "2026-01-07",
    })
    assert resp.status_code == 201
    body = resp.get_json()
    _assert_body(body, 201)
    assert body["data"]["number"]
    assert body["data"]["content"] == "管理员创建的挑战"


def test_create_missing_field_returns_400(admin_client):
    client, headers = admin_client
    resp = client.post("/api/challenges", headers=headers, json={"content": "x"})
    assert resp.status_code == 400
    assert resp.get_json()["errno"] == 1


def test_update_admin(admin_client, seed_challenge):
    client, headers = admin_client
    ch = seed_challenge()
    resp = client.put(f"/api/challenges/{ch.id}", headers=headers, json={"content": "改后内容"})
    assert resp.status_code == 200
    assert resp.get_json()["data"]["content"] == "改后内容"


def test_update_normal_forbidden(user_client, seed_challenge):
    client, headers = user_client
    ch = seed_challenge()
    resp = client.put(f"/api/challenges/{ch.id}", headers=headers, json={"content": "x"})
    assert resp.status_code == 403


# ---------------- 软删 ----------------

def test_delete_admin_soft_delete(admin_client, seed_challenge):
    client, headers = admin_client
    ch = seed_challenge()
    resp = client.delete(f"/api/challenges/{ch.id}", headers=headers)
    assert resp.status_code == 200
    _assert_body(resp.get_json(), 200)
    # 软删后公开详情 404
    assert client.get(f"/api/challenges/{ch.id}").status_code == 404
    # 记录仍在库（软删非物理删）
    assert ChallengeService.get(ch.id, include_deleted=True) is not None


def test_delete_normal_forbidden(user_client, seed_challenge):
    client, headers = user_client
    ch = seed_challenge()
    resp = client.delete(f"/api/challenges/{ch.id}", headers=headers)
    assert resp.status_code == 403
