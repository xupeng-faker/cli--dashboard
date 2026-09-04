# Copyright 2026 Huawei Technologies Co., Ltd. All rights reserved
"""
基于事件列表的聚合计算（mock 数据使用）。
"""
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Sequence

from app.services.query import EventQuery
from app.utils.timeutil import TZ_SHANGHAI, add_months

SUCCESS = "success"


def event_matches(
    event: Dict[str, Any],
    query: EventQuery,
    *,
    ignore_dimension: bool = False,
    ignore_time: bool = False,
) -> bool:
    if not ignore_time and not (query.start <= event["event_time"] < query.end):
        return False
    if ignore_dimension:
        return True
    if query.domain and event.get("domain") != query.domain:
        return False
    if query.platform and event.get("platform") != query.platform:
        return False
    if query.environment and event.get("environment") != query.environment:
        return False
    if query.result and event.get("result") != query.result:
        return False
    if query.command_name and event.get("command_name") != query.command_name:
        return False
    if query.user_id and event.get("user_id") != query.user_id:
        return False
    if query.input_source and event.get("input_source") != query.input_source:
        return False
    if query.keyword:
        keyword = query.keyword.lower()
        haystack = " ".join(
            [
                str(event.get("command") or ""),
                str(event.get("command_name") or ""),
                str(event.get("event_id") or ""),
                str(event.get("user_id") or ""),
                str(event.get("user_cn_name") or ""),
            ]
        ).lower()
        if keyword not in haystack:
            return False
    return True


def filter_events(
    events: Sequence[Dict[str, Any]],
    query: EventQuery,
    *,
    ignore_dimension: bool = False,
    ignore_time: bool = False,
) -> List[Dict[str, Any]]:
    return [
        event
        for event in events
        if event_matches(event, query, ignore_dimension=ignore_dimension, ignore_time=ignore_time)
    ]


def _percentile(values: List[float], pct: float) -> Optional[float]:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    rank = (len(ordered) - 1) * pct
    low = int(rank)
    high = min(low + 1, len(ordered) - 1)
    weight = rank - low
    return ordered[low] * (1 - weight) + ordered[high] * weight


