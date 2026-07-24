"""challenge 域 HTTP 资源注册入口（flask-restful）。

端点：
- GET  /api/challenges                     公开，游标分页（每项带截取 title）
- POST /api/challenges                     ADMIN，创建（number 自动生成）
- GET  /api/challenges/<id>                公开，详情（不改 pageviews，修 CR #20）
- PUT  /api/challenges/<id>                ADMIN，更新
- DELETE /api/challenges/<id>              ADMIN，软删
- POST /api/challenges/<id>/views          公开，原子自增 pageviews
"""
from flask import request
from flask_restful import Resource

from ezgym.core.response import ok
from ezgym.core.security import admin_required
from ezgym.domains.challenge.schemas import (
    ChallengeCreateSchema,
    ChallengeListItemSchema,
    ChallengeSchema,
    ChallengeUpdateSchema,
)
from ezgym.domains.challenge.service import ChallengeService

_detail_schema = ChallengeSchema()
_list_schema = ChallengeListItemSchema(many=True)
_create_schema = ChallengeCreateSchema()
_update_schema = ChallengeUpdateSchema()


class ChallengeListResource(Resource):
    def get(self):
        cursor = request.args.get("cursor", type=int)
        limit = request.args.get("limit", type=int)
        page = ChallengeService.list_challenges(cursor, limit)
        return ok(
            {
                "items": _list_schema.dump(page.items),
                "next_cursor": page.next_cursor,
                "count": page.count,
            }
        )

    @admin_required
    def post(self):
        payload = _create_schema.load(request.get_json(silent=True) or {})
        obj = ChallengeService.create_challenge(**payload)
        return ok(_detail_schema.dump(obj), 201)


class ChallengeResource(Resource):
    def get(self, challenge_id):
        # 修 CR #20：GET 详情不自增 pageviews
        obj = ChallengeService.get_or_404(challenge_id, "挑战不存在")
        return ok(_detail_schema.dump(obj))

    @admin_required
    def put(self, challenge_id):
        obj = ChallengeService.get_or_404(challenge_id, "挑战不存在")
        payload = _update_schema.load(request.get_json(silent=True) or {})
        obj = ChallengeService.update_challenge(obj, **payload)
        return ok(_detail_schema.dump(obj))

    @admin_required
    def delete(self, challenge_id):
        obj = ChallengeService.get_or_404(challenge_id, "挑战不存在")
        ChallengeService.soft_delete(obj)
        return ok({"id": challenge_id})


class ChallengeViewsResource(Resource):
    def post(self, challenge_id):
        views = ChallengeService.increment_pageviews(challenge_id)
        return ok({"id": challenge_id, "pageviews": views})


def register(api):
    api.add_resource(ChallengeListResource, "/api/challenges")
    api.add_resource(ChallengeResource, "/api/challenges/<int:challenge_id>")
    api.add_resource(ChallengeViewsResource, "/api/challenges/<int:challenge_id>/views")
