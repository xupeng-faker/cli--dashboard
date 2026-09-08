# Copyright 2026 Huawei Technologies Co., Ltd. All rights reserved
"""
看板查询入参校验。
"""
from datetime import datetime
from typing import Optional, Tuple

from app.services.query import EventQuery
from app.utils.errors import ValidationError
from app.utils.timeutil import TZ_SHANGHAI, clamp_to_data_start, default_range, now_shanghai

__all__ = ["parse_int", "parse_limit_offset", "parse_event_query"]


def parse_int(value: Optional[str], field_name: str, min_value: int, max_value: int) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValidationError("Invalid parameter", payload={"field": field_name}) from exc
    if parsed < min_value or parsed > max_value:
        raise ValidationError("Invalid parameter", payload={"field": field_name})
    return parsed


def parse_limit_offset(limit: Optional[str], offset: Optional[str]) -> Tuple[int, int]:
    parsed_limit = parse_int(limit, "limit", 1, 100)
    parsed_offset = parse_int(offset, "offset", 0, 1_000_000)
    return (parsed_limit or 20, parsed_offset or 0)


def _parse_datetime(value: Optional[str], field_name: str) -> Optional[datetime]:
    if value is None or value == "":
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValidationError("Invalid datetime", payload={"field": field_name}) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=TZ_SHANGHAI)
    return parsed.astimezone(TZ_SHANGHAI)


_ALLOWED_GRANULARITY = {"hour", "day", "week", "month"}


def _parse_granularity(value: Optional[str]) -> Optional[str]:
    if value is None or value == "":
        return None
    text = str(value).strip().lower()
    if text not in _ALLOWED_GRANULARITY:
        raise ValidationError("Invalid parameter", payload={"field": "granularity"})
    return text


def _parse_bool(value: Optional[str], field_name: str) -> bool:
    if value is None or value == "":
        return False
    text = str(value).strip().lower()
    if text in ("1", "true", "yes", "on"):
        return True
    if text in ("0", "false", "no", "off"):
        return False
    raise ValidationError("Invalid parameter", payload={"field": field_name})


def parse_event_query(args) -> EventQuery:
    default_start, default_end = default_range()
    start = clamp_to_data_start(_parse_datetime(args.get("start"), "start") or default_start)
    end = _parse_datetime(args.get("end"), "end") or default_end
    if end <= start:
        raise ValidationError("Invalid time range", payload={"field": "end"})
    max_span_days = 4000
    if (end - start).days > max_span_days:
        raise ValidationError("Time range too large", payload={"max_days": max_span_days})
    if end > now_shanghai().replace(hour=23, minute=59, second=59, microsecond=999999):
        end = now_shanghai()

    def _opt(name: str, max_length: int) -> Optional[str]:
        raw = args.get(name)
        if raw is None:
            return None
        text = str(raw).strip()
        if not text:
            return None
        if len(text) > max_length:
            raise ValidationError("Invalid parameter", payload={"field": name})
        return text

    return EventQuery(
        start=start,
        end=end,
        domain=_opt("domain", 64),
        platform=_opt("platform", 64),
        environment=_opt("environment", 32),
        result=_opt("result", 32),
        command_name=_opt("command_name", 64),
        user_id=_opt("user_id", 64),
        keyword=_opt("keyword", 128),
        input_source=_opt("input_source", 32),
        granularity_override=_parse_granularity(args.get("granularity")),
        cumulative=_parse_bool(args.get("cumulative"), "cumulative"),
    )
