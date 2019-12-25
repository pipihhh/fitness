import os
from flask import current_app, jsonify, request
from flask_restful import Resource
from conf.default import DefaultConfig
from general.sql_map import SelectMap
from general.db_pool import fetchall_dict, fetchone_dict
from general.response import Response
from utils.error_handler import init_key_error_handler
from utils.general_object import GeneralObject


class CourseList(Resource):
    default_url = os.path.join(DefaultConfig.MEDIA_URL, "default_course.jpg")

    def get(self):
        args = request.args
        course_id = args.get("id", 0)
        response = Response()
        offset = request.args.get("offset") or current_app.config["PAGE_OFFSET"]
        offset = int(offset)
        try:
            ret_list = fetchall_dict(SelectMap.course_list_by_page, (course_id, offset), GeneralObject)
            ret_json = []
            self._set_collected(ret_list, ret_json)
            response.data = {
                "course_list": ret_json, "count": len(ret_json),
                "query_id": ret_list[-1].id,
                "last_query_id": course_id, "page_offset": offset
            }
            return jsonify(response.dict_data)
        except Exception as e:
            init_key_error_handler(response, e, "错误:")
            return jsonify(response.dict_data)

    def _set_collected(self, course_list, buffer):
        user_id = getattr(request, "user", {}).get("id")
        if user_id:
            for course in course_list:
                collect = fetchone_dict(SelectMap.collect_by_course_id, (course.id, user_id),
                                        GeneralObject)
                course.is_collect = True if collect else False
                course.collect_id = collect.id if collect else None
                # action = fetchone_dict(SelectMap.action_list_by_course_id, (course.id,), GeneralObject)
                # course.picture = action.picture if action else default_url
                self._set_picture(course)
                buffer.append(course.data)
        else:
            for course in course_list:
                course.is_collect = False
                course.collect_id = None
                self._set_picture(course)
                buffer.append(course.data)

    def _set_picture(self, course):
        action = fetchone_dict(SelectMap.action_list_by_course_id, (course.id, ), GeneralObject)
        if action is None:
            course.picture = self.default_url
        else:
            course.picture = action.picture
