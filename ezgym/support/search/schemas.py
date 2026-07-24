"""search 域 marshmallow schemas（请求校验）。"""
from marshmallow import fields, validate

from ezgym.core.schema import BaseInputSchema

__all__ = ["SearchQuerySchema"]


class SearchQuerySchema(BaseInputSchema):
    """GET /api/search 查询参数。目前仅支持 type=blog。"""

    type = fields.Str(
        load_default="blog",
        validate=validate.OneOf(["blog"]),
    )
    q = fields.Str(load_default="")
    cursor = fields.Int(required=False, allow_none=True)
    limit = fields.Int(required=False, allow_none=True)
