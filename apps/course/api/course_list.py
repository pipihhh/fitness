from flask import current_app, jsonify, request
from flask_restful import Resource
from general.sql_map import SelectMap
from general.db_pool import fetchall_dict, fetchone_dict
from general.response import Response
from utils.error_handler import init_key_error_handler
from utils.general_object import GeneralObject


class CourseList(Resource):

    def get(self):
        args = request.args
        course_id = args.get("id", 0)
        response = Response()
        offset = request.args.get("offset", current_app.config["PAGE_OFFSET"])
        offset = int(offset)
        try:
            user_id = getattr(request, "user", {}).get("id")
            ret_list = fetchall_dict(SelectMap.course_list_by_page, (course_id, offset), GeneralObject)
            ret_json = []
            if user_id:
                for course in ret_list:
                    collect = fetchone_dict(SelectMap.collect_by_course_id, (course.id, user_id),
                                            GeneralObject)
                    course.is_collect = True if collect else False
                    course.collect_id = collect.id if collect else None
                    ret_json.append(course.data)
            else:
                for course in ret_list:
                    course.is_collect = False
                    course.collect_id = None
                    ret_json.append(course.data)
            response.data = {
                "course_list": ret_json, "count": len(ret_json),
                "query_id": ret_list[-1].id,
                "last_query_id": course_id, "page_offset": offset
            }
            return jsonify(response.dict_data)
        except Exception as e:
            init_key_error_handler(response, e, "错误:")
            return jsonify(response.dict_data)
