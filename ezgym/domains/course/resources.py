"""course 域 HTTP 资源注册入口（flask-restful）。

resource 只做 解析→鉴权→调 service→ok；错误由 service raise、全局 handler 兜底。
"""
from flask import request
from flask_jwt_extended import verify_jwt_in_request
from flask_restful import Resource

from ezgym.core.response import ok
from ezgym.core.security import admin_required, current_user_id, login_required
from ezgym.domains.course.schemas import (
    ActionCreateSchema,
    ActionSchema,
    CollectionCreateSchema,
    CourseCreateSchema,
    CourseUpdateSchema,
)
from ezgym.domains.course.service import (
    CourseActionService,
    CourseCollectionService,
    CourseService,
)

__all__ = ["register"]

_action_schema = ActionSchema()


def _page_body(page):
    return {"items": page.items, "next_cursor": page.next_cursor, "count": page.count}


class CourseListResource(Resource):
    """/api/courses —— GET 软登录列表；POST ADMIN 建课。"""

    def get(self):
        verify_jwt_in_request(optional=True)
        user_id = current_user_id()
        cursor = request.args.get("cursor", type=int)
        limit = request.args.get("limit", type=int)
        page = CourseService.list_courses(cursor, limit, user_id)
        return ok(_page_body(page))

    @admin_required
    def post(self):
        data = CourseCreateSchema().load(request.get_json(silent=True) or {})
        course = CourseService.create_course(**data)
        return ok(CourseService.serialize(course), 201)


class CourseResource(Resource):
    """/api/courses/<id> —— GET login；PUT/DELETE ADMIN。"""

    @login_required
    def get(self, course_id):
        user_id = current_user_id()
        return ok(CourseService.get_course(course_id, user_id))

    @admin_required
    def put(self, course_id):
        data = CourseUpdateSchema().load(request.get_json(silent=True) or {})
        course = CourseService.update_course(course_id, **data)
        return ok(CourseService.serialize(course))

    @admin_required
    def delete(self, course_id):
        CourseService.delete_course(course_id)
        return ok({"id": course_id, "deleted": True})


class CourseActionListResource(Resource):
    """/api/courses/<id>/actions —— GET 公开；POST ADMIN。"""

    def get(self, course_id):
        return ok(CourseActionService.list_actions(course_id))

    @admin_required
    def post(self, course_id):
        data = ActionCreateSchema().load(request.get_json(silent=True) or {})
        action = CourseActionService.create_action(course_id, **data)
        return ok(_action_schema.dump(action), 201)


class ActionResource(Resource):
    """/api/actions/<id> —— DELETE ADMIN 软删，返回明确 data（修 CR #26）。"""

    @admin_required
    def delete(self, action_id):
        CourseActionService.delete_action(action_id)
        return ok({"id": action_id, "deleted": True})


class CollectionListResource(Resource):
    """/api/collections —— POST login 收藏。"""

    @login_required
    def post(self):
        data = CollectionCreateSchema().load(request.get_json(silent=True) or {})
        user_id = current_user_id()
        col = CourseCollectionService.collect(user_id, data["course_id"])
        return ok(
            {"id": col.id, "course_id": col.course_id, "user_id": col.user_id}, 201)


class CollectionResource(Resource):
    """/api/collections/<id> —— DELETE login 软删本人收藏。"""

    @login_required
    def delete(self, collection_id):
        user_id = current_user_id()
        CourseCollectionService.uncollect(collection_id, user_id)
        return ok({"id": collection_id, "deleted": True})


def register(api):
    """向 flask-restful Api 注册本域 Resource。"""
    api.add_resource(CourseListResource, "/api/courses")
    api.add_resource(CourseResource, "/api/courses/<int:course_id>")
    api.add_resource(CourseActionListResource, "/api/courses/<int:course_id>/actions")
    api.add_resource(ActionResource, "/api/actions/<int:action_id>")
    api.add_resource(CollectionListResource, "/api/collections")
    api.add_resource(CollectionResource, "/api/collections/<int:collection_id>")