def compute_metrics(events: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(events)
    users = {event["user_id"] for event in events}
    success_count = sum(1 for event in events if event["result"] == SUCCESS)
    failure_count = sum(1 for event in events if event["result"] == "failure")
    durations = [float(event["duration_ms"]) for event in events]
    api_durations = [float(event["api_duration_ms"]) for event in events if event.get("api_duration_ms") is not None]
    avg_duration = sum(durations) / total if total else 0
    avg_api = sum(api_durations) / len(api_durations) if api_durations else 0
    return {
        "total_calls": total,
        "unique_users": len(users),
        "success_count": success_count,
        "failure_count": failure_count,
        "success_rate": (success_count / total * 100) if total else 0,
        "avg_duration_ms": avg_duration,
        "avg_api_duration_ms": avg_api,
        "p50_duration_ms": _percentile(durations, 0.5) or 0,
        "p95_duration_ms": _percentile(durations, 0.95) or 0,
    }


def _bucket_start(event_time: datetime, granularity: str) -> datetime:
    local = event_time.astimezone(TZ_SHANGHAI)
    if granularity == "hour":
        return local.replace(minute=0, second=0, microsecond=0)
    if granularity == "week":
        monday = local - timedelta(days=local.weekday())
        return monday.replace(hour=0, minute=0, second=0, microsecond=0)
    if granularity == "month":
        return local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return local.replace(hour=0, minute=0, second=0, microsecond=0)


def _next_bucket(cursor: datetime, granularity: str) -> datetime:
    if granularity == "hour":
        return cursor + timedelta(hours=1)
    if granularity == "week":
        return cursor + timedelta(days=7)
    if granularity == "month":
        return add_months(cursor, 1)
    return cursor + timedelta(days=1)


def iter_buckets(start: datetime, end: datetime, granularity: str) -> List[datetime]:
    cursor = _bucket_start(start, granularity)
    buckets = []
    while cursor < end:
        buckets.append(cursor)
        cursor = _next_bucket(cursor, granularity)
    return buckets


def compute_trend(events: Sequence[Dict[str, Any]], query: EventQuery) -> List[Dict[str, Any]]:
    granularity = query.granularity
    grouped: Dict[datetime, List[Dict[str, Any]]] = defaultdict(list)
    for event in events:
        grouped[_bucket_start(event["event_time"], granularity)].append(event)
    rows = []
    for bucket in iter_buckets(query.start, query.end, granularity):
        bucket_events = grouped.get(bucket, [])
        metrics = compute_metrics(bucket_events)
        rows.append(
            {
                "bucket": bucket.isoformat(),
                "calls": metrics["total_calls"],
                "users": metrics["unique_users"],
                "success_rate": metrics["success_rate"],
                "avg_duration_ms": metrics["avg_duration_ms"],
                "avg_api_duration_ms": metrics["avg_api_duration_ms"],
            }
        )
    return rows


def count_by(events: Sequence[Dict[str, Any]], key: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for event in events:
        grouped[str(event.get(key) or "unknown")].append(event)
    rows = []
    for name, group in grouped.items():
        metrics = compute_metrics(group)
        rows.append({"name": name, **metrics})
    rows.sort(key=lambda item: item["total_calls"], reverse=True)
    if limit is not None:
        return rows[:limit]
    return rows


def command_stats(events: Sequence[Dict[str, Any]], limit: int = 30) -> List[Dict[str, Any]]:
    grouped: Dict[tuple, List[Dict[str, Any]]] = defaultdict(list)
    for event in events:
        grouped[(event["domain"], event.get("platform") or "", event["command"], event["command_name"])].append(event)
    rows = []
    for (domain, platform, command, command_name), group in grouped.items():
        metrics = compute_metrics(group)
        rows.append(
            {
                "domain": domain,
                "platform": platform,
                "command": command,
                "command_name": command_name,
                **metrics,
            }
        )
    rows.sort(key=lambda item: item["total_calls"], reverse=True)
    return rows[:limit]


def user_stats(events: Sequence[Dict[str, Any]], limit: int = 30) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for event in events:
        grouped[event["user_id"]].append(event)
    rows = []
    for user_id, group in grouped.items():
        sample = group[0]
        metrics = compute_metrics(group)
        last_seen = max(item["event_time"] for item in group)
        rows.append(
            {
                "user_id": user_id,
                "user_cn_name": sample["user_cn_name"],
                "org_dept_name4": sample.get("org_dept_name4"),
                "org_dept_name5": sample.get("org_dept_name5"),
                "last_seen": last_seen.isoformat(),
                **metrics,
            }
        )
    rows.sort(key=lambda item: item["total_calls"], reverse=True)
    return rows[:limit]


def dept_stats(events: Sequence[Dict[str, Any]], key: str = "org_dept_name4") -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for event in events:
        grouped[str(event.get(key) or "未填写部门")].append(event)
    rows = []
    for name, group in grouped.items():
        metrics = compute_metrics(group)
        rows.append({"name": name, **metrics})
    rows.sort(key=lambda item: item["total_calls"], reverse=True)
    return rows


def error_category_stats(events: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    failed = [event for event in events if event.get("error_category")]
    return count_by(failed, "error_category")


def error_code_stats(events: Sequence[Dict[str, Any]], limit: int = 15) -> List[Dict[str, Any]]:
    failed = [event for event in events if event.get("error_code")]
    return count_by(failed, "error_code", limit=limit)


def slow_commands(events: Sequence[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
    rows = command_stats(events, limit=200)
    rows.sort(key=lambda item: item["p95_duration_ms"], reverse=True)
    return rows[:limit]


def duration_buckets(events: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    edges = [0, 200, 500, 1000, 2000, 5000, 10000, 30000]
    labels = ["<200ms", "200-500ms", "500ms-1s", "1-2s", "2-5s", "5-10s", "10-30s", ">=30s"]
    counts = [0] * len(labels)
    for event in events:
        duration = event["duration_ms"]
        placed = False
        for index in range(len(edges) - 1):
            if edges[index] <= duration < edges[index + 1]:
                counts[index] += 1
                placed = True
                break
        if not placed:
            counts[-1] += 1
    return [{"name": label, "total_calls": count} for label, count in zip(labels, counts)]


def distinct_values(events: Iterable[Dict[str, Any]], key: str) -> List[str]:
    values = sorted({str(event.get(key)) for event in events if event.get(key)})
    return values
