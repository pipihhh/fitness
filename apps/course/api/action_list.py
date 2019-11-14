from flask_restful import Resource
from flask import request, jsonify
from apps.course.api.action import ActionTemplate
from apps.course.api.course import CourseTemplate
from general.sql_map import SelectMap
from general.db_pool import fetchall_dict, fetchone_dict
from general.response import Response
from general.exception import UserDoesNotExistException
from utils.error_handler import init_key_error_handler


class ActionList(Resource):
    def get(self):
        """
        根据course id获取对应的所有的action信息 没有分页
        :return:
        """
        response = Response()
        try:
            course_id = request.args["id"]
            action_list = fetchall_dict(SelectMap.action_by_course_id, (course_id, ), ActionTemplate)
            course = fetchone_dict(SelectMap.course_by_id, (course_id, ), CourseTemplate)
            if not action_list:
                raise UserDoesNotExistException("动作不存在")
            response.data = {
                "action_list": [action.__dict__ for action in action_list],
            }
            response.data.update(course.__dict__)
        except Exception as e:
            init_key_error_handler(response, e, "信息:")
        return jsonify(response.dict_data)
