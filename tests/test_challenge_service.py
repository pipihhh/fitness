"""challenge 域 service 单测：原子自增、日期解析、title 截取、number 唯一。"""
from datetime import datetime

import pytest

from ezgym.core.errors import BadRequest, NotFound
from ezgym.domains.challenge.schemas import ChallengeListItemSchema
from ezgym.domains.challenge.service import ChallengeService


def test_create_parses_date_string_to_datetime(app):
    obj = ChallengeService.create_challenge(
        content="七日打卡挑战",
        start_time="2026-01-01",
        end_time="2026-01-07",
    )
    assert isinstance(obj.start_time, datetime)
    assert (obj.start_time.year, obj.start_time.month, obj.start_time.day) == (2026, 1, 1)
    assert isinstance(obj.end_time, datetime)
    assert (obj.end_time.year, obj.end_time.month, obj.end_time.day) == (2026, 1, 7)


def test_create_invalid_date_raises_bad_request(app):
    with pytest.raises(BadRequest):
        ChallengeService.create_challenge(
            content="x", start_time="2026/01/01", end_time="2026-01-07"
        )


def test_create_generates_unique_number(app):
    a = ChallengeService.create_challenge(content="a", start_time="2026-01-01", end_time="2026-01-07")
    b = ChallengeService.create_challenge(content="b", start_time="2026-01-01", end_time="2026-01-07")
    assert a.number and b.number
    assert a.number != b.number


def test_increment_pageviews_is_atomic_and_returns_latest(app):
    obj = ChallengeService.create_challenge(content="c", start_time="2026-01-01", end_time="2026-01-07")
    assert obj.pageviews == 0
    assert ChallengeService.increment_pageviews(obj.id) == 1
    assert ChallengeService.increment_pageviews(obj.id) == 2
    # 重新读取确认落库
    assert ChallengeService.get(obj.id).pageviews == 2


def test_increment_pageviews_missing_raises_not_found(app):
    with pytest.raises(NotFound):
        ChallengeService.increment_pageviews(999999)


def test_list_item_title_truncated_to_config_length(app):
    length = app.config["TITLE_LENGTH"]
    content = "一" * (length + 5)
    obj = ChallengeService.create_challenge(content=content, start_time="2026-01-01", end_time="2026-01-07")
    dumped = ChallengeListItemSchema().dump(obj)
    assert dumped["title"] == content[:length]
    assert len(dumped["title"]) == length


def test_update_parses_only_provided_date_fields(app):
    obj = ChallengeService.create_challenge(content="c", start_time="2026-01-01", end_time="2026-01-07")
    updated = ChallengeService.update_challenge(obj, content="new", end_time="2026-02-01")
    assert updated.content == "new"
    assert (updated.end_time.year, updated.end_time.month, updated.end_time.day) == (2026, 2, 1)
    # start_time 未传，保持原值
    assert (updated.start_time.year, updated.start_time.month, updated.start_time.day) == (2026, 1, 1)
