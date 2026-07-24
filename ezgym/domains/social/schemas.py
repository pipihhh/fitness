"""social 域 marshmallow schemas（请求校验）。

- FollowCreateSchema：POST /api/follows 入参（to_id 必填）。
- FollowListQuerySchema：GET /api/follows 查询参数（type / user_id / cursor / limit）。
"""
from marshmallow import fields, validate

from ezgym.core.schema import BaseInputSchema

__all__ = ["FollowCreateSchema", "FollowListQuerySchema"]


class FollowCreateSchema(BaseInputSchema):
    """POST /api/follows 入参。"""

    to_id = fields.Int(required=True)


class FollowListQuerySchema(BaseInputSchema):
    """GET /api/follows 查询参数：type 决定粉丝/关注，缺省看关注列表。"""

    type = fields.Str(
        load_default="following",
        validate=validate.OneOf(["fans", "following"]),
    )
    user_id = fields.Int(required=False, allow_none=True)
    cursor = fields.Int(required=False, allow_none=True)
    limit = fields.Int(required=False, allow_none=True)
