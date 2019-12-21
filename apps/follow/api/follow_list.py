from utils.generic_import import *


class FollowList(Resource):
    map = {
        "fans": SelectMap.fans_list,
        "follow": SelectMap.follow_list
    }

    @permission_valid(NORMAL)
    def get(self):
        status, req = generic_template(FollowListValid, request.args, GeneralObject)
        if status is False:
            return jsonify(req.dict_data)
        resp = Response()
        try:
            user_id = request.args.get("id") or getattr(request, "user")["id"]
            ret_list = fetchall_dict(self.map[req.tag], (user_id, ), GeneralObject)
            if not ret_list:
                raise UserDoesNotExistException("此用户暂无数据")
            resp.data = {
                f"{req.tag}_list": [ret.data for ret in ret_list],
                "count": len(ret_list)
            }
        except Exception as e:
            init_error_message(resp, message=str(e))
        return jsonify(resp.dict_data)


class FollowListValid(BaseValid):
    def valid(self):
        if not hasattr(self, "tag"):
            raise InvalidArgumentException("缺少必要的参数tag")

    def tag_valid(self, tag):
        if tag not in FollowList.map:
            raise InvalidArgumentException("tag不存在")
