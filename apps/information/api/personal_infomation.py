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
        query_id = request.args.get("id", 0)
        offset = request.args.get("offset", current_app.config["PAGE_OFFSET"])
        blog_list = fetchall_dict(SelectMap.blog_list_info, (getattr(request, "user")["id"], query_id, offset),
                                  GeneralObject)
        if not blog_list:
            raise UserDoesNotExistException("数据不存在")
        response.data = {
            "blog_list": [blog.data for blog in blog_list],
            "query_id": blog_list[-1].id, "last_query_id": query_id,
            "count": len(blog_list), "page_offset": offset
        }
