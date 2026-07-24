"""identity 域 marshmallow schemas（请求校验 + 响应序列化）。

请求校验统一继承 BaseInputSchema（unknown=EXCLUDE：多余入参自动忽略，
因此前端即便传 permission 提权也会被丢弃）。校验失败由全局 error handler
统一转 400。
"""
from marshmallow import fields, validate

from ezgym.core.schema import BaseInputSchema

__all__ = [
    "RegisterSchema",
    "LoginSchema",
    "PasswordResetRequestSchema",
    "PasswordResetConfirmSchema",
    "UpdateProfileSchema",
    "ChangePasswordSchema",
]


class RegisterSchema(BaseInputSchema):
    """注册入参。permission 不在字段列表里 -> 被 EXCLUDE 丢弃，前端无法提权。"""

    account = fields.Str(required=True, validate=validate.Length(min=3, max=64))
    password = fields.Str(required=True, validate=validate.Length(min=6, max=128))
    nick_name = fields.Str(required=True, validate=validate.Length(min=1, max=64))
    phone = fields.Str(validate=validate.Length(max=20))
    gender = fields.Int()
    age = fields.Int(validate=validate.Range(min=0, max=150))
    email = fields.Email(validate=validate.Length(max=128))
    description = fields.Str()
    avatar = fields.Str(validate=validate.Length(max=255))


class LoginSchema(BaseInputSchema):
    """登录入参：先验证码后密码，密码走 body（修 CR #16）。"""

    account = fields.Str(required=True)
    password = fields.Str(required=True)
    captcha_code = fields.Str(required=True)


class PasswordResetRequestSchema(BaseInputSchema):
    """发起找回密码：只需邮箱。"""

    email = fields.Email(required=True)


class PasswordResetConfirmSchema(BaseInputSchema):
    """确认改密：token + 新密码。email/uid 可选（token 内已含身份）。"""

    token = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=validate.Length(min=6, max=128))
    email = fields.Email()
    uid = fields.Int()


class UpdateProfileSchema(BaseInputSchema):
    """改本人资料：全部字段可选，仅更新出现的键（缺省不动）。

    avatar 只做长度校验、不校验文件是否存在（修 CR #15：回传原头像不应报错）。
    """

    nick_name = fields.Str(validate=validate.Length(min=1, max=64))
    phone = fields.Str(validate=validate.Length(max=20))
    gender = fields.Int()
    age = fields.Int(validate=validate.Range(min=0, max=150))
    email = fields.Email(validate=validate.Length(max=128))
    description = fields.Str()
    avatar = fields.Str(validate=validate.Length(max=255))


class ChangePasswordSchema(BaseInputSchema):
    """改密：旧密码 + 新密码。"""

    old_password = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=validate.Length(min=6, max=128))
