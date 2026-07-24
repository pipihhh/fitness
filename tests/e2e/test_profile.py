"""profile / 子资源 / 注册统计 e2e：真实 client 打端点，断言 HTTP + {errno,code,data}。

覆盖：
- GET /api/users/{id}/profile 软登录：各计数、is_following（登录/未登录）、用户不存在 404。
- 子资源 blogs/comments/collections/followers/following 分页。
- GET /api/stats/registrations ADMIN 鉴权（NORMAL→403）、跨度超限→400、正常按天返回。
"""
from datetime import datetime

from ezgym.core.database import db
from ezgym.domains.content.service import ContentService
from ezgym.domains.course.service import CourseCollectionService, CourseService
from ezgym.domains.interaction.service import CommentService
from ezgym.domains.social.service import SocialService


def _assert_body(payload, http_status):
    assert payload["errno"] == 0
    assert payload["code"] == http_status
    assert "data" in payload


# ---------------- profile 聚合 ----------------

def test_profile_aggregates(client, make_user):
    owner = make_user(nick_name="Owner")
    other = make_user()
    b = ContentService.create_blog(owner.id, "t", "c")
    ContentService.create_blog(owner.id, "t2", "c2")
    CommentService.create_comment(owner.id, b.id, "hi")
    course = CourseService.create_course("普拉提")
    CourseCollectionService.collect(owner.id, course.id)
    SocialService.follow(other.id, owner.id)

    resp = client.get(f"/api/users/{owner.id}/profile")
    assert resp.status_code == 200
    body = resp.get_json()
    _assert_body(body, 200)
    data = body["data"]
    assert data["user"]["nick_name"] == "Owner"
    assert data["blog_count"] == 2
    assert data["fans_count"] == 1
    assert data["following_count"] == 0
    assert data["collection_count"] == 1
    assert data["is_following"] is False  # 未登录


def test_profile_is_following_when_logged_in(client, make_user, auth_headers):
    owner = make_user()
    viewer = make_user()
    SocialService.follow(viewer.id, owner.id)

    resp = client.get(
        f"/api/users/{owner.id}/profile", headers=auth_headers(viewer)
    )
    assert resp.status_code == 200
    assert resp.get_json()["data"]["is_following"] is True


def test_profile_soft_login_no_token_ok(client, make_user):
    owner = make_user()
    resp = client.get(f"/api/users/{owner.id}/profile")
    assert resp.status_code == 200
    assert resp.get_json()["data"]["is_following"] is False


def test_profile_missing_user_404(client):
    resp = client.get("/api/users/999999/profile")
    assert resp.status_code == 404
    assert resp.get_json()["errno"] == 1


# ---------------- 子资源分页 ----------------

def test_profile_blogs_pagination(client, make_user):
    owner = make_user()
    for i in range(3):
        ContentService.create_blog(owner.id, f"t{i}", f"c{i}")

    resp = client.get(f"/api/users/{owner.id}/blogs?limit=2")
    assert resp.status_code == 200
    body = resp.get_json()
    _assert_body(body, 200)
    assert body["data"]["count"] == 2
    assert body["data"]["next_cursor"] is not None

    cursor = body["data"]["next_cursor"]
    resp2 = client.get(f"/api/users/{owner.id}/blogs?limit=2&cursor={cursor}")
    assert resp2.get_json()["data"]["count"] == 1


def test_profile_comments_list(client, make_user):
    owner = make_user()
    b = ContentService.create_blog(owner.id, "t", "c")
    CommentService.create_comment(owner.id, b.id, "hello")
    resp = client.get(f"/api/users/{owner.id}/comments")
    assert resp.status_code == 200
    assert resp.get_json()["data"]["count"] == 1


def test_profile_collections_list(client, make_user):
    owner = make_user()
    course = CourseService.create_course("有氧课")
    CourseCollectionService.collect(owner.id, course.id)
    resp = client.get(f"/api/users/{owner.id}/collections")
    assert resp.status_code == 200
    assert resp.get_json()["data"]["count"] == 1


def test_profile_followers_and_following(client, make_user):
    owner = make_user()
    fan = make_user()
    idol = make_user()
    SocialService.follow(fan.id, owner.id)   # owner 有 1 粉丝
    SocialService.follow(owner.id, idol.id)  # owner 关注 1 人

    followers = client.get(f"/api/users/{owner.id}/followers")
    assert followers.status_code == 200
    assert followers.get_json()["data"]["count"] == 1

    following = client.get(f"/api/users/{owner.id}/following")
    assert following.status_code == 200
    assert following.get_json()["data"]["count"] == 1


def test_profile_subresource_empty_ok(client, make_user):
    """无数据的子资源正常返回空列表，而非报错。"""
    owner = make_user()
    resp = client.get(f"/api/users/{owner.id}/blogs")
    assert resp.status_code == 200
    body = resp.get_json()
    _assert_body(body, 200)
    assert body["data"]["items"] == []
    assert body["data"]["count"] == 0


# ---------------- 注册统计（ADMIN）----------------

def _set_created_at(user, dt):
    user.created_at = dt
    db.session.commit()


def test_registration_stats_requires_login_401(client):
    resp = client.get("/api/stats/registrations?start=2026-07-01&end=2026-07-03")
    assert resp.status_code == 401


def test_registration_stats_normal_forbidden_403(client, make_user, auth_headers):
    user = make_user()
    resp = client.get(
        "/api/stats/registrations?start=2026-07-01&end=2026-07-03",
        headers=auth_headers(user),
    )
    assert resp.status_code == 403


def test_registration_stats_admin_ok(client, make_user, admin_headers):
    u1 = make_user()
    u2 = make_user()
    _set_created_at(u1, datetime(2026, 7, 1, 8, 0))
    _set_created_at(u2, datetime(2026, 7, 1, 9, 0))

    resp = client.get(
        "/api/stats/registrations?start=2026-07-01&end=2026-07-02",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    body = resp.get_json()
    _assert_body(body, 200)
    data = body["data"]
    assert data[0] == {"date": "2026-07-01", "count": 2}
    assert data[1] == {"date": "2026-07-02", "count": 0}  # 无数据计 0（修 CR #21）


def test_registration_stats_empty_returns_zeros(client, admin_headers):
    """空结果正常返回，不报错（修 CR #21）。"""
    resp = client.get(
        "/api/stats/registrations?start=2030-01-01&end=2030-01-02",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data == [
        {"date": "2030-01-01", "count": 0},
        {"date": "2030-01-02", "count": 0},
    ]


def test_registration_stats_span_over_30_days_400(client, admin_headers):
    resp = client.get(
        "/api/stats/registrations?start=2026-01-01&end=2026-03-01",
        headers=admin_headers,
    )
    assert resp.status_code == 400
    assert resp.get_json()["code"] == 400


def test_registration_stats_bad_date_400(client, admin_headers):
    resp = client.get(
        "/api/stats/registrations?start=2026/01/01&end=2026-01-03",
        headers=admin_headers,
    )
    assert resp.status_code == 400


def test_registration_stats_missing_param_400(client, admin_headers):
    resp = client.get("/api/stats/registrations?start=2026-01-01", headers=admin_headers)
    assert resp.status_code == 400
