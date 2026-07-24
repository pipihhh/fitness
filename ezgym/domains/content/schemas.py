"""content 域 marshmallow schemas（请求校验 + 响应序列化）。

- 序列化：BlogSchema（ORM -> dict，去掉 is_deleted）。
- 请求校验：BlogCreateSchema / BlogListQuerySchema，继承 BaseInputSchema。
"""
from marshmallow import fields, validate

from ezgym.core.schema import BaseInputSchema, BaseSchema
from ezgym.domains.content.models import Blog

__all__ = ["BlogSchema", "BlogCreateSchema", "BlogListQuerySchema"]


class BlogSchema(BaseSchema):
    """Blog ORM 序列化。"""

    class Meta(BaseSchema.Meta):
        model = Blog
        exclude = ("is_deleted",)


class BlogCreateSchema(BaseInputSchema):
    """POST /api/blogs 入参：content 必填，title/picture 可选。"""

    title = fields.Str(required=False, allow_none=True,
                       validate=validate.Length(max=255))
    content = fields.Str(required=True, validate=validate.Length(min=1))
    picture = fields.Str(required=False, allow_none=True,
                         validate=validate.Length(max=255))


class BlogListQuerySchema(BaseInputSchema):
    """GET /api/blogs 查询参数：scope 决定列表口径。"""

    scope = fields.Str(
        load_default="latest",
        validate=validate.OneOf(["latest", "following", "user"]),
    )
    user_id = fields.Int(required=False, allow_none=True)
    cursor = fields.Int(required=False, allow_none=True)
    limit = fields.Int(required=False, allow_none=True)
