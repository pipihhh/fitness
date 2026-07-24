"""content 域 service 单测：帖子 CRUD、点赞事务一致（#12）、搜索参数化（#2）、
列表三种 scope、XSS 清洗、跨域函数。穿透真实内存库。
"""
import pytest

from ezgym.core.errors import BadRequest, Forbidden, NotFound
from ezgym.domains.content import service as content_service
from ezgym.core.database import db
from ezgym.domains.content.models import Blog, Like
from ezgym.domains.content.service import ContentService
from ezgym.domains.social.service import SocialService


# ---------- 新建 / 删除 ----------
def test_create_blog_sanitizes_content(app, make_user):
    u = make_user()
    blog = ContentService.create_blog(
        u.id, title="<b>hi</b>", content="<script>alert(1)</script>hello")
    # XSS：script 被转义，而不是原样保留
    assert "<script>" not in blog.content
    assert "&lt;script&gt;" in blog.content
    assert "hello" in blog.content


def test_delete_blog_author_soft_deletes(app, make_user):
    u = make_user()
    blog = ContentService.create_blog(u.id, title="t", content="c")
    ContentService.delete_blog(blog.id, u.id)
    assert db.session.get(Blog, blog.id).is_deleted is True


def test_delete_blog_non_author_forbidden(app, make_user):
    u = make_user()
    other = make_user()
    blog = ContentService.create_blog(u.id, title="t", content="c")
    with pytest.raises(Forbidden):
        ContentService.delete_blog(blog.id, other.id)


def test_delete_blog_admin_allowed(app, make_user):
    u = make_user()
    admin = make_user(admin=True)
    blog = ContentService.create_blog(u.id, title="t", content="c")
    ContentService.delete_blog(blog.id, admin.id, is_admin=True)
    assert db.session.get(Blog, blog.id).is_deleted is True


# ---------- 点赞事务一致（#12 回归）----------
def test_like_increments_count_and_creates_row(app, make_user):
    u = make_user()
    liker = make_user()
    blog = ContentService.create_blog(u.id, title="t", content="c")
    result = ContentService.like_blog(blog.id, liker.id)
    assert result["is_liked"] is True
    assert result["like_count"] == 1
    # like_count 与明细一致
    assert db.session.get(Blog, blog.id).like_count == 1
    assert Like.query.filter_by(
        blog_id=blog.id, user_id=liker.id, is_deleted=False).count() == 1


def test_like_is_idempotent_no_double_increment(app, make_user):
    u = make_user()
    liker = make_user()
    blog = ContentService.create_blog(u.id, title="t", content="c")
    ContentService.like_blog(blog.id, liker.id)
    ContentService.like_blog(blog.id, liker.id)  # 重复点赞
    assert db.session.get(Blog, blog.id).like_count == 1  # 不叠加
    assert Like.query.filter_by(
        blog_id=blog.id, user_id=liker.id, is_deleted=False).count() == 1


def test_unlike_decrements_not_below_zero(app, make_user):
    u = make_user()
    liker = make_user()
    blog = ContentService.create_blog(u.id, title="t", content="c")
    ContentService.like_blog(blog.id, liker.id)
    ContentService.unlike_blog(blog.id, liker.id)
    assert db.session.get(Blog, blog.id).like_count == 0
    # 明细软删
    assert Like.query.filter_by(
        blog_id=blog.id, user_id=liker.id, is_deleted=False).count() == 0
    # 再次取消不会减到负数
    ContentService.unlike_blog(blog.id, liker.id)
    assert db.session.get(Blog, blog.id).like_count == 0


def test_relike_restores_soft_deleted_row(app, make_user):
    u = make_user()
    liker = make_user()
    blog = ContentService.create_blog(u.id, title="t", content="c")
    r1 = ContentService.like_blog(blog.id, liker.id)
    ContentService.unlike_blog(blog.id, liker.id)
    r2 = ContentService.like_blog(blog.id, liker.id)
    assert r2["like_id"] == r1["like_id"]  # 复用同一行
    assert db.session.get(Blog, blog.id).like_count == 1
    assert Like.query.filter_by(blog_id=blog.id, user_id=liker.id).count() == 1


