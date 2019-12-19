from utils.generic_import import *


parse = reqparse.RequestParser()
parse.add_argument("course_id", type=int)
parse.add_argument("id", type=int)


class Study(Resource):

    def _roll_back(self, resp, req, collect):
        ret = execute_sql(UpdateMap.collect_rollback, (getattr(request, "user")["id"], req.course_id))
        if ret == 0:
            raise UserAlreadyExistException("选取失败")
        resp.data = {
            "id": collect.id, "create_time": collect.create_time,
            "user_id": collect.user_id, "course_id": collect.course_id,
        }

    @idempotent
    @permission_valid(NORMAL)
    def post(self):
        req = GeneralObject()
        resp = post(StudyValid, parse, req)
        if resp is not None:
            return jsonify(resp.dict_data)
        resp = Response()
        try:
            now = datetime.datetime.now()
            user_id = getattr(request, "user")["id"]
            collect = fetchone_dict(SelectMap.collect_without_flag, (user_id, req.course_id), GeneralObject)
            if collect:
                self._roll_back(resp, req, collect)
            else:
                rowid = execute_sql(InsertMap.collect, (user_id, req.course_id, now), True)
                if rowid == 0:
                    raise InvalidArgumentException("选取失败")
                resp.data = {
                    "id": rowid, "create_time": now,
                    "user_id": user_id, "course_id": req.course_id
                }
        except Exception as e:
            init_error_message(resp, message=str(e))
        return jsonify(resp.dict_data)

    @idempotent
    @permission_valid(NORMAL)
    def delete(self):
        req = GeneralObject()
        resp = post(StudyValid, parse, req)
        if resp is not None:
            return jsonify(resp.dict_data)
        resp = Response()
        try:
            ret = execute_sql(DeleteMap.collect, (req.id, ))
            if ret == 0:
                raise InvalidArgumentException("取消错误")
            resp.data = {
                "msg": "ok"
            }
        except Exception as e:
            init_error_message(resp, message=str(e))
        return jsonify(resp.dict_data)


class StudyValid(BaseValid):
    def valid(self):
        if request.method == "POST":
            if not hasattr(self, "course_id"):
                raise InvalidArgumentException("错误的course_id")
        if request.method == "DELETE":
            if not hasattr(self, "id"):
                raise InvalidArgumentException("错误的id")

    def course_id_valid(self, course_id):
        user_id = getattr(request, "user")["id"]
        collect = fetchone_dict(SelectMap.collect_by_course_id, (course_id, user_id), GeneralObject)
        if request.method == "POST" and collect is not None:
            raise InvalidArgumentException("已经选过此课程")
        course = fetchone_dict(SelectMap.course_by_id, (course_id, ), GeneralObject)
        if course is None:
            raise InvalidArgumentException("错误的课程id")

    def id_valid(self, _id):
        collect = fetchone_dict(SelectMap.collect_valid, (_id, ), GeneralObject)
        if collect is None:
            raise InvalidArgumentException("找不到信息 错误的id")
