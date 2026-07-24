"""course 域 service（业务逻辑 + 事务边界）。

三个 service 均继承 BaseService，查询走 base_query 过滤软删，写操作方法内 commit。
对外（供 profile wave B）暴露 count_collections_by_user / list_collections_by_user。
"""
from flask import current_app

from ezgym.core.database import db
from ezgym.core.errors import Conflict, Forbidden
from ezgym.core.pagination import Page, cursor_paginate
from ezgym.core.service import BaseService
from ezgym.domains.course.models import Course, CourseAction, CourseCollection
from ezgym.domains.course.schemas import ActionSchema, CourseSchema

__all__ = [
    "CourseService",
    "CourseActionService",
    "CourseCollectionService",
    "count_collections_by_user",
    "list_collections_by_user",
]

_course_schema = CourseSchema()
_action_schema = ActionSchema()


class CourseService(BaseService):
    """课程 CRUD + 列表展示（picture / is_collected）。"""

    model = Course

    # ---------- 展示辅助 ----------
    @staticmethod
    def _default_picture() -> str:
        base = current_app.config.get("MEDIA_URL", "/media/images")
        return f"{base}/default.jpg"

    @classmethod
    def _pictures_for(cls, course_ids: list[int]) -> dict[int, str]:
        """批量取每个课程首个（按 sequence）有图动作的 picture，避免 N+1。"""
        result: dict[int, str] = {}
        if not course_ids:
            return result
        actions = (
            CourseAction.query.filter(
                CourseAction.course_id.in_(course_ids),
                CourseAction.is_deleted.is_(False),
            )
            .order_by(CourseAction.course_id.asc(), CourseAction.sequence.asc())
            .all()
        )
        for a in actions:
            if a.course_id not in result and a.picture:
                result[a.course_id] = a.picture
        return result

    @classmethod
    def serialize(cls, course, picture=None, is_collected=None, collection_id=None) -> dict:
        """序列化单个课程；picture 缺省用默认图；登录场景带收藏信息。"""
        data = _course_schema.dump(course)
        data["picture"] = picture or cls._default_picture()
        if is_collected is not None:
            data["is_collected"] = is_collected
            data["collection_id"] = collection_id
        return data

    # ---------- 查询 ----------
    @classmethod
    def get_course(cls, course_id: int, user_id: int | None = None) -> dict:
        course = cls.get_or_404(course_id, "课程不存在")
        picture = cls._pictures_for([course_id]).get(course_id)
        if user_id:
            col = (
                CourseCollection.query.filter_by(
                    course_id=course_id, user_id=user_id, is_deleted=False
                ).first()
            )
            cid = col.id if col else None
            return cls.serialize(course, picture, is_collected=cid is not None, collection_id=cid)
        return cls.serialize(course, picture)

    @classmethod
    def list_courses(cls, cursor: int | None, limit: int | None,
                     user_id: int | None = None) -> Page:
        """游标分页课程列表。空结果正常返回（items=[], next_cursor=None）——修 CR #22。"""
        page = cursor_paginate(cls.base_query(), cursor, limit, cls.model.id)
        courses = page.items
        ids = [c.id for c in courses]
        pictures = cls._pictures_for(ids)
        col_map: dict[int, int] = {}
        if user_id and ids:
            cols = CourseCollection.query.filter(
                CourseCollection.course_id.in_(ids),
                CourseCollection.user_id == user_id,
                CourseCollection.is_deleted.is_(False),
            ).all()
            col_map = {c.course_id: c.id for c in cols}
        items = []
        for c in courses:
            picture = pictures.get(c.id)
            if user_id:
                cid = col_map.get(c.id)
                items.append(cls.serialize(
                    c, picture, is_collected=cid is not None, collection_id=cid))
            else:
                items.append(cls.serialize(c, picture))
        return Page(items=items, count=page.count, next_cursor=page.next_cursor)

    # ---------- 写入 ----------
    @classmethod
    def create_course(cls, name, type=None, level=None, burning=None):
        """建课。name 唯一冲突→Conflict；所有字段完整插入——修 CR #4。"""
        if cls.base_query().filter(cls.model.name == name).first():
            raise Conflict("课程名称已存在")
        return cls.create(name=name, type=type, level=level, burning=burning)

    @classmethod
    def update_course(cls, course_id: int, **fields):
        course = cls.get_or_404(course_id, "课程不存在")
        new_name = fields.get("name")
        if new_name and new_name != course.name:
            if cls.base_query().filter(cls.model.name == new_name).first():
                raise Conflict("课程名称已存在")
        return cls.update(course, **fields)

    @classmethod
    def delete_course(cls, course_id: int) -> None:
        course = cls.get_or_404(course_id, "课程不存在")
        cls.soft_delete(course)


