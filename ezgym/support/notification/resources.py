"""notification 域 HTTP 资源注册入口（flask-restful）。"""


def register(api):
    """向 flask-restful Api 注册本域 Resource。

    地基阶段为 stub。本域 agent 在此用
    ``api.add_resource(XxxResource, "/api/...")`` 注册端点。
    Api 已绑定 app，勿在此创建新的 Api 实例。
    """
    pass
