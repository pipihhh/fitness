"""course 域 marshmallow schemas（请求校验 + 响应序列化）。

- 序列化：CourseSchema / ActionSchema（ORM -> dict，去掉 is_deleted）。
- 请求校验：CourseCreateSchema / CourseUpdateSchema / ActionCreateSchema /
  CollectionCreateSchema，均继承 BaseInputSchema（unknown=EXCLUDE）。
"""
from marshmallow import fields, validate

from ezgym.core.schema import BaseInputSchema, BaseSchema
from ezgym.domains.course.models import Course, CourseAction

__all__ = [
    "CourseSchema",
    "ActionSchema",
    "CourseCreateSchema",
    "CourseUpdateSchema",
    "ActionCreateSchema",
    "CollectionCreateSchema",
]


class CourseSchema(BaseSchema):
    """Course ORM 序列化。"""

    class Meta(BaseSchema.Meta):
        model = Course
        exclude = ("is_deleted",)


class ActionSchema(BaseSchema):
    """CourseAction ORM 序列化。"""

    class Meta(BaseSchema.Meta):
        model = CourseAction
        exclude = ("is_deleted",)


class CourseCreateSchema(BaseInputSchema):
    """POST /api/courses 入参：name 必填，其余可选。"""

    name = fields.Str(required=True, validate=validate.Length(min=1, max=128))
    type = fields.Str(required=False, allow_none=True)
    level = fields.Str(required=False, allow_none=True)
    burning = fields.Int(required=False, allow_none=True)


class CourseUpdateSchema(BaseInputSchema):
    """PUT /api/courses/{id} 入参：全部可选（任意子集）。"""

    name = fields.Str(validate=validate.Length(min=1, max=128))
    type = fields.Str(allow_none=True)
    level = fields.Str(allow_none=True)
    burning = fields.Int(allow_none=True)


class ActionCreateSchema(BaseInputSchema):
    """POST /api/courses/{id}/actions 入参：sequence 必填。"""

    content = fields.Str(required=False, allow_none=True)
    picture = fields.Str(required=False, allow_none=True)
    sequence = fields.Int(required=True)


class CollectionCreateSchema(BaseInputSchema):
    """POST /api/collections 入参。"""

    course_id = fields.Int(required=True)
