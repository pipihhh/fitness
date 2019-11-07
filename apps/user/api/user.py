import re
import os
import uuid
import json
import datetime
from flask_restful import Resource
from general.vaild import BaseValid, add_arg
from general.response import Response
from general.exception import *
from general.trace import trace
from general.db_pool import *
from general.password_handler import md5
from general.sql_map import InsertMap, SelectMap, DeleteMap, UpdateMap
from utils.error_handler import init_key_error_handler
from utils.date_utils import get_exp_str, get_now
from utils.secert import encode_base64, get_jwt
from conf.permission import permission_valid, ADMIN, NORMAL
from flask import request, jsonify, current_app, g
from flask_restful.reqparse import RequestParser

parser = RequestParser()
parser.add_argument("account", type=str, required=True)
parser.add_argument("password", type=str, required=True)
parser.add_argument("permission", type=int, required=True)
parser.add_argument("phone", type=str, required=True)
parser.add_argument("email", type=str)
parser.add_argument("gender", type=int, required=True)  # 0男1女
parser.add_argument("age", type=int, required=True)
parser.add_argument("nick_name", type=str, required=True)
parser.add_argument("description", type=str)
parser.add_argument("avatar", type=str)


class User(Resource):
    def get(self):
        """
        get方法的接口，获取单个的用户，通过账号密码，如果用户存在，则返回用户信息和token
        :return:
        """
        account = request.json["account"]
        password = md5(request.json["password"])
        response = Response()
        connection = pool.connection()
        cursor = connection.cursor()
        try:
            ret = get_one(cursor, SelectMap.user_info_with_login, [account, password])
            if ret is None:
                raise UserDoesNotExistException("用户不存在")
            response.data = {
                "id": ret[0], "account": ret[1],
                "permission": ret[2], "phone": ret[3],
                "email": ret[4], "gender": ret[5],
                "avatar": ret[6], "description": ret[7],
                "token": self._make_jwt(ret)
            }
        except UserDoesNotExistException as e:
            init_key_error_handler(response, e, "提示:")
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

    def _make_jwt(self, user):
        """
        为用户生成token，iat代表了签发token的时间，exp代表了超时时间 和配置有关
        :param user:查到的用户对象信息组成的元组 具体的对应字段在sql_map中查看
        :return:
        """
        config = current_app.config
        header = {"typ": config["JWT_TYPE"], "alg": config["JWT_ALG"]}
        payload = {
            "id": user[0], "permission": user[2], "password": user[8],
            "exp": get_exp_str(), "iat": get_now()
        }
        return get_jwt(
            encode_base64(json.dumps(header)), encode_base64(json.dumps(payload)),
            config["JWT_ALG"]
        )

    def post(self):
        """
        post方法，添加用户，会进行参数校验
        :return:
        """
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
        except Exception:
            response.code = 500
            response.data = trace()
            response.errno = 1
        finally:
            connection.close()
        return jsonify(response.dict_data)

    @permission_valid(NORMAL)
    def put(self):
        """
        修改，修改用户信息使用此方法
        :return:
        """
        response = Response()
        connection = pool.connection()
        try:
            tag = request.json["tag"]
            user_id = request.json.get("id") or getattr(g, "user")["id"]
            getattr(self, "_update_" + tag)(connection, user_id)
            response.data = {"msg": "ok"}
        except (KeyError, AttributeError, InvalidArgumentException) as e:
            init_key_error_handler(response, e)
        finally:
            connection.close()
        return jsonify(response.dict_data)

    def _update_avatar(self, connection, user_id):
        """
        此方法用来修改用户的头像，此方法适用于普通用户和管理员，普通用户只拥有修改自己头像的权限
        此时在请求中需要携带avatar，其中值为对应的文件名而不应该是路径，否则此方法会报错
        :param connection: 数据库连接对象 不是cursor对象
        :param user_id: 要修改的用户的id
        :return:
        """
        avatar = request.json["avatar"]
        image_path = os.path.join(current_app.config["MEDIA_DIR"], avatar)
        if not os.path.isfile(image_path):
            raise InvalidArgumentException("avatar的格式错误!")
        avatar = current_app.config["MEDIA_URL"] + avatar
        if self._valid_current_permission(user_id):
            cursor = connection.cursor()
            try:
                update_sql_execute(cursor, UpdateMap.update_avatar_by_user_id, [avatar, user_id])
                connection.commit()
            except Exception:
                connection.rollback()
                connection.commit()
                raise
            finally:
                cursor.close()

    def _update_description(self, connection, user_id):
        cursor = connection.cursor()
        valid = UserValid(request.json)
        description = valid.clean_data["description"]
        print(description)
        try:
            ret = update_sql_execute(cursor, UpdateMap.update_description_by_id, [description, user_id])
            if ret != 1:
                raise InvalidArgumentException("参数有误，修改失败")
            connection.commit()
        except Exception:
            connection.rollback()
            connection.commit()
            raise
        finally:
            cursor.close()

    def _update_all(self, connection, user_id):
        cursor = connection.cursor()
        args = parser.parse_args()
        valid = UserValid()
        add_arg(valid, args)
        ret = valid.valid_data()
        if ret:
            err_msg = "参数格式有误:" + ",".join(ret)
            raise IllegalTokenException(err_msg)
        try:
            params = valid.clean_data
            user_info_args = [
                params["phone"], params.get("email"), params["gender"], params["avatar"],
                params["age"], params["nick_name"], params.get("nick_name"), user_id
            ]
            user_args = [params["account"], md5(params["password"]), user_id]
            update_sql_execute(cursor, UpdateMap.update_user_info_by_user_id, user_info_args)
            update_sql_execute(cursor, UpdateMap.update_user_by_id, user_args)
            connection.commit()
        except Exception:
            connection.rollback()
            connection.commit()
            raise
        finally:
            cursor.close()

    def _update_password(self, connection, user_id):
        cursor = connection.cursor()
        valid = UserValid()
        add_arg(valid, request.json)
        ret = valid.valid_data()
        if self._valid_current_permission(user_id) and not ret:
            try:
                update_sql_execute(cursor, UpdateMap.update_password_by_id,
                                   [md5(valid.clean_data["password"]), user_id])
                connection.commit()
            except Exception:
                connection.rollback()
                connection.commit()
                raise
            finally:
                cursor.close()
                return
        string = None
        if ret:
            string = "参数有误:" + ",".join(ret.values())
        raise InvalidArgumentException(string or "权限错误")

    def _valid_current_permission(self, user_id):
        current_id = getattr(request, "user")["id"]  # 当前发起请求的用户的id
        current_permission = getattr(request, "user")["permission"]  # 当前用户的权限
        return current_id == user_id or current_permission & ADMIN == ADMIN

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
        except KeyError:
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
        """
        删除一个用户的具体逻辑，包括判断用户是否存在等，此方法如果用户不存在会
        抛出异常
        :param user_id: 想要删除的用户的id
        :param connection: 数据库连接的conn对象
        :return: 抛出异常或者返回response对象
        """
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
    def __init__(self, *args, **kwargs):
        self._regx_phone = re.compile(r"1[3|5|7|8|9]\d{9}")
        self._regx_email = re.compile(r"\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*")
        BaseValid.__init__(self, *args, **kwargs)

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

    def nick_name_valid(self, nick_name):
        if len(nick_name) >= 30:
            raise InvalidArgumentException("昵称过长")

    def avatar_valid(self, avatar):
        image_path = os.path.join(current_app.config["MEDIA_DIR"], avatar)
        if not os.path.isfile(image_path):
            raise InvalidArgumentException("avatar的格式错误!")
        self.__dict__["avatar"] = current_app.config["MEDIA_URL"] + avatar

    def permission_valid(self, permission):
        import conf.permission
        p_set = set()
        for key in conf.permission.__all__:
            if key.isupper():
                p_set.add(int(getattr(conf.permission, key)))
        if permission not in p_set:
            raise InvalidArgumentException("权限参数不正确")

    def account_valid(self, account):
        if len(account) >= 18:
            raise InvalidArgumentException("账号长度过长")

    def password_valid(self, password):
        if request.method == "PUT":
            user_id = request.json.get("id") or getattr(request, "user")["id"]
            connection = pool.connection()
            cursor = connection.cursor()
            user = get_one(cursor, SelectMap.user_valid_by_id, user_id)
            if user:
                real_password = user[-1]
                if md5(password) == real_password and request.json["tag"] == "password":
                    raise InvalidArgumentException("密码相同!")
                if user[0] != user_id and user[2] & ADMIN != ADMIN:
                    raise InvalidArgumentException("权限不足")
                return
            raise InvalidArgumentException("用户不存在")

    def description_valid(self, description):
        if len(description) > 300:
            raise InvalidArgumentException("描述过长")
        description = description.replace("<", "&lt;").replace(">", "&gt;").replace(" ", "&nbsp;")
        setattr(self, "description", description)
