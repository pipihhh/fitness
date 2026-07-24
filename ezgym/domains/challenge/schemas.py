"""challenge 域 marshmallow schemas（请求校验 + 响应序列化）。

- ChallengeSchema：单挑战完整序列化。
- ChallengeListItemSchema：列表项，额外带从 content 截取的 title（config.TITLE_LENGTH）。
- ChallengeCreateSchema / ChallengeUpdateSchema：写入请求校验。
  日期以 "YYYY-MM-DD" 字符串入参，实际解析为 datetime 在 service 层完成。
"""
from flask import current_app
from marshmallow import fields

from ezgym.core.schema import BaseInputSchema, BaseSchema
from ezgym.domains.challenge.models import Challenge

__all__ = [
    "ChallengeSchema",
    "ChallengeListItemSchema",
    "ChallengeCreateSchema",
    "ChallengeUpdateSchema",
]


class ChallengeSchema(BaseSchema):
    """单挑战完整序列化。"""

    class Meta(BaseSchema.Meta):
        model = Challenge
        exclude = ("is_deleted",)


class ChallengeListItemSchema(BaseSchema):
    """列表项：在完整字段基础上追加截取的 title。"""

    title = fields.Method("_truncate_title")

    class Meta(BaseSchema.Meta):
        model = Challenge
        exclude = ("is_deleted",)

    def _truncate_title(self, obj) -> str:
        content = obj.content or ""
        length = current_app.config.get("TITLE_LENGTH", 10)
        return content[:length]


class ChallengeCreateSchema(BaseInputSchema):
    """创建挑战入参。number 由 service 自动生成，不接受前端传入。"""

    picture = fields.Str(required=False, allow_none=True)
    content = fields.Str(required=False, allow_none=True)
    start_time = fields.Str(required=True)  # "YYYY-MM-DD"
    end_time = fields.Str(required=True)  # "YYYY-MM-DD"


class ChallengeUpdateSchema(BaseInputSchema):
    """更新挑战入参：任意子集。"""

    picture = fields.Str(required=False, allow_none=True)
    content = fields.Str(required=False, allow_none=True)
    start_time = fields.Str(required=False, allow_none=True)  # "YYYY-MM-DD"
    end_time = fields.Str(required=False, allow_none=True)  # "YYYY-MM-DD"
