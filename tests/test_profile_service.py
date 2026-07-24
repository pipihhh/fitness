"""ProfileService 单测：跨域计数聚合、is_following、注册量按天统计。

跨域数据经各域 service 造（content/interaction/course/social），
验证 identity.ProfileService 聚合正确；注册统计验证按天分桶、空日期计 0、
跨度校验（修 CR #21 类"空即异常/布尔写反"）。
"""
from datetime import datetime, timedelta

import pytest

from ezgym.core.database import db
from ezgym.core.errors import BadRequest, NotFound
from ezgym.domains.content.service import ContentService
from ezgym.domains.course.service import CourseCollectionService, CourseService
from ezgym.domains.identity.service import ProfileService
from ezgym.domains.interaction.service import CommentService
from ezgym.domains.social.service import SocialService


# ---------------- profile 聚合 ----------------

def test_get_profile_aggregates_counts(app, make_user):
    owner = make_user(nick_name="Owner")
    other = make_user()

    # 2 篇动态
    blog1 = ContentService.create_blog(owner.id, "t1", "c1")
    ContentService.create_blog(owner.id, "t2", "c2")
    # 1 条评论
    CommentService.create_comment(owner.id, blog1.id, "nice")
    # 1 个收藏
    course = CourseService.create_course("瑜伽入门")
    CourseCollectionService.collect(owner.id, course.id)
    # owner 有 1 个粉丝(other 关注 owner)，owner 关注 0 人
    SocialService.follow(other.id, owner.id)

    profile = ProfileService.get_profile(owner.id, viewer_id=None)

    assert profile["user"]["id"] == owner.id
    assert profile["user"]["nick_name"] == "Owner"
    assert profile["blog_count"] == 2
    assert profile["fans_count"] == 1
    assert profile["following_count"] == 0
    assert profile["collection_count"] == 1
    assert profile["is_following"] is False  # viewer 未登录


def test_get_profile_is_following_true_and_false(app, make_user):
    owner = make_user()
    viewer = make_user()

    # viewer 未关注 owner
    assert ProfileService.get_profile(owner.id, viewer.id)["is_following"] is False

    SocialService.follow(viewer.id, owner.id)
    assert ProfileService.get_profile(owner.id, viewer.id)["is_following"] is True

    # 另一个未登录 viewer
    assert ProfileService.get_profile(owner.id, None)["is_following"] is False


def test_get_profile_missing_user_raises_not_found(app):
    with pytest.raises(NotFound):
        ProfileService.get_profile(999999, viewer_id=None)


# ---------------- 子资源列表委托 ----------------

def test_list_blogs_delegates_and_paginates(app, make_user):
    owner = make_user()
    for i in range(3):
        ContentService.create_blog(owner.id, f"t{i}", f"c{i}")

    page = ProfileService.list_blogs(owner.id, cursor=None, limit=2)
    assert page.count == 2
    assert page.next_cursor is not None
    page2 = ProfileService.list_blogs(owner.id, cursor=page.next_cursor, limit=2)
    assert page2.count == 1


# ---------------- 注册量按天统计 ----------------

def _set_created_at(user, dt: datetime):
    user.created_at = dt
    db.session.commit()


def test_registration_stats_buckets_by_day(app, make_user):
    # 2026-07-01 两个、2026-07-03 一个、2026-07-02 无
    _set_created_at(make_user(), datetime(2026, 7, 1, 8, 0))
    _set_created_at(make_user(), datetime(2026, 7, 1, 20, 0))
    _set_created_at(make_user(), datetime(2026, 7, 3, 9, 0))

    stats = ProfileService.registration_stats("2026-07-01", "2026-07-03")

    assert stats == [
        {"date": "2026-07-01", "count": 2},
        {"date": "2026-07-02", "count": 0},  # 无数据日期计 0（修 CR #21）
        {"date": "2026-07-03", "count": 1},
    ]


def test_registration_stats_empty_range_returns_zeros(app):
    """空结果正常返回全 0 的列表，而非报错（修 CR #21 类"空即异常"）。"""
    stats = ProfileService.registration_stats("2030-01-01", "2030-01-03")
    assert stats == [
        {"date": "2030-01-01", "count": 0},
        {"date": "2030-01-02", "count": 0},
        {"date": "2030-01-03", "count": 0},
    ]


def test_registration_stats_single_day(app, make_user):
    _set_created_at(make_user(), datetime(2026, 6, 15, 12, 0))
    stats = ProfileService.registration_stats("2026-06-15", "2026-06-15")
    assert stats == [{"date": "2026-06-15", "count": 1}]


def test_registration_stats_span_over_30_days_raises(app):
    start = "2026-01-01"
    end = (datetime(2026, 1, 1) + timedelta(days=31)).date().isoformat()
    with pytest.raises(BadRequest):
        ProfileService.registration_stats(start, end)


def test_registration_stats_span_exactly_30_days_ok(app):
    end = (datetime(2026, 1, 1) + timedelta(days=30)).date().isoformat()
    stats = ProfileService.registration_stats("2026-01-01", end)
    assert len(stats) == 31  # 含首尾共 31 天，跨度 30


def test_registration_stats_end_before_start_raises(app):
    with pytest.raises(BadRequest):
        ProfileService.registration_stats("2026-07-10", "2026-07-01")


def test_registration_stats_bad_format_raises(app):
    with pytest.raises(BadRequest):
        ProfileService.registration_stats("2026/07/01", "2026-07-03")


def test_registration_stats_missing_param_raises(app):
    with pytest.raises(BadRequest):
        ProfileService.registration_stats(None, "2026-07-03")


def test_registration_stats_includes_soft_deleted_users(app, make_user):
    """软删用户仍计入注册量（软删不改变'曾注册'的事实）。"""
    u = make_user()
    _set_created_at(u, datetime(2026, 5, 10, 10, 0))
    u.is_deleted = True
    db.session.commit()
    stats = ProfileService.registration_stats("2026-05-10", "2026-05-10")
    assert stats == [{"date": "2026-05-10", "count": 1}]
