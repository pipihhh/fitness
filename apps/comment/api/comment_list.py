from utils.generic_import import *


class CommentList(Resource):
    def get(self):
        status, req = generic_template(CommentListValid, request.args, GeneralObject)
        if not status:
            return jsonify(req.dict_data)
        resp = Response()
        try:
            blog_id = req.blog_id
            comment_list = fetchall_dict(SelectMap.comment_list_by_blog, (blog_id,), GeneralObject)
            if not comment_list:
                raise InvalidArgumentException("暂无评论")
            for comment in comment_list:
                reply_list = fetchall_dict(SelectMap.reply_list_by_comment_id, (comment.id,), GeneralObject)
                comment.reply_count = len(reply_list)
                comment.reply_list = [reply.data for reply in reply_list]
                reply_linklist = {}
                for reply in reply_list:
                    reply_linklist[reply.id] = reply.data
                comment.reply_linklist = reply_linklist
            resp.data = {
                "comment_list": [comment.data for comment in comment_list],
                "count": len(comment_list)
            }
        except Exception as e:
            init_error_message(resp, message=str(e))
        return jsonify(resp.dict_data)


class CommentListValid(BaseValid):
    def valid(self):
        if not hasattr(self, "blog_id"):
            raise InvalidArgumentException("缺少参数blog_id")
        blog = fetchone_dict(SelectMap.blog_by_id, (getattr(self, "blog_id"),), GeneralObject)
        if blog is None:
            raise InvalidArgumentException("blog不存在")
