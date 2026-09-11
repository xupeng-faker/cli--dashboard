# Copyright 2026 Huawei Technologies Co., Ltd. All rights reserved
"""
看板聚合服务。
"""
from dataclasses import replace
from typing import Any, Dict, Optional

from flask import current_app

from app.services.gauss_repository import GaussRepository
from app.services.mock_repository import MockRepository
from app.services.query import EventQuery, lifetime_query, month_query, previous_month_to_date_query
from app.utils.timeutil import as_aware, clamp_to_data_start, to_iso

__all__ = [
    "get_repository",
    "get_overview",
    "get_commands",
    "get_users",
    "get_departments",
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
        previous_number = float(previous or 0)
        current_number = float(current or 0)
        if previous_number:
            change = round((current_number - previous_number) / previous_number * 100, 1)
        elif current_number:
            hint = "上期无数据"
        else:
            change = 0.0
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
        "cumulative": query.cumulative,
    }


def _clamped_query(query: EventQuery) -> EventQuery:
    start = clamp_to_data_start(query.start)
    if start != query.start:
        return replace(query, start=start)
    return query


def _first_data_query(repo, query: EventQuery) -> EventQuery:
    window = _clamped_query(query)
    earliest = repo.earliest_time(window)
    if earliest is None:
        return window
    earliest = as_aware(earliest)
    if window.start < earliest:
        return replace(window, start=earliest)
    return window


def get_overview(query: EventQuery) -> Dict[str, Any]:
    repo = get_repository()
    chart_query = _first_data_query(repo, query)
    lifetime_range = lifetime_query(query)
    this_month_range = month_query(query, 0)
    lifetime = repo.metrics(lifetime_range)
    month_start_lifetime = repo.metrics(replace(lifetime_range, end=this_month_range.start))
    this_month = repo.metrics(this_month_range)
    last_month = repo.metrics(previous_month_to_date_query(query))
    new_users = repo.new_users(month_query(query, 0))
    previous_new_users = repo.new_users(previous_month_to_date_query(query))
    return {
        "data_source": repo.source,
        "range": _range_meta(chart_query),
        "kpis": {
            "total_calls": _kpi(
                lifetime["total_calls"],
                month_start_lifetime["total_calls"],
                compare_label="较本月初",
            ),
            "total_users": _kpi(
                lifetime["unique_users"],
                month_start_lifetime["unique_users"],
                compare_label="较本月初",
            ),
            "mau": _kpi(this_month["unique_users"], last_month["unique_users"], compare_label="较上月同期"),
            "new_users": _kpi(new_users, previous_new_users, compare_label="较上月同期"),
            "month_calls": _kpi(this_month["total_calls"], last_month["total_calls"], compare_label="较上月同期"),
            "avg_calls_per_user": _kpi(
                this_month["total_calls"] / this_month["unique_users"] if this_month["unique_users"] else 0,
                last_month["total_calls"] / last_month["unique_users"] if last_month["unique_users"] else 0,
                compare_label="较上月同期",
            ),
        },
        "trend": repo.trend(chart_query),
        "result_dist": repo.distribution(chart_query, "result"),
        "domain_dist": repo.distribution(chart_query, "domain"),
        "platform_dist": repo.distribution(chart_query, "platform"),
        "input_source_dist": repo.distribution(chart_query, "input_source"),
        "dept4_dist": repo.departments(chart_query, field="org_dept_name4"),
        "top_commands": repo.commands(chart_query, limit=10),
    }


def get_commands(query: EventQuery) -> Dict[str, Any]:
    repo = get_repository()
    chart_query = _first_data_query(repo, query)
    return {
        "data_source": repo.source,
        "range": _range_meta(chart_query),
        "commands": repo.commands(chart_query, limit=40),
        "cli_versions": repo.distribution(chart_query, "cli_version"),
        "output_formats": repo.distribution(chart_query, "output_format"),
        "input_sources": repo.distribution(chart_query, "input_source"),
        "domains": repo.distribution(chart_query, "domain"),
    }


def get_users(query: EventQuery) -> Dict[str, Any]:
    repo = get_repository()
    chart_query = _first_data_query(repo, query)
    return {
        "data_source": repo.source,
        "range": _range_meta(chart_query),
        "users": repo.users(chart_query, limit=40),
        "departments": repo.departments(chart_query),
        "environments": repo.distribution(chart_query, "environment"),
        "trend": repo.trend(chart_query),
    }


def get_departments(
    query: EventQuery,
    level: int,
    dept4: Optional[str] = None,
    dept5: Optional[str] = None,
) -> Dict[str, Any]:
    repo = get_repository()
    return {
        "data_source": repo.source,
        "range": _range_meta(query),
        "level": level,
        "dept4": dept4,
        "dept5": dept5,
        "departments": repo.departments(
            query,
            field=f"org_dept_name{level}",
            dept4=dept4,
            dept5=dept5,
        ),
    }


def get_quality(query: EventQuery) -> Dict[str, Any]:
    repo = get_repository()
    chart_query = _first_data_query(repo, query)
    return {
        "data_source": repo.source,
        "range": _range_meta(chart_query),
        "metrics": repo.metrics(chart_query),
        "trend": repo.trend(chart_query),
        "error_categories": repo.error_categories(chart_query),
        "error_codes": repo.error_codes(chart_query),
        "duration_histogram": repo.duration_histogram(chart_query),
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
