from flask_restful import Resource
from flask import request, current_app, jsonify
from general.response import Response
from general.sql_map import SelectMap
from general.db_pool import fetchall_dict
from general.exception import UserDoesNotExistException
from utils.error_handler import init_key_error_handler
from apps.blog.api.blog import BlogTemplate


class BlogList(Resource):

    def get(self):
        response = Response()
        try:
            _id = request.args.get("id", 0)
            offset = current_app.config["PAGE_OFFSET"]
            blog_list = fetchall_dict(SelectMap.blog_list_by_id, (_id, offset), BlogTemplate)
            if blog_list:
                response.data = {
                    "blog_list": [blog.__dict__ for blog in blog_list],
                    "query_id": blog_list[-1].id, "last_query_id": _id, "page_offset": offset
                }
            else:
                raise UserDoesNotExistException("数据不存在")
        except Exception as e:
            init_key_error_handler(response, e, "信息:")
        return jsonify(response.dict_data)
