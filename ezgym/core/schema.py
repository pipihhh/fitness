"""Schema 基类。

统一 marshmallow 配置：ORM 序列化用 BaseSchema（SQLAlchemyAutoSchema），
纯请求校验用 BaseInputSchema（普通 Schema）。datetime 由 ma 默认按 ISO 序列化。
"""
from marshmallow import EXCLUDE

from ezgym.extensions import db, ma

__all__ = ["BaseSchema", "BaseInputSchema"]


class BaseSchema(ma.SQLAlchemyAutoSchema):
    """ORM -> dict 序列化基类。子类在 Meta 里指定 model。"""

    class Meta:
        sqla_session = db.session
        load_instance = False
        include_fk = True
        unknown = EXCLUDE


class BaseInputSchema(ma.Schema):
    """请求参数校验基类。忽略未知字段，避免多余入参报错。"""

    class Meta:
        unknown = EXCLUDE
