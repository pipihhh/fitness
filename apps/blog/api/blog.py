from flask import jsonify, request, current_app
from flask_restful import Resource, reqparse
from bs4 import BeautifulSoup, Comment
from general.vaild import BaseValid
from utils.date_utils import is_file_exist
from general.exception import InvalidArgumentException
from general.sql_map import SelectMap, InsertMap, DeleteMap
from general.db_pool import execute_query_sql, execute_sql, fetchone_dict, fetchall_dict
from general.response import Response
from utils.error_handler import init_key_error_handler
from utils.idempotent_request import idempotent
from utils.general_object import GeneralObject
from utils.post_template import post
from conf.permission import permission_valid, NORMAL, ADMIN


parser = reqparse.RequestParser()
parser.add_argument("user_id", type=int, required=True)
parser.add_argument("content", type=str, required=True)
parser.add_argument("title", type=str, required=True)
parser.add_argument("picture", type=str, required=True)


class Blog(Resource):

    def get(self):
        response = Response()
        try:
            _id = request.args["id"]
            blog = fetchone_dict(SelectMap.blog_by_id, (_id, ), BlogTemplate)
            if blog is None:
                raise InvalidArgumentException("数据不存在")
            user = fetchone_dict(SelectMap.user_info_by_user_id, (blog.user_id, ), GeneralObject)
            response.data = blog.__dict__
            response.data.update({
                "nick_name": user.nick_name, "gender": user.gender, "email": user.email,
                "avatar": user.avatar, "permission": user.permission
            })
            req = fetchone_dict(SelectMap.comment_and_reply_count_by_blog, (_id, ), GeneralObject)
            response.data.update({
                "comment_count": req.count
            })
        except Exception as e:
            init_key_error_handler(response, e, "信息:")
        print(response.dict_data)
        return jsonify(response.dict_data)

    @idempotent
    @permission_valid(NORMAL)
    def post(self):
        """
        添加帖子的接口 帖子的添加需要携带 user_id content title picture 等键值对
        图片需要先上传 content需要不存在注释以及script标签
        :return:
        """
        response = Response()
        blog = BlogTemplate()
        resp = post(BlogValid, parser, blog)
        if resp is not None:
            return resp
        try:
            from datetime import datetime
            now = datetime.now()
            row_id = execute_sql(InsertMap.blog, (blog.user_id, blog.content, blog.title, blog.picture, now))
            if row_id == 0:
                raise InvalidArgumentException("插入记录失败")
            response.data = {
                "id": row_id, "user_id": blog.user_id, "content": blog.content,
                "title": blog.title, "picture": blog.picture, "create_time": now
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
            b = fetchone_dict(SelectMap.blog_by_id, (_id, ), GeneralObject)
            permission = getattr(request, "user")["permission"]
            if getattr(request, "user")["id"] != b.user_id and permission & ADMIN != ADMIN:
                raise InvalidArgumentException("权限不足")
            ret = execute_sql(DeleteMap.blog_by_id, (_id, ))
            if ret == 0:
                raise InvalidArgumentException("删除失败")
            response.data = {"msg": "ok"}
        except Exception as e:
            init_key_error_handler(response, e, "信息:")
        return jsonify(response.dict_data)


class BlogValid(BaseValid):
    def picture_valid(self, picture):
        import os
        if picture == '':
            setattr(self, "picture", os.path.join(current_app.config["MEDIA_URL"], "default_blog.jpg"))
        if is_file_exist(picture):
            setattr(self, "picture", os.path.join(current_app.config["MEDIA_URL"], picture))
            return
        raise InvalidArgumentException("图片不存在 请先上传!")

    def user_id_valid(self, user_id):
        ret = execute_query_sql(SelectMap.user_valid_by_id, (user_id, ), lambda c: c.fetchone())
        if not ret:
            raise InvalidArgumentException("用户不存在")
        if getattr(request, "user")["permission"] != 255 and getattr(request, "user")["id"] != user_id:
            raise InvalidArgumentException("此用户权限不足以创建为其他人创建文章")

    def content_valid(self, content):
        bs = BeautifulSoup(content, "html.parser")
        if bs.script or bs.findAll(text=lambda text: isinstance(text, Comment)):
            raise InvalidArgumentException("错误的content内容")


class BlogTemplate(object):
    def __init__(self):
        self.id = None
        self.user_id = None
        self.content = None
        self.title = None
        self.picture = None
        self.create_time = None
        self.upper = None
