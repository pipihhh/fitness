"""challenge 域 service（业务逻辑 + 事务边界）。

- 列表游标分页（core.pagination）。
- 创建：日期 "YYYY-MM-DD" 解析为 datetime，number 自动生成唯一号。
- pageviews 原子自增：用 `Challenge.pageviews + 1` 表达式做单条 UPDATE，
  避免读改写竞态（修 CR #20）；GET 详情不再触碰 pageviews。
"""
import uuid
from datetime import datetime

from sqlalchemy import select, update

from ezgym.core.database import db
from ezgym.core.errors import BadRequest, NotFound
from ezgym.core.pagination import Page, cursor_paginate
from ezgym.core.service import BaseService
from ezgym.domains.challenge.models import Challenge

__all__ = ["ChallengeService"]


class ChallengeService(BaseService[Challenge]):
    model = Challenge

    DATE_FORMAT = "%Y-%m-%d"

    # ---------- helpers ----------
    @classmethod
    def _parse_date(cls, value) -> datetime | None:
        """把 "YYYY-MM-DD" 解析为 datetime；空值返回 None，非法格式 400。"""
        if value in (None, ""):
            return None
        if isinstance(value, datetime):
            return value
        try:
            return datetime.strptime(value, cls.DATE_FORMAT)
        except (ValueError, TypeError):
            raise BadRequest("日期格式应为 YYYY-MM-DD")

    @staticmethod
    def _generate_number() -> str:
        """生成业务唯一号（32 位十六进制）。"""
        return uuid.uuid4().hex

    # ---------- 查询 ----------
    @classmethod
    def list_challenges(cls, cursor: int | None, limit: int | None) -> Page:
        return cursor_paginate(cls.base_query(), cursor, limit, Challenge.id)

    # ---------- 写入 ----------
    @classmethod
    def create_challenge(
        cls,
        *,
        picture: str | None = None,
        content: str | None = None,
        start_time=None,
        end_time=None,
    ) -> Challenge:
        return cls.create(
            picture=picture,
            content=content,
            start_time=cls._parse_date(start_time),
            end_time=cls._parse_date(end_time),
            number=cls._generate_number(),
        )

    @classmethod
    def update_challenge(cls, obj: Challenge, **fields) -> Challenge:
        """按传入子集更新；start_time/end_time 若在子集内则解析为 datetime。"""
        data: dict = {}
        for key in ("picture", "content"):
            if key in fields:
                data[key] = fields[key]
        for key in ("start_time", "end_time"):
            if key in fields:
                data[key] = cls._parse_date(fields[key])
        return cls.update(obj, **data)

    @classmethod
    def increment_pageviews(cls, challenge_id: int) -> int:
        """原子自增 pageviews 并返回最新值。

        用 `pageviews = pageviews + 1` 的表达式 UPDATE，把自增下推到数据库，
        避免"读-改-写"竞态（修 CR #20 的竞态部分）。
        """
        result = db.session.execute(
            update(Challenge)
            .where(Challenge.id == challenge_id, Challenge.is_deleted.is_(False))
            .values(pageviews=Challenge.pageviews + 1)
        )
        if result.rowcount == 0:
            db.session.rollback()
            raise NotFound("挑战不存在")
        db.session.commit()
        return db.session.execute(
            select(Challenge.pageviews).where(Challenge.id == challenge_id)
        ).scalar_one()
