import os
from flask import request, g, current_app, jsonify
from flask_restful import Resource, reqparse
from general.vaild import BaseValid
from general.exception import InvalidArgumentException
from general.response import Response
from general.db_pool import execute_sql, execute_query_sql
from general.sql_map import InsertMap, SelectMap
from utils.error_handler import init_key_error_handler
from utils.post_template import post
from conf.permission import permission_valid, ADMIN


parse = reqparse.RequestParser()
parse.add_argument("id", type=int, required=True)
parse.add_argument("content", type=str, required=True)
parse.add_argument("picture", type=str)
parse.add_argument("sequence", type=int, required=True)


class Action(Resource):

    @permission_valid(ADMIN)
    def post(self):
        """
        此方法用来添加一个对应课程的动作 但是此方法不会校验sequence(动作编号)，所以请谨慎调用
        :return:
        """
        template = ActionTemplate()
        ret = post(ActionValid, parse, template)
        response = Response()
        if ret:
            return jsonify(ret.dict_data)
        try:
            count = execute_sql(InsertMap.action, [
                template.id, template.content, template.picture, template.sequence
            ])
            response.data = {
                "course_id": template.id, "content": template.content,
                "picture": template.picture, "sequence": template.sequence,
                "count": count
            }
        except Exception as e:
            init_key_error_handler(response, e)
        return jsonify(response.dict_data)


class ActionValid(BaseValid):
    def picture_valid(self, picture):
        media_dir = current_app.config["MEDIA_DIR"]
        media_dir = os.path.join(media_dir, "action")
        file_dir = os.path.join(media_dir, picture)
        if os.path.isfile(file_dir):
            return
        raise InvalidArgumentException("图片不存在!请先上传")

    def id_valid(self, _id):
        ret = execute_query_sql(SelectMap.course_by_create, [_id, ], lambda c: c.fetchone())
        if ret == ():
            raise InvalidArgumentException("课程不存在")


class ActionTemplate(object):
    def __init__(self):
        self.id = None
        self.content = None
        self.picture = None
        self.sequence = None
