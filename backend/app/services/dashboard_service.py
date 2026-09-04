# Copyright 2026 Huawei Technologies Co., Ltd. All rights reserved
"""
看板聚合服务。
"""
from dataclasses import replace
from typing import Any, Dict, Optional

from flask import current_app

from app.services.gauss_repository import GaussRepository
from app.services.mock_repository import MockRepository
from app.services.query import EventQuery, lifetime_query, month_query
from app.utils.timeutil import as_aware, to_iso

__all__ = [
    "get_repository",
    "get_overview",
    "get_commands",
    "get_users",
    "get_quality",
    "get_events",
    "get_filter_options",
]


def get_repository():
    if current_app.config.get("USE_MOCK"):
        return MockRepository()
    return GaussRepository()


def _round(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 2)
    return value


def _kpi(
    current: Any,
    previous: Any,
    *,
    hint: Optional[str] = None,
    compare_label: str = "较上周期",
) -> Dict[str, Any]:
    current_value = _round(current or 0)
    previous_value = _round(previous or 0)
    change = None
    if hint is None:
        if previous:
            change = round((float(current or 0) - float(previous)) / float(previous) * 100, 1)
        elif current:
            change = 100.0
    payload = {
        "value": current_value,
        "prev": previous_value,
        "change_pct": change,
        "compare_label": compare_label,
    }
    if hint:
        payload["hint"] = hint
    return payload


def _range_meta(query: EventQuery) -> Dict[str, Any]:
    return {
        "start": to_iso(query.start),
        "end": to_iso(query.end),
        "granularity": query.granularity,
    }


def _effective_query(repo, query: EventQuery) -> EventQuery:
    earliest = repo.earliest_time(query)
    if earliest is None:
        return query
    earliest = as_aware(earliest)
    if query.start < earliest:
        return replace(query, start=earliest)
    return query


def get_overview(query: EventQuery) -> Dict[str, Any]:
    repo = get_repository()
    chart_query = _effective_query(repo, query)
    lifetime = repo.metrics(lifetime_query(query))
    this_month = repo.metrics(month_query(query, 0))
    last_month = repo.metrics(month_query(query, 1))
    return {
        "data_source": repo.source,
        "range": _range_meta(chart_query),
        "kpis": {
            "total_calls": _kpi(lifetime["total_calls"], None, hint="历史累计"),
            "mau": _kpi(this_month["unique_users"], last_month["unique_users"], compare_label="较上月"),
            "month_calls": _kpi(this_month["total_calls"], last_month["total_calls"], compare_label="较上月"),
            "success_rate": _kpi(this_month["success_rate"], last_month["success_rate"], compare_label="较上月"),
            "avg_duration_ms": _kpi(this_month["avg_duration_ms"], last_month["avg_duration_ms"], compare_label="较上月"),
            "p95_duration_ms": _kpi(this_month["p95_duration_ms"], last_month["p95_duration_ms"], compare_label="较上月"),
        },
        "trend": repo.trend(chart_query),
        "result_dist": repo.distribution(chart_query, "result"),
        "domain_dist": repo.distribution(chart_query, "domain"),
        "platform_dist": repo.distribution(chart_query, "platform"),
        "input_source_dist": repo.distribution(chart_query, "input_source"),
        "dept5_dist": repo.departments(chart_query, field="org_dept_name5"),
        "top_commands": repo.commands(chart_query, limit=10),
    }


def get_commands(query: EventQuery) -> Dict[str, Any]:
    repo = get_repository()
    return {
        "data_source": repo.source,
        "range": _range_meta(query),
        "commands": repo.commands(query, limit=40),
        "cli_versions": repo.distribution(query, "cli_version"),
        "output_formats": repo.distribution(query, "output_format"),
        "input_sources": repo.distribution(query, "input_source"),
        "domains": repo.distribution(query, "domain"),
    }


def get_users(query: EventQuery) -> Dict[str, Any]:
    repo = get_repository()
    return {
        "data_source": repo.source,
        "range": _range_meta(query),
        "users": repo.users(query, limit=40),
        "departments": repo.departments(query),
        "environments": repo.distribution(query, "environment"),
        "trend": repo.trend(query),
    }


def get_quality(query: EventQuery) -> Dict[str, Any]:
    repo = get_repository()
    return {
        "data_source": repo.source,
        "range": _range_meta(query),
        "metrics": repo.metrics(query),
        "trend": repo.trend(query),
        "error_categories": repo.error_categories(query),
        "error_codes": repo.error_codes(query),
        "slow_commands": repo.slow_commands(query),
        "duration_histogram": repo.duration_histogram(query),
    }


def get_events(query: EventQuery, limit: int, offset: int) -> Dict[str, Any]:
    repo = get_repository()
    items, total = repo.events(query, limit=limit, offset=offset)
    return {
        "data_source": repo.source,
        "range": _range_meta(query),
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


def get_filter_options(query: EventQuery) -> Dict[str, Any]:
    repo = get_repository()
    return {
        "data_source": repo.source,
        **repo.filter_options(query),
    }
