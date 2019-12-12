from utils.generic_import import *


class PersonalInfo(Resource):

    @permission_valid(NORMAL)
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
        query_id = request.args.get("id", 0)
        offset = request.args.get("offset", current_app.config["PAGE_OFFSET"])
        blog_list = fetchall_dict(SelectMap.blog_list_info, (getattr(request, "user")["id"], query_id, offset),
                                  GeneralObject)
        if not blog_list:
            raise UserDoesNotExistException("数据不存在")
        user = fetchone_dict(SelectMap.user_info_by_user_id, (getattr(request, "user")["id"],), GeneralObject)
        for blog in blog_list:
            blog.nick_name = user.nick_name
            comment_list = fetchall_dict(SelectMap.comment_by_blog_id, (blog.id,), GeneralObject)
            blog.comment_count = len(comment_list)
            blog.content = self._get_content(blog.content)
        response.data = {
            "blog_list": [blog.data for blog in blog_list],
            "query_id": blog_list[-1].id, "last_query_id": query_id,
            "count": len(blog_list), "page_offset": offset
        }

    @permission_valid(NORMAL)
    def _fans_info(self, response):
        _id = getattr(request, "user")["id"]
        fans = fetchone_dict(SelectMap.fans_info, (_id, ), GeneralObject)
        response.data = {
            "count": fans.count
        }

    @permission_valid(NORMAL)
    def _follow_info(self, response):
        _id = getattr(request, "user")["id"]
        follows = fetchone_dict(SelectMap.follow_info, (_id, ), GeneralObject)
        response.data = {
            "count": follows.count
        }

    def _get_content(self, content):
        soup = BeautifulSoup(content, "html.parser")
        length = current_app.config["TITLE_LENGTH"]
        return soup.text[:length + 1] + "..."
