import datetime
from flask import request, jsonify
from flask_restful import Resource, reqparse
from general.vaild import BaseValid
from general.sql_map import SelectMap, InsertMap, DeleteMap
from general.db_pool import fetchone_dict, execute_sql
from general.exception import InvalidArgumentException
from general.response import Response
from conf.permission import permission_valid, NORMAL
from utils.post_template import post
from utils.error_handler import init_key_error_handler
from utils.idempotent_request import idempotent
from utils.general_object import GeneralObject

parse = reqparse.RequestParser()
parse.add_argument("content", type=str, required=True)
parse.add_argument("blog_id", type=int, required=True)


class Comment(Resource):

    @idempotent
    @permission_valid(NORMAL)
    def post(self):
        comment = CommentTemplate()
        response = post(CommentValid, parse, comment)
        if response:
            return jsonify(response.dict_data)
        try:
            response = Response()
            now = datetime.datetime.now()
            user_id = getattr(request, "user")["id"]
            user = fetchone_dict(SelectMap.user_info_by_user_id, (user_id,), GeneralObject)
            ret = execute_sql(InsertMap.comment,
                              (comment.content, now, comment.blog_id, user_id, user.nick_name),
                              True)
            if ret == 0:
                raise InvalidArgumentException("评论失败")
            response.data = {
                "id": ret, "create_time": now, "content": comment.content,
                "blog_id": comment.blog_id, "user_id": user_id,
                "nick_name": user.nick_name
            }
        except Exception as e:
            init_key_error_handler(response, e, "信息:")
        return jsonify(response.dict_data)

    @idempotent
    @permission_valid(NORMAL)
    def delete(self):
        response = Response()
        try:
            _id = request.json["id"]
            comment_count = execute_sql(DeleteMap.comment_by_id, (_id, ))
            if comment_count == 0:
                raise InvalidArgumentException("删除失败!")
            reply_count = execute_sql(DeleteMap.reply_by_comment_id, (_id, ))
            response.data = {
                "comment_count": comment_count, "reply_count": reply_count,
                "msg": "ok"
            }
        except Exception as e:
            init_key_error_handler(response, e, "信息:")
        return jsonify(response.dict_data)


class CommentValid(BaseValid):
    def content_valid(self, content):
        if len(content) > 1024:
            raise InvalidArgumentException("评论过长")
        description = content.replace("<", "&lt;").replace(">", "&gt;").replace(" ", "&nbsp;")
        setattr(self, "content", description)

    def blog_id_valid(self, blog_id):
        blog = fetchone_dict(SelectMap.blog_by_id, (blog_id,), GeneralObject)
        if blog is None:
            raise InvalidArgumentException("博客不存在")


class CommentTemplate(object):
    def __init__(self):
        self.content = None
        self.blog_id = None
        self.user_id = None
        self.nick_name = None
