import datetime
from flask import request, jsonify
from flask_restful import Resource, reqparse
from conf.permission import permission_valid, NORMAL
from general.vaild import BaseValid
from general.sql_map import SelectMap, InsertMap, UpdateMap, DeleteMap
from general.db_pool import fetchone_dict, execute_sql
from general.exception import InvalidArgumentException
from general.response import Response
from utils.error_handler import init_key_error_handler
from utils.idempotent_request import idempotent
from utils.general_object import GeneralObject
from utils.post_template import post
from conf.code import FORMAT_ERROR
from apps.blog.api.blog import BlogTemplate

parse = reqparse.RequestParser()
parse.add_argument("blog_id", type=int, required=True)


class Upper(Resource):

    @idempotent
    @permission_valid(NORMAL)
    def post(self):
        insert_upper = UpperTemplate()
        response = post(UpperValid, parse, insert_upper)
        if response:
            return jsonify(response.dict_data)
        try:
            user_id = getattr(request, "user")["id"]
            old_upper = fetchone_dict(SelectMap.upper_without_delete_flag, (insert_upper.blog_id, user_id),
                                      UpperTemplate)
            if old_upper is not None:
                response = self._rollback(old_upper)
            else:
                response = self._real_insert(insert_upper)
            execute_sql(UpdateMap.update_blog_upper_by_id, (insert_upper.blog_id, ))
        except Exception as e:
            init_key_error_handler(response, e, "信息:")
        return jsonify(response.dict_data)

    def _real_insert(self, upper):
        response = Response()
        now = datetime.datetime.now()
        user_id = getattr(request, "user")["id"]
        ret = execute_sql(InsertMap.upper, (upper.blog_id, user_id, now), True)
        if ret == 0:
            response.code = FORMAT_ERROR
            response.errno = 1
            response.data = {"msg": "点赞失败"}
            return response
        response.data = {
            "id": ret, "user_id": upper.user_id, "blog_id": upper.blog_id,
            "create_time": now
        }
        return response

    def _rollback(self, upper):
        response = Response()
        user_id = getattr(request, "user")["id"]
        ret = execute_sql(UpdateMap.update_upper_by_user_and_blog, (upper.blog_id, user_id))
        if ret == 0:
            response.code = FORMAT_ERROR
            response.errno = 1
            response.data = {"msg": "点赞失败"}
            return response
        response.data = {
            "user_id": upper.user_id, "blog_id": upper.blog_id,
            "create_time": upper.create_time
        }
        return response

    @idempotent
    @permission_valid(NORMAL)
    def delete(self):
        upper = UpperTemplate()
        response = post(UpperValid, parse, upper)
        if response:
            return jsonify(response)
        try:
            user_id = getattr(request, "user")["id"]
            response = Response()
            ret = execute_sql(DeleteMap.upper_by_id, (upper.blog_id, user_id))
            if ret == 0:
                raise InvalidArgumentException("取消失败")
            execute_sql(UpdateMap.blog_upper_dev, (upper.blog_id, ))
            response.data = {
                "msg": "ok"
            }
        except Exception as e:
            init_key_error_handler(response, e, "信息:")
        return jsonify(response.dict_data)


class UpperValid(BaseValid):
    def blog_id_valid(self, blog_id):
        blog = fetchone_dict(SelectMap.blog_by_id, (blog_id,), BlogTemplate)
        if blog is None:
            raise InvalidArgumentException("博客不存在")
        user_id = getattr(request, "user")["id"]
        upper = fetchone_dict(SelectMap.upper_by_user_and_blog, (blog_id, user_id), GeneralObject)
        if (upper is None and request.method == "POST") or request.method == "DELETE":
            return
        raise InvalidArgumentException("已经点赞过了;数据不存在")


class UpperTemplate(object):
    def __init__(self):
        self.user_id = None
        self.blog_id = None
