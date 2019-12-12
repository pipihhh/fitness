import datetime
from utils.generic_import import *


parse = reqparse.RequestParser()
parse.add_argument("to_id", type=int, required=True)


class Follow(Resource):

    @idempotent
    @permission_valid(NORMAL)
    def post(self):
        req = GeneralObject()
        resp = post(FollowValid, parse, req)
        if resp is not None:
            return jsonify(resp.dict_data)
        resp = Response()
        try:
            now = datetime.datetime.now()
            ret = execute_sql(InsertMap.follow, (getattr(request, "user")["id"], req.to_id, now), True)
            if ret == 0:
                raise UserDoesNotExistException("关注失败 请重试")
            resp.data = {
                "from_id": getattr(request, "user")["id"],
                "to_id": req.to_id,
                "create_time": now,
                "count": ret,
                "msg": "ok"
            }
        except Exception as e:
            init_error_message(resp, message=str(e))
        return jsonify(resp.dict_data)

    @permission_valid(NORMAL)
    def delete(self):
        req = GeneralObject()
        resp = post(FollowValid, parse, req)
        if resp is not None:
            return jsonify(resp.dict_data)
        resp = Response()
        try:
            ret = execute_sql(DeleteMap.follow, (getattr(request, "user")["id"], req.to_id))
            if ret == 0:
                raise UserDoesNotExistException("删除失败")
            resp.data = {
                "from_id": getattr(request, "user")["id"], "to_id": req.to_id,
                "count": ret, "msg": "ok"
            }
        except Exception as e:
            init_error_message(resp, message=str(e))


class FollowValid(BaseValid):
    def to_id_valid(self, to_id):
        user = fetchone_dict(SelectMap.user_valid_by_id, (to_id, ), GeneralObject)
        if user is None:
            raise InvalidArgumentException("用户不存在")
        follow = fetchone_dict(SelectMap.follow_valid, (getattr(request, "user")["id"], to_id), GeneralObject)
        if follow is not None:
            raise UserAlreadyExistException("已经关注过了")