def test_like_nonexistent_blog_not_found(app, make_user):
    liker = make_user()
    with pytest.raises(NotFound):
        ContentService.like_blog(999999, liker.id)


# ---------- 列表三种 scope ----------
def test_list_scope_latest(app, make_user):
    a = make_user()
    b = make_user()
    ContentService.create_blog(a.id, title="t", content="a1")
    ContentService.create_blog(b.id, title="t", content="b1")
    page = ContentService.list_blogs("latest", None, None, None, None)
    assert page.count == 2


def test_list_scope_user(app, make_user):
    a = make_user()
    b = make_user()
    ContentService.create_blog(a.id, title="t", content="a1")
    ContentService.create_blog(b.id, title="t", content="b1")
    page = ContentService.list_blogs("user", a.id, None, None, None)
    assert page.count == 1
    assert page.items[0]["user_id"] == a.id


def test_list_scope_user_requires_user_id(app, make_user):
    with pytest.raises(BadRequest):
        ContentService.list_blogs("user", None, None, None, None)


def test_list_scope_following(app, make_user):
    viewer = make_user()
    followed = make_user()
    stranger = make_user()
    SocialService.follow(viewer.id, followed.id)
    ContentService.create_blog(followed.id, title="t", content="f1")
    ContentService.create_blog(stranger.id, title="t", content="s1")
    page = ContentService.list_blogs("following", None, viewer.id, None, None)
    assert page.count == 1
    assert page.items[0]["user_id"] == followed.id


def test_list_following_empty_when_anonymous(app, make_user):
    followed = make_user()
    ContentService.create_blog(followed.id, title="t", content="f1")
    page = ContentService.list_blogs("following", None, None, None, None)
    assert page.count == 0


def test_list_enriches_author_and_counts(app, make_user):
    a = make_user(nick_name="作者甲")
    liker = make_user()
    blog = ContentService.create_blog(a.id, title="t", content="c")
    ContentService.like_blog(blog.id, liker.id)
    page = ContentService.list_blogs("latest", None, liker.id, None, None)
    item = page.items[0]
    assert item["author"]["nick_name"] == "作者甲"
    assert item["like_count"] == 1
    assert item["is_liked"] is True
    assert item["comment_count"] == 0


# ---------- 搜索参数化（#2 回归）----------
def test_search_is_parameterized_no_injection(app, make_user):
    a = make_user()
    ContentService.create_blog(a.id, title="t", content="apple pie")
    ContentService.create_blog(a.id, title="t", content="banana split")
    # 注入 payload 不应返回全表、也不应报错
    page = content_service.search_blogs("' OR '1'='1", None, None)
    assert page.count == 0
    # 正常关键词命中
    hit = content_service.search_blogs("apple", None, None)
    assert hit.count == 1
    assert "apple" in hit.items[0]["content"]


# ---------- 跨域函数 ----------
def test_cross_domain_helpers(app, make_user):
    a = make_user()
    b = make_user()
    blog = ContentService.create_blog(a.id, title="t", content="c")
    assert content_service.blog_exists(blog.id) is True
    assert content_service.blog_exists(999999) is False
    assert content_service.get_blog(blog.id).id == blog.id
    assert content_service.count_blogs_by_user(a.id) == 1
    assert content_service.count_blogs_by_user(b.id) == 0
    page = content_service.list_blogs_by_user(a.id, None, None)
    assert page.count == 1


def test_list_blogs_liked_by_user(app, make_user):
    a = make_user()
    liker = make_user()
    blog1 = ContentService.create_blog(a.id, title="t", content="c1")
    ContentService.create_blog(a.id, title="t", content="c2")
    ContentService.like_blog(blog1.id, liker.id)
    page = content_service.list_blogs_liked_by_user(liker.id, None, None)
    assert page.count == 1
    assert page.items[0]["id"] == blog1.id
