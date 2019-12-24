from utils.generic_import import *
from apps.search.vailders.blog_valider import BlogValider


class Searcher(Resource):
    def get(self):
        """
        搜索接口 目前只有blog的搜索 参数有4 tag content offset id
        offset和id选填 默认为配置项和0
        tag为你要搜索的表 目前只支持了blog
        content代表要搜索的内容 在blog表中只会和title相搜索
        :return:
        """
        response = Response()
        try:
            tag = request.args["tag"]
            func = getattr(self, f"_{tag}_search")
            func(response)
        except AttributeError:
            init_error_message(response, message="找不到tag对应的接口")
        except Exception as e:
            init_error_message(response, message=str(e))
        return jsonify(response.dict_data)

    def _blog_search(self, response):
        valider = BlogValider(request.args)
        valider.valid_data()
        data = valider.clean_data
        _id = request.args.get("id", 0)
        offset = request.args.get("offset", current_app.config["PAGE_OFFSET"])
        blog_list = fetchall_dict(
            SelectMap.blog_search.format(_id, data["content"], offset), None,
            create_cmp_with_class(_lt)
        )
        if not blog_list:
            raise UserDoesNotExistException("博客不存在或id已超过限制")
        query_id = blog_list[-1].id
        blog_list.sort()
        response.data = {
            "blog_list": [blog.data for blog in blog_list],
            "count": len(blog_list), "last_query_id": _id,
            "query_id": query_id
        }


def _lt(self, o):
    if self.upper == o.upper:
        return o.create_time > self.create_time
    return self.upper > o.upper
