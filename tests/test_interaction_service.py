"""interaction 域 service 单测：评论需帖子存在、级联删回复、回复校验、
XSS 清洗、跨域计数函数。穿透真实内存库。
"""
import pytest

from ezgym.core.database import db
from ezgym.core.errors import Forbidden, NotFound
from ezgym.domains.content.service import ContentService
from ezgym.domains.interaction import service as interaction_service
from ezgym.domains.interaction.models import Comment, Reply
from ezgym.domains.interaction.service import CommentService, ReplyService


def _blog(make_user):
    author = make_user()
    return ContentService.create_blog(author.id, title="t", content="c")


# ---------- 评论 ----------
def test_create_comment_requires_blog(app, make_user):
    u = make_user()
    with pytest.raises(NotFound):
        CommentService.create_comment(u.id, 999999, "hi")


def test_create_comment_sanitizes_content(app, make_user):
    u = make_user()
    blog = _blog(make_user)
    comment = CommentService.create_comment(
        u.id, blog.id, "<script>x</script>hi")
    assert "<script>" not in comment.content
    assert "&lt;script&gt;" in comment.content


def test_delete_comment_cascades_replies(app, make_user):
    author = make_user()
    blog = _blog(make_user)
    comment = CommentService.create_comment(author.id, blog.id, "c")
    r1 = ReplyService.create_reply(author.id, comment.id, "r1")
    r2 = ReplyService.create_reply(author.id, comment.id, "r2")
    CommentService.delete_comment(comment.id, author.id)
    assert db.session.get(Comment, comment.id).is_deleted is True
    assert db.session.get(Reply, r1.id).is_deleted is True
    assert db.session.get(Reply, r2.id).is_deleted is True


def test_delete_comment_non_author_forbidden(app, make_user):
    author = make_user()
    other = make_user()
    blog = _blog(make_user)
    comment = CommentService.create_comment(author.id, blog.id, "c")
    with pytest.raises(Forbidden):
        CommentService.delete_comment(comment.id, other.id)


def test_delete_comment_admin_allowed(app, make_user):
    author = make_user()
    admin = make_user(admin=True)
    blog = _blog(make_user)
    comment = CommentService.create_comment(author.id, blog.id, "c")
    CommentService.delete_comment(comment.id, admin.id, is_admin=True)
    assert db.session.get(Comment, comment.id).is_deleted is True


# ---------- 回复 ----------
def test_create_reply_requires_comment(app, make_user):
    u = make_user()
    with pytest.raises(NotFound):
        ReplyService.create_reply(u.id, 999999, "hi")


def test_create_reply_to_reply(app, make_user):
    author = make_user()
    blog = _blog(make_user)
    comment = CommentService.create_comment(author.id, blog.id, "c")
    r1 = ReplyService.create_reply(author.id, comment.id, "r1")
    r2 = ReplyService.create_reply(author.id, comment.id, "r2", reply_id=r1.id)
    assert r2.reply_id == r1.id


def test_delete_reply_only_self(app, make_user):
    author = make_user()
    other = make_user()
    blog = _blog(make_user)
    comment = CommentService.create_comment(author.id, blog.id, "c")
    reply = ReplyService.create_reply(author.id, comment.id, "r")
    with pytest.raises(Forbidden):
        ReplyService.delete_reply(reply.id, other.id)
    ReplyService.delete_reply(reply.id, author.id)
    assert db.session.get(Reply, reply.id).is_deleted is True


# ---------- 列表（内嵌 reply + 作者信息）----------
def test_list_for_blog_nests_replies_with_authors(app, make_user):
    author = make_user(nick_name="评论者")
    replier = make_user(nick_name="回复者")
    blog = _blog(make_user)
    comment = CommentService.create_comment(author.id, blog.id, "c")
    ReplyService.create_reply(replier.id, comment.id, "r")
    items = CommentService.list_for_blog(blog.id)
    assert len(items) == 1
    assert items[0]["author"]["nick_name"] == "评论者"
    assert len(items[0]["replies"]) == 1
    assert items[0]["replies"][0]["author"]["nick_name"] == "回复者"


def test_list_for_blog_excludes_soft_deleted(app, make_user):
    author = make_user()
    blog = _blog(make_user)
    c1 = CommentService.create_comment(author.id, blog.id, "c1")
    CommentService.create_comment(author.id, blog.id, "c2")
    CommentService.delete_comment(c1.id, author.id)
    items = CommentService.list_for_blog(blog.id)
    assert len(items) == 1


# ---------- 跨域计数函数 ----------
def test_count_comments_helpers(app, make_user):
    author = make_user()
    blog = _blog(make_user)
    blog2 = ContentService.create_blog(author.id, title="t", content="c2")
    CommentService.create_comment(author.id, blog.id, "c1")
    CommentService.create_comment(author.id, blog.id, "c2")
    CommentService.create_comment(author.id, blog2.id, "c3")

    assert interaction_service.count_comments_by_blog(blog.id) == 2
    counts = interaction_service.count_comments_by_blogs([blog.id, blog2.id])
    assert counts == {blog.id: 2, blog2.id: 1}
    assert interaction_service.count_comments_by_user(author.id) == 3
    page = interaction_service.list_comments_by_user(author.id, None, None)
    assert page.count == 3


def test_count_comments_by_blogs_empty(app):
    assert interaction_service.count_comments_by_blogs([]) == {}
