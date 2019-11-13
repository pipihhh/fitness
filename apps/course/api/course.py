import datetime
from flask import request, g, current_app, jsonify
from flask_restful import Resource, reqparse
from general.vaild import BaseValid
from general.response import Response
from general.db_pool import execute_sql, execute_query_sql
from general.sql_map import InsertMap, SelectMap, UpdateMap, DeleteMap
from general.exception import UserDoesNotExistException
from utils.error_handler import init_key_error_handler
from utils.idempotent_request import idempotent
from utils.post_template import post
from conf.code import FORMAT_ERROR
from conf.permission import permission_valid, ADMIN


parse = reqparse.RequestParser()
parse.add_argument("name", type=str, required=True)
parse.add_argument("type", type=int, required=True)
parse.add_argument("level", type=int, required=True)
parse.add_argument("burning", type=int, required=True)
parse.add_argument("id", type=int)


class Course(Resource):

    @idempotent
    @permission_valid(ADMIN)
    def post(self):
        valid = CourseValid(parse.parse_args())
        err_map = valid.valid_data()
        response = Response()
        if err_map:
            response.data = err_map
            response.errno = len(err_map)
            response.code = FORMAT_ERROR
            return jsonify(response.dict_data)
        try:
            data = valid.clean_data
            execute_sql(InsertMap.course, [
                data["type"], data["name"], datetime.datetime.now(),
                data["level"], data["burning"]
            ])
            ret = execute_query_sql(SelectMap.course_by_create, [data["name"], ], lambda c: c.fetchone())
            response.data = {
                "id": ret[0], "type": ret[1], "name": ret[2], "create_time": ret[3],
                "level": ret[4], "burning": ret[5]
            }
        except Exception as e:
            init_key_error_handler(response, e, "插入数据失败:")
        return jsonify(response.dict_data)

    @idempotent
    @permission_valid(ADMIN)
    def put(self):
        """
        修改课程的接口
        :return:
        """
        response = Response()
        try:
            _id = request.json["id"]
            course = CourseTemplate()
            response = post(CourseValid, parse, course)
            if response:
                return jsonify(response.dict_data)
            ret = execute_sql(UpdateMap.update_course_by_id, [
                course.name, course.type, course.level, course.burning,
                course.id
            ])
            if ret == 0:
                raise UserDoesNotExistException("课程不存在")
            response.data = {
                "id": course.id, "name": course.name, "type": course.type,
                "level": course.level, "burning": course.burning
            }
        except KeyError as e:
            init_key_error_handler(response, e, "缺少入参:")
        except UserDoesNotExistException as e:
            init_key_error_handler(response, e)
        return jsonify(response)

    @idempotent
    @permission_valid(ADMIN)
    def delete(self):
        """
        删除课程接口 但是并不会删除action
        :return:
        """
        response = Response()
        try:
            _id = request.json["id"]
            course_num = execute_sql(DeleteMap.course_by_id, [_id, ])
            response.data = {"msg": "ok", "count": course_num}
        except KeyError as e:
            init_key_error_handler(response, e)
        return jsonify(response.dict_data)


class CourseValid(BaseValid):
    pass


class CourseTemplate(object):
    def __init__(self):
        self.name = None
        self.type = None
        self.level = None
        self.burning = None
        self.id = None
