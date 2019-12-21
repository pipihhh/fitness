import os
from utils.generic_import import *


class PersonalInfo(Resource):

    def get(self):
        response = Response()
        try:
            tag = request.args["tag"]
            func = getattr(self, f"_{tag}_info")
            func(response)
        except Exception as e:
            init_error_message(response, message=str(e))
        return jsonify(response.dict_data)

    def _blog_info(self, response):
        user_id = request.args.get("user_id") or getattr(request, "user")["id"]
        blog_list = fetchall_dict(SelectMap.blog_list_info, (user_id, ),
                                  GeneralObject)
        if not blog_list:
            raise UserDoesNotExistException("数据不存在")
        user = fetchone_dict(SelectMap.user_info_by_user_id, (user_id,), GeneralObject)
        for blog in blog_list:
            blog.nick_name = user.nick_name
            comment = fetchone_dict(SelectMap.comment_and_reply_count_by_blog, (blog.id,), GeneralObject)
            blog.comment_count = comment.count
            blog.content = self._get_content(blog.content)
        response.data = {
            "blog_list": [blog.data for blog in blog_list],
            "count": len(blog_list)
        }

    def _fans_and_follow_info(self, resp):
        user_id = request.args.get("id") or getattr(request, "user")["id"]
        fans = fetchone_dict(SelectMap.fans_info, (user_id, ), GeneralObject)
        follows = fetchone_dict(SelectMap.follow_info, (user_id, ), GeneralObject)
        resp.data = {
            "fans": fans.count, "follow": follows.count
        }

    def _fans_info(self, response):
        _id = request.args.get("id") or getattr(request, "user")["id"]
        fans = fetchone_dict(SelectMap.fans_info, (_id, ), GeneralObject)
        response.data = {
            "fans": fans.count
        }

    def _follow_info(self, response):
        _id = request.args.get("id") or getattr(request, "user")["id"]
        follows = fetchone_dict(SelectMap.follow_info, (_id, ), GeneralObject)
        response.data = {
            "follows": follows.count
        }

    def _comment_info(self, resp):
        user_id = request.user["id"]
        # 获取别人评价我的博客的信息
        comment_list = fetchall_dict(SelectMap.comment_list_by_user, (user_id, user_id), GeneralObject)
        for comment in comment_list:
            comment.is_comment = True
        reply_list = fetchall_dict(SelectMap.reply_list_by_user, (user_id, user_id), GeneralObject)
        for reply in reply_list:
            reply.is_comment = False
        reply_reply_list = fetchall_dict(SelectMap.reply_list_by_reply, (user_id, user_id), GeneralObject)
        for reply in reply_reply_list:
            reply.is_comment = False
        if not comment_list and reply_reply_list and reply_list:
            raise UserDoesNotExistException("暂无评论")
        comment_list.extend(reply_list)
        comment_list.extend(reply_reply_list)
        comment_list.sort(key=lambda x: x.create_time)
        comment_list.reverse()
        resp.data = {
            "ret_list": [comment.data for comment in comment_list],
            "count": len(comment_list)
        }

    def _get_content(self, content):
        soup = BeautifulSoup(content, "html.parser")
        length = current_app.config["TITLE_LENGTH"]
        return soup.text[:length + 1] + "..."

    def _course_info(self, resp):
        default_url = os.path.join(current_app.config["MEDIA_URL"], "default_course.jpg")
        user_id = request.args.get("id") or getattr(request, "user")["id"]
        course_list = fetchall_dict(SelectMap.course_list_by_user_id, (user_id, ), GeneralObject)
        if course_list:
            for course in course_list:
                action = fetchone_dict(SelectMap.action_list_by_course_id, (course.id, ), GeneralObject)
                course.picture = action.picture if action else default_url
            resp.data = {
                "course_list": [course.data for course in course_list],
                "count": len(course_list)
            }
        else:
            raise UserDoesNotExistException("暂无选课")
