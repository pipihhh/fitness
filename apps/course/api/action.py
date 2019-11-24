import os
from flask import current_app, jsonify, request
from flask_restful import Resource, reqparse
from general.vaild import BaseValid
from general.exception import InvalidArgumentException
from general.response import Response
from general.db_pool import execute_sql, execute_query_sql
from general.sql_map import InsertMap, SelectMap, DeleteMap
from general.exception import UserDoesNotExistException
from utils.error_handler import init_key_error_handler
from utils.post_template import post
from utils.idempotent_request import idempotent
from conf.permission import permission_valid, ADMIN


parse = reqparse.RequestParser()
parse.add_argument("id", type=int, required=True)   # 课程的id
parse.add_argument("content", type=str, required=True)  # 动作的内容
parse.add_argument("picture", type=str)   # 图片的文件名
parse.add_argument("sequence", type=int, required=True)   # 动作的排序权重 从小到大排


class Action(Resource):

    @idempotent
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

    @permission_valid(ADMIN)
    def delete(self):
        response = Response()
        try:
            _id = request.json["id"]
            ret = execute_sql(DeleteMap.action_by_id, (_id, ))
            if ret == 0:
                raise UserDoesNotExistException("动作不存在")
        except Exception as e:
            init_key_error_handler(response, e, "信息:")
        return jsonify(response.dict_data)


class ActionValid(BaseValid):
    def picture_valid(self, picture):
        media_dir = current_app.config["MEDIA_DIR"]
        file_dir = os.path.join(media_dir, picture)
        if os.path.isfile(file_dir):
            setattr(self, picture, os.path.join(current_app.config["MEDIA_URL"], picture))
            return
        raise InvalidArgumentException("图片不存在!请先上传")

    def id_valid(self, _id):
        ret = execute_query_sql(SelectMap.course_by_id, [_id, ], lambda c: c.fetchone())
        if ret == ():
            raise InvalidArgumentException("课程不存在")

    def sequence_valid(self, sequence):
        ret = execute_query_sql(SelectMap.action_by_course_id, [getattr(self, "id"), ], lambda c: c.fetchall())
        for action in ret:
            if action[2] == sequence:
                raise InvalidArgumentException("课程的顺序重复!")


class ActionTemplate(object):
    def __init__(self):
        self.id = None
        self.content = None
        self.picture = None
        self.sequence = None