class CourseActionService(BaseService):
    """课程动作 CRUD。"""

    model = CourseAction

    @classmethod
    def list_actions(cls, course_id: int) -> dict:
        """该课程所有动作（按 sequence）+ 课程信息。"""
        course = CourseService.get_or_404(course_id, "课程不存在")
        actions = (
            cls.base_query()
            .filter(cls.model.course_id == course_id)
            .order_by(cls.model.sequence.asc(), cls.model.id.asc())
            .all()
        )
        picture = CourseService._pictures_for([course_id]).get(course_id)
        return {
            "course": CourseService.serialize(course, picture),
            "actions": _action_schema.dump(actions, many=True),
        }

    @classmethod
    def create_action(cls, course_id: int, content=None, picture=None, sequence=None):
        """新增动作。同课程 sequence 不可重复→Conflict。"""
        CourseService.get_or_404(course_id, "课程不存在")
        if sequence is not None:
            dup = cls.base_query().filter(
                cls.model.course_id == course_id,
                cls.model.sequence == sequence,
            ).first()
            if dup:
                raise Conflict("该课程下 sequence 已存在")
        return cls.create(
            course_id=course_id, content=content, picture=picture, sequence=sequence)

    @classmethod
    def delete_action(cls, action_id: int):
        """软删动作（原表硬删，现统一软删）。返回被删对象供上层给出明确 data——修 CR #26。"""
        action = cls.get_or_404(action_id, "动作不存在")
        cls.soft_delete(action)
        return action


class CourseCollectionService(BaseService):
    """课程收藏。(user_id, course_id) 唯一，软删+恢复。"""

    model = CourseCollection

    @classmethod
    def collect(cls, user_id: int, course_id: int):
        """收藏课程：已软删记录则恢复，否则新建；已收藏则幂等返回。"""
        CourseService.get_or_404(course_id, "课程不存在")
        existing = cls.base_query(include_deleted=True).filter(
            cls.model.user_id == user_id,
            cls.model.course_id == course_id,
        ).first()
        if existing:
            if existing.is_deleted:
                existing.is_deleted = False
                db.session.commit()
            return existing
        return cls.create(user_id=user_id, course_id=course_id)

    @classmethod
    def uncollect(cls, collection_id: int, user_id: int):
        """软删本人收藏；非本人→Forbidden。"""
        col = cls.get_or_404(collection_id, "收藏不存在")
        if col.user_id != user_id:
            raise Forbidden("只能操作本人的收藏")
        cls.soft_delete(col)
        return col

    @classmethod
    def count_collections_by_user(cls, user_id: int) -> int:
        return cls.base_query().filter(cls.model.user_id == user_id).count()

    @classmethod
    def list_collections_by_user(cls, user_id: int, cursor: int | None,
                                 limit: int | None) -> Page:
        """本人收藏列表（游标分页），每项带 collection_id + 课程信息。"""
        page = cursor_paginate(
            cls.base_query().filter(cls.model.user_id == user_id),
            cursor, limit, cls.model.id,
        )
        cols = page.items
        course_ids = [c.course_id for c in cols]
        courses = {}
        if course_ids:
            for course in CourseService.base_query().filter(
                Course.id.in_(course_ids)
            ).all():
                courses[course.id] = course
        pictures = CourseService._pictures_for(course_ids)
        items = []
        for c in cols:
            course = courses.get(c.course_id)
            course_data = (
                CourseService.serialize(course, pictures.get(c.course_id))
                if course else None
            )
            items.append({
                "collection_id": c.id,
                "course_id": c.course_id,
                "course": course_data,
            })
        return Page(items=items, count=page.count, next_cursor=page.next_cursor)


# ---------- 跨域暴露（供 profile wave B 消费）----------
def count_collections_by_user(user_id: int) -> int:
    return CourseCollectionService.count_collections_by_user(user_id)


def list_collections_by_user(user_id: int, cursor: int | None, limit: int | None) -> Page:
    return CourseCollectionService.list_collections_by_user(user_id, cursor, limit)
