import re
import uuid
import datetime
from flask_restful import Resource
from general.vaild import BaseValid, add_arg
from general.response import Response
from general.exception import *
from general.trace import trace
from general.db_pool import *
from general.password_handler import md5
from general.sql_map import InsertMap, SelectMap, DeleteMap
from conf.permission import permission_valid, ADMIN
from flask import request, jsonify
from flask_restful.reqparse import RequestParser

parser = RequestParser()
parser.add_argument("account", type=str, required=True)
parser.add_argument("password", type=str, required=True)
parser.add_argument("permission", type=int, required=True)
parser.add_argument("phone", type=str, required=True)
parser.add_argument("email", type=str)
parser.add_argument("gender", type=int, required=True)
parser.add_argument("age", type=int, required=True)
parser.add_argument("nick_name", type=str, required=True)
parser.add_argument("description", type=str)


class User(Resource):
    def get(self):
        account = request.json["account"]
        password = md5(request.json["password"])
        response = Response()
        connection = pool.connection()
        cursor = connection.cursor()
        try:
            ret = get_one(cursor, SelectMap.user_info_by_user_id, [account, password])
            response.data = {
                "id": ret[0], "account": ret[1],
                "permission": ret[2], "phone": ret[3],
                "email": ret[4], "gender": ret[5],
                "avatar": ret[6], "description": ret[7]
            }
        except Exception as e:
            response.code = 500
            response.errno = 1
            response.data = {
                "msg": "获取用户失败:" + str(e)
            }
        finally:
            cursor.close()
            connection.close()
        return jsonify(response.dict_data)

    def post(self):
        response = Response()
        args = parser.parse_args()
        valid = UserValid()
        add_arg(valid, args)
        ret = valid.valid_data()
        connection = pool.connection()
        if ret:
            response.data = ret
            response.errno = len(ret)
            response.code = 405
            return jsonify(response.dict_data)
        try:
            ret = self._add_user(args, connection)
            response.data = ret
        except UserAlreadyExistException as e:
            response.code = 405
            response.errno = 1
            response.data = {"msg": str(e)}
        except Exception as e:
            response.code = 500
            response.data = trace()
            response.errno = 1
            import traceback
            traceback.print_exc()
        finally:
            connection.close()
        return jsonify(response.dict_data)

    def put(self):
        pass

    @permission_valid(ADMIN)
    def delete(self):
        response = Response()
        try:
            user_id = request.json["id"]
            connection = pool.connection()
            response = self._delete_user(user_id, connection)
        except UserDoesNotExistException as e:
            response.code = 405
            response.errno = 1
            response.data = {"msg": str(e)}
        except KeyError as e:
            response.code = 405
            response.errno = 1
            response.data = {"msg": "你必须传一个id"}
        return jsonify(response.dict_data)

    def _add_user(self, args, connection):
        """
        新增一个用户，包括user表和user_info表，如果其中一个表插入出现问题
        则回滚，并返回错误
        :param args: ajax提交过来的参数
        :param connection: 数据库连接对象
        :return: 返回的json中 data部分 字典格式 出错返回错误信息，没出错返回插入成功的成员的信息
        """
        cursor = connection.cursor()
        number = str(uuid.uuid4())[:20]
        user_list = [args["account"], md5(args["password"]), args["permission"], str(number)]
        user = get_one(cursor, SelectMap.user_valid, [args["account"], ])
        if user:
            cursor.close()
            raise UserAlreadyExistException("此账号已存在")
        try:
            insert_sql_execute(cursor, InsertMap.user, user_list)
            user_id = get_one(cursor, SelectMap.user_by_number, str(number))[0]
            user_info_list = [
                user_id,
                args["phone"], args.get("email"),
                args["gender"], args["age"],
                args["nick_name"], args.get("description"),
                datetime.datetime.now()
            ]
            insert_sql_execute(cursor, InsertMap.user_info, user_info_list)
            connection.commit()
        except Exception as e:
            connection.rollback()
            connection.commit()
            return {"msg": "插入数据过程中出错:" + str(e)}
        finally:
            cursor.close()
        data = {"id": user_id}
        data.update(args)
        return data

    def _delete_user(self, user_id, connection):
        cursor = connection.cursor()
        user = get_one(cursor, SelectMap.user_valid_by_id, user_id)
        response = Response()
        if user:
            try:
                ret1 = delete_sql_execute(cursor, DeleteMap.user_by_id, user_id)
                ret2 = delete_sql_execute(cursor, DeleteMap.user_info_by_user_id, user_id)
                connection.commit()
                response.data = {"msg": ret1 + ret2}
            except Exception as e:
                connection.rollback()
                connection.commit()
                response.code = 500
                response.errno = 1
                response.data = {"msg": "内部错误:" + str(e)}
            finally:
                cursor.close()
                connection.close()
                return response
        raise UserDoesNotExistException("用户不存在")


class UserValid(BaseValid):
    def __init__(self):
        self._regx_phone = re.compile(r"1[3|5|7|8|9]\d{9}")
        self._regx_email = re.compile(r"\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*")
        BaseValid.__init__(self)

    def phone_valid(self, phone):
        if len(phone) != 11:
            raise InvalidArgumentException("错误的手机号长度")
        if re.match(self._regx_phone, phone) is None:
            raise InvalidArgumentException("手机号不合法")

    def email_valid(self, email):
        if re.match(self._regx_email, email) is None:
            raise InvalidArgumentException("错误的邮箱格式")

    def age_valid(self, age):
        if age <= 0 or age >= 200:
            raise InvalidArgumentException("错误的年龄段")

    def gender_valid(self, gender):
        if gender != 0 and gender != 1:
            raise InvalidArgumentException("错误的性别")
