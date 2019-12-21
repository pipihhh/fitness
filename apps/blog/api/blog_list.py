from flask_restful import Resource
from flask import request, current_app, jsonify
from apps.user.api.user_list import UserListValid
from apps.search.api.searcher import _lt
from general.response import Response
from general.sql_map import SelectMap
from general.db_pool import fetchall_dict
from general.exception import UserDoesNotExistException, InvalidArgumentException
from utils.post_template import post
from utils.general_object import GeneralObject, create_cmp_with_class
from utils.error_handler import init_key_error_handler
from apps.blog.api.blog import BlogTemplate


class BlogList(Resource):

    def get(self):
        response = Response()
        try:
            tag = request.args.get("tag", "back")
            func = getattr(self, f"_{tag}_list")
            func(response)
        except Exception as e:
            init_key_error_handler(response, e, "信息:")
            import traceback
            traceback.print_exc()
        return jsonify(response.dict_data)

    def _back_list(self, response):
        _id = request.args.get("id", 0)
        offset = request.args.get("offset", current_app.config["PAGE_OFFSET"])
        offset = int(offset)
        blog_list = fetchall_dict(SelectMap.blog_list_by_id, (_id, offset), BlogTemplate)
        if blog_list:
            response.data = {
                "blog_list": [blog.__dict__ for blog in blog_list],
                "query_id": blog_list[-1].id, "last_query_id": _id, "page_offset": offset,
                "count": len(blog_list)
            }
        else:
            raise UserDoesNotExistException("数据不存在")

    def _user_list(self, response):
        req = GeneralObject()
        resp = post(UserListValid, request.args, req)
        if resp is not None:
            response = resp
            return
        blog_id = getattr(resp, "blog_id", 0)
        offset = req.offset
        page = req.page
        blog_list = fetchall_dict(SelectMap.blog_list_by_user, (req.id, blog_id, (page - 1) * offset + 1, offset),
                                  create_cmp_with_class(_lt))
        if blog_list:
            blog_list.sort()
            response.data = {
                "blog_list": [blog.data for blog in blog_list],
                "count": len(blog_list), "page": page,
            }
        else:
            raise UserDoesNotExistException("数据不存在")

    def _comment_list(self, resp):
        user_id = request.args.get("id") or request.user["id"]
        blog_list = fetchall_dict(SelectMap.blog_list_comment, (user_id, user_id), GeneralObject)
        if not blog_list:
            raise UserDoesNotExistException("数据不存在")
        resp.data = {
            "blog_list": [blog.data for blog in blog_list],
            "count": len(blog_list)
        }

    def _upper_list(self, resp):
        user_id = request.args.get("id") or request.user["id"]
        blog_list = fetchall_dict(SelectMap.blog_list_upper, (user_id, user_id), GeneralObject)
        if not blog_list:
            raise UserDoesNotExistException("数据不存在")
        resp.data = {
            "blog_list": [blog.data for blog in blog_list],
            "count": len(blog_list)
        }


class BlogListValid(UserListValid):
    def _page_valid(self, page):
        if page < 0:
            raise InvalidArgumentException("page小于1")
