import datetime
from bs4 import BeautifulSoup, Comment
from flask import request, current_app, jsonify
from flask_restful import Resource, reqparse
from general.response import Response
from general.sql_map import InsertMap, SelectMap, UpdateMap
from general.db_pool import execute_sql, fetchone_dict
from general.exception import InvalidArgumentException
from utils.generate_number import generate_number
from utils.date_utils import is_file_exist
from utils.idempotent_request import idempotent
from conf.permission import permission_valid, ADMIN
from general.vaild import BaseValid
from utils.error_handler import init_key_error_handler
from utils.post_template import post


parse = reqparse.RequestParser()
parse.add_argument("picture", type=str, required=True)
parse.add_argument("content", type=str, required=True)
parse.add_argument("start_time", type=str, required=True)
parse.add_argument("end_time", type=str, required=True)


class Challenge(Resource):

    def get(self):
        """
        获取一个特定的挑战的接口 根据course id  请求需要携带一个参数 id 由于挑战 不用登陆也可以访问
        所以不加权，此pageviews每请求一次就会增加一次 在多线程环境下会不准确 但是没关系 问题不大
        :return:
        """
        response = Response()
        try:
            _id = request.args["id"]
            challenge = fetchone_dict(SelectMap.challenge_by_id, [_id, ], ChallengeTemplate)
            if challenge:
                ret = execute_sql(UpdateMap.update_challenge_pageviews, [challenge.id, ])
                if ret == 0:
                    raise InvalidArgumentException("数据不存在")
                response.data = {
                    "id": challenge.id, "picture": challenge.picture,
                    "content": challenge.content, "start_time": challenge.start_time,
                    "end_time": challenge.end_time, "create_time": challenge.create_time,
                    "pageviews": challenge.pageviews + 1
                }
                return jsonify(response.dict_data)
            raise InvalidArgumentException("数据不存在")
        except Exception as e:
            init_key_error_handler(response, e, "信息:")
        return jsonify(response.dict_data)

    @idempotent
    @permission_valid(ADMIN)
    def post(self):
        """
        添加挑战的接口 此接口的content是一个重点 是有格式要求的 要求就是 其中的html不能包含script标签
        也不能含有任何的注释
        添加挑战的另一个约定就是 start_time和end_time是有格式要求的 必须是2019-11-03这种格式 无法配置
        :return:
        """
        challenge = ChallengeTemplate()
        response = post(ChallengeValid, parse, challenge)
        if response is None:
            response = Response()
            try:
                number = generate_number(20)
                ret = execute_sql(InsertMap.challenge, [
                    challenge.picture, challenge.content, challenge.start_time,
                    challenge.end_time, datetime.datetime.now(), challenge.pageviews,
                    number
                ])
                if ret == 0:
                    raise InvalidArgumentException("数据写入失败")
                challenge = fetchone_dict(SelectMap.challenge_by_number, [number, ], ChallengeTemplate)
                response.data = {
                    "id": challenge.id, "picture": challenge.picture,
                    "content": challenge.content, "start_time": challenge.start_time,
                    "end_time": challenge.end_time, "create_time": challenge.create_time,
                    "pageviews": challenge.pageviews
                }
            except Exception as e:
                init_key_error_handler(response, e, "信息:")
        return jsonify(response.dict_data)

    @idempotent
    @permission_valid(ADMIN)
    def put(self):
        """
        修改挑战的接口 和post接口相比 需要多传一个id的key 如果id不存在 则无法执行
        :return:
        """
        challenge = ChallengeTemplate()
        response = post(ChallengeValid, parse, template=challenge)
        if response is None:
            response = Response()
            try:
                _id = challenge.id
                ret = execute_sql(UpdateMap.update_challenge_by_id, [
                    challenge.picture, challenge.content, challenge.start_time,
                    challenge.end_time, _id
                ])
                if ret == 0:
                    raise InvalidArgumentException("数据不存在")
            except InvalidArgumentException as e:
                response.errno = 1
                response.code = 403
                response.data = {"msg": str(e)}
            except Exception as e:
                init_key_error_handler(response, e, "信息:")
        return jsonify(response.dict_data)


class ChallengeValid(BaseValid):
    def start_time_valid(self, start_time):
        now = datetime.date.today()
        start_time = datetime.date.fromisoformat(start_time)
        if start_time < now:
            raise InvalidArgumentException("开始时间必须大于或等于当前时间(1分钟的误差)")

    def end_time_valid(self, end_time):
        now = datetime.date.today()
        end_time = datetime.date.fromisoformat(end_time)
        start_time = getattr(self, "start_time")
        if isinstance(start_time, str):
            start_time = datetime.date.fromisoformat(start_time)
        if end_time < start_time or end_time < now:
            raise InvalidArgumentException("错误的end_time")

    def content_valid(self, content):
        bs = BeautifulSoup(content, "html.parser")
        if bs.script or bs.findAll(text=lambda text: isinstance(text, Comment)):
            raise InvalidArgumentException("错误的content内容")

    def picture_valid(self, picture):
        if not is_file_exist(picture):
            raise InvalidArgumentException("图片文件不存在，请先上传!")
        setattr(self, picture, current_app.config["MEDIA_URL"] + picture)

    def id_valid(self, _id):
        challenge = fetchone_dict(SelectMap.challenge_by_id, [_id], ChallengeTemplate)
        if challenge:
            return
        raise InvalidArgumentException("数据不存在")


class ChallengeTemplate(object):
    def __init__(self):
        self.picture = None
        self.content = None
        self.start_time = None
        self.end_time = None
        self.pageviews = 0
