"""search 域 HTTP 资源注册入口（flask-restful）。

resource 只做 解析→调 service→ok（修 CR #7）。搜索为公开端点。
"""
from flask import request
from flask_restful import Resource

from ezgym.core.response import ok
from ezgym.support.search.schemas import SearchQuerySchema
from ezgym.support.search.service import SearchService

__all__ = ["register"]


class SearchResource(Resource):
    """/api/search —— GET 公开，目前仅 type=blog。"""

    def get(self):
        args = SearchQuerySchema().load(request.args)
        page = SearchService.search_blogs(
            args["q"], args.get("cursor"), args.get("limit"))
        return ok({
            "items": page.items,
            "next_cursor": page.next_cursor,
            "count": page.count,
        })


def register(api):
    """向 flask-restful Api 注册本域 Resource。"""
    api.add_resource(SearchResource, "/api/search")
