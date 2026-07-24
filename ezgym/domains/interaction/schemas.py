"""interaction 域 marshmallow schemas（请求校验）。

评论/回复的展示昵称经 identity.service 实时取，模型无冗余 nick_name，故这里主要做入参校验。
"""
from marshmallow import fields, validate

from ezgym.core.schema import BaseInputSchema

__all__ = ["CommentCreateSchema", "ReplyCreateSchema"]


class CommentCreateSchema(BaseInputSchema):
    """POST /api/comments 入参。"""

    blog_id = fields.Int(required=True)
    content = fields.Str(required=True, validate=validate.Length(min=1))


class ReplyCreateSchema(BaseInputSchema):
    """POST /api/replies 入参：reply_id 可选（回复某条 reply）。"""

    comment_id = fields.Int(required=True)
    content = fields.Str(required=True, validate=validate.Length(min=1))
    reply_id = fields.Int(required=False, allow_none=True)
