# Copyright 2026 Huawei Technologies Co., Ltd. All rights reserved
"""
看板查询条件。
"""
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Optional

from app.utils.timeutil import DATA_START, calendar_month_bounds, now_shanghai, pick_granularity

__all__ = [
    "EventQuery",
    "previous_query",
    "lifetime_query",
    "month_query",
    "previous_month_to_date_query",
]

LIFETIME_START = DATA_START


@dataclass
class EventQuery:
    start: datetime
    end: datetime
    domain: Optional[str] = None
    platform: Optional[str] = None
    environment: Optional[str] = None
    result: Optional[str] = None
    command_name: Optional[str] = None
    user_id: Optional[str] = None
    keyword: Optional[str] = None
    input_source: Optional[str] = None
    granularity_override: Optional[str] = None
    cumulative: bool = False

    @property
    def granularity(self) -> str:
        if self.granularity_override in ("hour", "day", "week", "month"):
            return self.granularity_override
        return pick_granularity(self.start, self.end)


def previous_query(query: EventQuery) -> EventQuery:
    delta = query.end - query.start
    return replace(query, start=query.start - delta, end=query.start)


def lifetime_query(query: EventQuery) -> EventQuery:
    return replace(query, start=LIFETIME_START, end=now_shanghai())


def month_query(query: EventQuery, months_ago: int = 0) -> EventQuery:
    start, end = calendar_month_bounds(now_shanghai(), months_ago)
    if months_ago == 0:
        end = now_shanghai()
    return replace(query, start=start, end=end)


def previous_month_to_date_query(query: EventQuery) -> EventQuery:
    now = now_shanghai()
    current_start, _ = calendar_month_bounds(now, 0)
    previous_start, previous_end = calendar_month_bounds(now, 1)
    previous_same_time = previous_start + (now - current_start)
    return replace(query, start=previous_start, end=min(previous_same_time, previous_end))
