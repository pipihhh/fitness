from general.vaild import BaseValid
from general.exception import InvalidArgumentException


class BlogValider(BaseValid):
    def valid(self):
        content = getattr(self, "content")
        if len(content) > 50:
            setattr(self, "content", content[:51])

    def id_valid(self, _id):
        if isinstance(_id, str):
            raise InvalidArgumentException("id的格式不能为字符串")

    def offset_valid(self, offset):
        if isinstance(offset, str):
            raise InvalidArgumentException("offset的格式不能为字符串")
