"""分页 helper：游标分页（基于 id）与偏移分页。

游标分页避免深翻页性能问题，是列表接口的首选；偏移分页用于管理端等需要页码的场景。
"""
from dataclasses import dataclass
from typing import Any

from flask import current_app

__all__ = ["Page", "cursor_paginate", "offset_paginate", "resolve_page_size"]


@dataclass
class Page:
    items: list[Any]
    count: int
    next_cursor: int | None = None


def resolve_page_size(size: int | None) -> int:
    """把请求传入的每页大小夹到 [1, MAX_PAGE_SIZE]，缺省用 PAGE_SIZE。"""
    default = current_app.config.get("PAGE_SIZE", 9)
    maximum = current_app.config.get("MAX_PAGE_SIZE", 100)
    if not size or size <= 0:
        return default
    return min(size, maximum)


def cursor_paginate(query, cursor: int | None, size: int | None, id_column) -> Page:
    """基于 id 游标的分页。

    :param query: 已构造好过滤/排序前的 SQLAlchemy Select/Query（这里用 Query 风格）
    :param cursor: 上一页最后一条 id；None/0 表示从头
    :param size: 每页条数
    :param id_column: 用于游标的列（通常 Model.id），按升序游标
    :return: Page(items, count, next_cursor)
    """
    limit = resolve_page_size(size)
    q = query
    if cursor:
        q = q.filter(id_column > cursor)
    items = q.order_by(id_column.asc()).limit(limit + 1).all()
    has_more = len(items) > limit
    items = items[:limit]
    next_cursor = getattr(items[-1], "id") if (has_more and items) else None
    return Page(items=items, count=len(items), next_cursor=next_cursor)


def offset_paginate(query, page: int | None, size: int | None) -> Page:
    """偏移分页。page 从 1 开始。"""
    limit = resolve_page_size(size)
    page = page if page and page > 0 else 1
    total = query.order_by(None).count()
    items = query.limit(limit).offset((page - 1) * limit).all()
    return Page(items=items, count=total)
