from flask import jsonify, request, current_app
from flask_restful import Resource
from general.vaild import BaseValid
from general.db_pool import execute_query_sql
from general.sql_map import SelectMap
from general.exception import InvalidArgumentException, UserDoesNotExistException
from utils.error_handler import init_key_error_handler
from utils.throttle import throttle
from conf.permission import permission_valid, ADMIN
from general.response import Response


class UserList(Resource):

    @throttle(2, 10)
    @permission_valid(ADMIN)
    def get(self):
        """
        带分页的 get方法获取所有的用户 用于在后台管理显示
        缺点为，我不会关心你这个id的合法性，假如每页要显示的数量为10个 但是 你给了我一个10个中的1个id 对于这种情况我不会进行校验
        此方法不会包含你传过来的id对应的用户，只会传过来以你传过来的id为头但是不含此id的LIMIT个用户，并将此结果集的最后一个用户的id单独返回
        用来作为下次请求的参数，如果你是首次请求，则默认选择的起始id为0
        :return:
        """
        response = Response()
        try:
            valid = UserListValid(request.json)
            data = valid.clean_data
            limit = current_app.config["PAGE_OFFSET"]
            ret = execute_query_sql(SelectMap.user_list_by_offset, [data.get("query_id", 0), limit])
            if ret == ():
                raise UserDoesNotExistException("id不存在")
            response.data = {
                "user_list": [{
                    "id": user[0],
                    "permission": user[1], "account": user[2], "nick_name": user[3],
                    "age": user[4], "avatar": user[5], "gender": user[6], "email": user[7],
                    "phone": user[8], "description": user[9], "create_time": user[10]
                } for user in ret],
                "count": len(ret),
                "query_id": ret[-1][0],
                "page": data["page"],
                "last_query_id": data.get("query_id", 0),
                "page_offset": limit
            }
        except (KeyError, UserDoesNotExistException) as e:
            init_key_error_handler(response, e)
        return jsonify(response.dict_data)


class UserListValid(BaseValid):
    def page_valid(self, page):
        """
        此方法会校验你传过来的页码是否合理，通过计算所有用户的行数和你的页数进行比对得出的
        :param page:
        :return:
        """
        if isinstance(page, int):
            count = execute_query_sql(SelectMap.user_count, [], lambda c: c.fetchone())[0]
            offset = current_app.config["PAGE_OFFSET"]
            if count + offset < page * offset:
                raise InvalidArgumentException("错误的页码")
            return
        raise InvalidArgumentException("page must be Integer")
