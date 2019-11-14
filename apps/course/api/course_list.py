from flask import current_app, jsonify, request
from flask_restful import Resource
from general.sql_map import SelectMap
from general.db_pool import execute_query_sql
from general.response import Response
from utils.error_handler import init_key_error_handler


class CourseList(Resource):

    def get(self):
        args = request.args
        course_id = args.get("id", 0)
        response = Response()
        offset = current_app.config["PAGE_OFFSET"]
        try:
            ret_list = execute_query_sql(SelectMap.course_list_by_page, [course_id, offset])
            ret_json = []
            for course in ret_list:
                ret_json.append({
                    "id": course[0], "type": course[1], "name": course[2], "create_time": course[3],
                    "level": course[4], "burning": course[5]
                })
            response.data = {
                "course_list": ret_json, "count": len(ret_json),
                "query_id": ret_list[-1][0],
                "last_query_id": course_id, "page_offset": offset
            }
            return jsonify(response.dict_data)
        except Exception as e:
            init_key_error_handler(response, e, "错误:")
            return jsonify(response.dict_data)
