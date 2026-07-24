"""course 域 service 单测。

覆盖：建课字段完整（修 CR #4）、name 冲突、sequence 重复冲突、收藏恢复逻辑、
空结果正常返回（修 CR #22）、picture 取值、is_collected 标记、跨域计数/列表。
"""
import pytest

from ezgym.core.errors import Conflict, Forbidden, NotFound
from ezgym.domains.course.service import (
    CourseActionService,
    CourseCollectionService,
    CourseService,
    count_collections_by_user,
    list_collections_by_user,
)


def test_create_course_persists_all_fields(app):
    """修 CR #4：建课后所有字段都正确落库并可回读。"""
    course = CourseService.create_course(
        name="燃脂初级", type="有氧", level="初级", burning=300)
    fetched = CourseService.get_or_404(course.id)
    assert fetched.name == "燃脂初级"
    assert fetched.type == "有氧"
    assert fetched.level == "初级"
    assert fetched.burning == 300
    assert fetched.is_deleted is False


def test_create_course_duplicate_name_conflict(app):
    CourseService.create_course(name="唯一课", type="力量", level="中级", burning=100)
    with pytest.raises(Conflict):
        CourseService.create_course(name="唯一课", type="有氧", level="初级", burning=50)


def test_action_sequence_conflict(app):
    course = CourseService.create_course(name="含动作课", type="有氧", level="初级", burning=1)
    CourseActionService.create_action(course.id, content="a", picture=None, sequence=1)
    with pytest.raises(Conflict):
        CourseActionService.create_action(course.id, content="b", picture=None, sequence=1)


def test_create_action_course_not_found(app):
    with pytest.raises(NotFound):
        CourseActionService.create_action(99999, content="x", picture=None, sequence=1)


def test_collect_restore_after_uncollect(app, make_user):
    user = make_user()
    course = CourseService.create_course(name="可收藏课", type="有氧", level="初级", burning=1)

    first = CourseCollectionService.collect(user.id, course.id)
    assert count_collections_by_user(user.id) == 1

    CourseCollectionService.uncollect(first.id, user.id)
    assert count_collections_by_user(user.id) == 0

    second = CourseCollectionService.collect(user.id, course.id)
    assert second.id == first.id  # 恢复同一条而非新建
    assert second.is_deleted is False
    assert count_collections_by_user(user.id) == 1


def test_collect_idempotent_when_active(app, make_user):
    user = make_user()
    course = CourseService.create_course(name="幂等课", type="有氧", level="初级", burning=1)
    a = CourseCollectionService.collect(user.id, course.id)
    b = CourseCollectionService.collect(user.id, course.id)
    assert a.id == b.id
    assert count_collections_by_user(user.id) == 1


def test_uncollect_forbidden_for_non_owner(app, make_user):
    owner = make_user()
    other = make_user()
    course = CourseService.create_course(name="他人课", type="有氧", level="初级", burning=1)
    col = CourseCollectionService.collect(owner.id, course.id)
    with pytest.raises(Forbidden):
        CourseCollectionService.uncollect(col.id, other.id)


def test_list_courses_empty_returns_normally(app):
    """修 CR #22：空列表是正常返回，不是异常。"""
    page = CourseService.list_courses(cursor=None, limit=None)
    assert page.items == []
    assert page.next_cursor is None
    assert page.count == 0


def test_list_courses_picture_default_and_first_action(app):
    with_pic = CourseService.create_course(name="有图课", type="有氧", level="初级", burning=1)
    CourseActionService.create_action(
        with_pic.id, content="a", picture="/media/images/x.jpg", sequence=1)
    no_pic = CourseService.create_course(name="无图课", type="有氧", level="初级", burning=1)

    page = CourseService.list_courses(cursor=None, limit=None)
    by_id = {item["id"]: item for item in page.items}
    assert by_id[with_pic.id]["picture"] == "/media/images/x.jpg"
    assert by_id[no_pic.id]["picture"] == "/media/images/default.jpg"


def test_list_courses_is_collected_flag(app, make_user):
    user = make_user()
    c1 = CourseService.create_course(name="已藏课", type="有氧", level="初级", burning=1)
    c2 = CourseService.create_course(name="未藏课", type="有氧", level="初级", burning=1)
    col = CourseCollectionService.collect(user.id, c1.id)

    # 匿名列表不带收藏字段
    anon = CourseService.list_courses(cursor=None, limit=None)
    assert "is_collected" not in anon.items[0]

    # 登录列表带收藏字段
    page = CourseService.list_courses(cursor=None, limit=None, user_id=user.id)
    by_id = {item["id"]: item for item in page.items}
    assert by_id[c1.id]["is_collected"] is True
    assert by_id[c1.id]["collection_id"] == col.id
    assert by_id[c2.id]["is_collected"] is False
    assert by_id[c2.id]["collection_id"] is None


def test_list_collections_by_user(app, make_user):
    user = make_user()
    c1 = CourseService.create_course(name="收藏A", type="有氧", level="初级", burning=1)
    c2 = CourseService.create_course(name="收藏B", type="有氧", level="初级", burning=1)
    CourseCollectionService.collect(user.id, c1.id)
    CourseCollectionService.collect(user.id, c2.id)

    page = list_collections_by_user(user.id, cursor=None, limit=None)
    assert page.count == 2
    course_ids = {item["course_id"] for item in page.items}
    assert course_ids == {c1.id, c2.id}
    assert all(item["course"] is not None for item in page.items)


def test_delete_course_hides_from_list(app):
    course = CourseService.create_course(name="待删课", type="有氧", level="初级", burning=1)
    CourseService.delete_course(course.id)
    page = CourseService.list_courses(cursor=None, limit=None)
    assert course.id not in {item["id"] for item in page.items}
    with pytest.raises(NotFound):
        CourseService.get_course(course.id)
