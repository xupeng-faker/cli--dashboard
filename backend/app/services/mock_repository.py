# Copyright 2026 Huawei Technologies Co., Ltd. All rights reserved
"""
内存样例数据仓库。
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.services.mock_data import get_mock_events
from app.services.query import EventQuery
from app.services import stats
from app.utils.timeutil import to_iso

__all__ = ["MockRepository"]


class MockRepository:
    source = "mock"

    def _rows(self, query: EventQuery, *, ignore_dimension: bool = False) -> List[Dict[str, Any]]:
        return stats.filter_events(get_mock_events(), query, ignore_dimension=ignore_dimension)

    def earliest_time(self, query: EventQuery) -> Optional[datetime]:
        rows = self._rows(query)
        if not rows:
            return None
        return min(item["event_time"] for item in rows)

    def metrics(self, query: EventQuery) -> Dict[str, Any]:
        return stats.compute_metrics(self._rows(query))

    def new_users(self, query: EventQuery) -> int:
        rows = stats.filter_events(get_mock_events(), query, ignore_time=True)
        first_seen: Dict[str, datetime] = {}
        for item in rows:
            user_id = item["user_id"]
            event_time = item["event_time"]
            if user_id not in first_seen or event_time < first_seen[user_id]:
                first_seen[user_id] = event_time
        return sum(1 for event_time in first_seen.values() if query.start <= event_time < query.end)

    def trend(self, query: EventQuery) -> List[Dict[str, Any]]:
        return stats.compute_trend(self._rows(query), query)

    def distribution(self, query: EventQuery, key: str, limit: int = 20) -> List[Dict[str, Any]]:
        return stats.count_by(self._rows(query), key, limit=limit)

    def commands(self, query: EventQuery, limit: int = 30) -> List[Dict[str, Any]]:
        return stats.command_stats(self._rows(query), limit=limit)

    def users(self, query: EventQuery, limit: int = 30) -> List[Dict[str, Any]]:
        return stats.user_stats(self._rows(query), limit=limit)

    def departments(
        self,
        query: EventQuery,
        field: str = "org_dept_name4",
        dept4: Optional[str] = None,
        dept5: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        rows = self._rows(query)
        if dept4:
            rows = [item for item in rows if item.get("org_dept_name4") == dept4]
        if dept5:
            rows = [item for item in rows if item.get("org_dept_name5") == dept5]
        return stats.dept_stats(rows, key=field)

    def error_categories(self, query: EventQuery) -> List[Dict[str, Any]]:
        return stats.error_category_stats(self._rows(query))

    def error_codes(self, query: EventQuery, limit: int = 15) -> List[Dict[str, Any]]:
        return stats.error_code_stats(self._rows(query), limit=limit)

    def duration_histogram(self, query: EventQuery) -> List[Dict[str, Any]]:
        return stats.duration_buckets(self._rows(query))

    def filter_options(self, query: EventQuery) -> Dict[str, List[str]]:
        rows = self._rows(query, ignore_dimension=True)
        return {
            "domains": stats.distinct_values(rows, "domain"),
            "platforms": stats.distinct_values(rows, "platform"),
            "environments": stats.distinct_values(rows, "environment"),
            "results": stats.distinct_values(rows, "result"),
            "command_names": stats.distinct_values(rows, "command_name"),
            "input_sources": stats.distinct_values(rows, "input_source"),
            "cli_versions": stats.distinct_values(rows, "cli_version"),
        }

    def events(self, query: EventQuery, limit: int, offset: int) -> Tuple[List[Dict[str, Any]], int]:
        rows = self._rows(query)
        rows.sort(key=lambda item: item["event_time"], reverse=True)
        total = len(rows)
        sliced = rows[offset : offset + limit]
        return [_serialize_event(item) for item in sliced], total


def _serialize_event(event: Dict[str, Any]) -> Dict[str, Any]:
    payload = dict(event)
    payload["event_time"] = to_iso(event["event_time"])
    return payload
