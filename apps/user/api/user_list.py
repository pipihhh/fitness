from flask_restful import Resource


class UserList(Resource):
    def get(self):
        """
        带分页的 get方法获取所有的用户 用于在后台管理显示
        :return:
        """
        pass
