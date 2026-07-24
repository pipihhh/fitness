"""notification 域 marshmallow schemas。

本域无对外 HTTP 端点（仅内部 service），不接收 HTTP 请求体、不返回序列化响应，
因此无需定义 marshmallow schema。入参校验（如邮箱是否存在）由调用方 identity 域负责。
保留本模块以对齐各域目录结构。
"""
