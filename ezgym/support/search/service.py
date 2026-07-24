"""search 域 service（跨域读，无自有表）。

搜索属 support 层，读 content 数据一律经 content_service.search_blogs（参数化查询，
修 CR #2），不直连 content 的 model、不拼 SQL。
"""
from ezgym.core.pagination import Page

__all__ = ["SearchService", "search_blogs"]


class SearchService:
    """搜索聚合。目前仅支持 type=blog。"""

    @staticmethod
    def search_blogs(q: str, cursor: int | None, limit: int | None) -> Page:
        # 惰性 import：content 是领域域，search 是 support 域，运行期调用其暴露函数
        from ezgym.domains.content import service as content_service
        return content_service.search_blogs(q, cursor, limit)


def search_blogs(q: str, cursor: int | None, limit: int | None) -> Page:
    return SearchService.search_blogs(q, cursor, limit)
