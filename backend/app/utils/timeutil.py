# Copyright 2026 Huawei Technologies Co., Ltd. All rights reserved
"""
时区与时间范围工具。
"""
from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

TZ_SHANGHAI = ZoneInfo("Asia/Shanghai")

__all__ = [
    "TZ_SHANGHAI",
    "now_shanghai",
    "as_aware",
    "to_iso",
    "pick_granularity",
    "start_of_month",
    "add_months",
    "calendar_month_bounds",
]


def now_shanghai() -> datetime:
    return datetime.now(TZ_SHANGHAI)


def as_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def to_iso(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return as_aware(value).isoformat()


def start_of_month(value: datetime) -> datetime:
    local = as_aware(value).astimezone(TZ_SHANGHAI)
    return local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def add_months(value: datetime, months: int) -> datetime:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    return value.replace(year=year, month=month)


def calendar_month_bounds(value: datetime, months_ago: int = 0) -> tuple[datetime, datetime]:
    start = add_months(start_of_month(value), -months_ago)
    end = add_months(start, 1)
    return start, end


def pick_granularity(start: datetime, end: datetime) -> str:
    hours = max((end - start).total_seconds() / 3600, 1)
    if hours <= 24 * 45:
        return "day"
    return "month"


def default_range() -> tuple[datetime, datetime]:
    end = now_shanghai()
    start = datetime(2020, 1, 1, tzinfo=TZ_SHANGHAI)
    return start, end
