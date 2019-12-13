from utils.generic_import import *

parse = reqparse.RequestParser()
parse.add_argument("comment_id", type=int, required=True)
parse.add_argument("content", type=str, required=True)
parse.add_argument("reply_id", type=int)


class Reply(Resource):

    @idempotent
    @permission_valid(NORMAL)
    def post(self):
        req = GeneralObject()
        resp = post(ReplyValid, parse, req)
        if resp is not None:
            return jsonify(resp.dict_data)
        resp = Response()
        try:
            now = datetime.datetime.now()
            _id = getattr(request, "user")["id"]
            user = fetchone_dict(SelectMap.user_info_by_user_id, (_id,), GeneralObject)
            reply_id = getattr(req, "reply_id") or 0
            rowid = execute_sql(InsertMap.reply, (
                req.comment_id, now, _id, user.nick_name,
                reply_id, req.content
            ), True)
            if rowid == 0:
                raise InvalidArgumentException("操作失败")
            resp.data = {
                "create_time": now, "id": rowid, "comment_id": req.comment_id,
                "user_id": _id, "nick_name": user.nick_name, "reply_id": reply_id
            }
        except Exception as e:
            init_error_message(resp, message=str(e))
        return jsonify(resp.dict_data)


class ReplyValid(BaseValid):
    def comment_id_valid(self, comment_id):
        comment = fetchone_dict(SelectMap.comment_valid, (comment_id,), GeneralObject)
        if comment is None:
            raise UserDoesNotExistException("comment不存在")

    def reply_id_valid(self, reply_id):
        reply = fetchone_dict(SelectMap.reply_valid, (reply_id,), GeneralObject)
        if reply is None:
            raise UserDoesNotExistException("reply不存在")

    def content_valid(self, content):
        if len(content) > 1024:
            raise InvalidArgumentException("评论过长")
        description = content.replace("<", "&lt;").replace(">", "&gt;").replace(" ", "&nbsp;")
        setattr(self, "content", description)
