"""social 域 service 单测：关注/取消/恢复、唯一防重复、跨域函数。

直接调 SocialService 与模块级跨域函数，穿透到真实内存库。
"""
import pytest

from ezgym.core.errors import BadRequest, NotFound
from ezgym.domains.social import service as social_service
from ezgym.domains.social.models import Follow
from ezgym.domains.social.service import SocialService


# ---------- 关注 ----------
def test_follow_creates_relation(app, make_user):
    a = make_user()
    b = make_user()
    follow, created = SocialService.follow(a.id, b.id)
    assert created is True
    assert follow.from_user_id == a.id
    assert follow.to_user_id == b.id
    assert follow.is_deleted is False


def test_follow_self_raises_bad_request(app, make_user):
    a = make_user()
    with pytest.raises(BadRequest):
        SocialService.follow(a.id, a.id)


def test_follow_nonexistent_user_raises_not_found(app, make_user):
    a = make_user()
    with pytest.raises(NotFound):
        SocialService.follow(a.id, 999999)


def test_follow_is_idempotent(app, make_user):
    a = make_user()
    b = make_user()
    f1, c1 = SocialService.follow(a.id, b.id)
    f2, c2 = SocialService.follow(a.id, b.id)
    assert c1 is True
    assert c2 is False  # 幂等：第二次不新建
    assert f1.id == f2.id
    # 唯一：库里只有一条
    assert Follow.query.filter_by(from_user_id=a.id, to_user_id=b.id).count() == 1


# ---------- 取消 + 恢复 ----------
def test_unfollow_soft_deletes(app, make_user):
    a = make_user()
    b = make_user()
    SocialService.follow(a.id, b.id)
    removed = SocialService.unfollow(a.id, b.id)
    assert removed is not None
    assert removed.is_deleted is True
    assert SocialService.is_following(a.id, b.id) is False


def test_unfollow_when_not_following_is_idempotent(app, make_user):
    a = make_user()
    b = make_user()
    # 未关注时取消：幂等成功返回 None，不抛错
    assert SocialService.unfollow(a.id, b.id) is None


def test_refollow_restores_soft_deleted_row(app, make_user):
    a = make_user()
    b = make_user()
    f1, _ = SocialService.follow(a.id, b.id)
    SocialService.unfollow(a.id, b.id)
    f2, created = SocialService.follow(a.id, b.id)
    assert created is True  # 恢复算作 created
    assert f2.id == f1.id  # 复用同一行（恢复而非新建）
    assert f2.is_deleted is False
    assert Follow.query.filter_by(from_user_id=a.id, to_user_id=b.id).count() == 1


# ---------- 跨域函数 ----------
def test_list_following_ids(app, make_user):
    a = make_user()
    b = make_user()
    c = make_user()
    SocialService.follow(a.id, b.id)
    SocialService.follow(a.id, c.id)
    ids = social_service.list_following_ids(a.id)
    assert set(ids) == {b.id, c.id}
    # 取消后不再出现
    SocialService.unfollow(a.id, b.id)
    assert social_service.list_following_ids(a.id) == [c.id]


def test_counts(app, make_user):
    a = make_user()
    b = make_user()
    c = make_user()
    SocialService.follow(a.id, b.id)  # a -> b
    SocialService.follow(c.id, b.id)  # c -> b
    SocialService.follow(a.id, c.id)  # a -> c
    assert social_service.count_following(a.id) == 2
    assert social_service.count_fans(a.id) == 0
    assert social_service.count_fans(b.id) == 2
    assert social_service.count_following(b.id) == 0


def test_is_following(app, make_user):
    a = make_user()
    b = make_user()
    assert social_service.is_following(a.id, b.id) is False
    SocialService.follow(a.id, b.id)
    assert social_service.is_following(a.id, b.id) is True


def test_list_followers_and_following_carry_public_info(app, make_user):
    a = make_user(nick_name="甲")
    b = make_user(nick_name="乙")
    SocialService.follow(a.id, b.id)

    following = social_service.list_following(a.id, None, None)
    assert following.count == 1
    item = following.items[0]
    assert item["user_id"] == b.id
    assert item["user"]["nick_name"] == "乙"

    fans = social_service.list_followers(b.id, None, None)
    assert fans.count == 1
    fan = fans.items[0]
    assert fan["user_id"] == a.id
    assert fan["user"]["nick_name"] == "甲"
