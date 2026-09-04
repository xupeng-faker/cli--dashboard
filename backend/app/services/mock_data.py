# Copyright 2026 Huawei Technologies Co., Ltd. All rights reserved
"""
本地演示用指令打点样例数据。

字段形态对齐真实 cli_command_event 记录，例如：
coretool coretest testresult log download / input_source=windows /
api_calls 使用 durationMs、statusCode。
"""
import random
import threading
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List

from app.utils.timeutil import TZ_SHANGHAI, now_shanghai

__all__ = ["get_mock_events"]

_LOCK = threading.Lock()
_EVENTS: List[Dict[str, Any]] = []

_CLI_VERSIONS = [
    ("0.0.3", 12),
    ("0.0.4", 28),
    ("0.0.5", 60),
]

_ENVIRONMENTS = [("prod", 78), ("beta", 14), ("test", 8)]
_INPUT_SOURCES = [("windows", 58), ("darwin", 27), ("linux", 15)]
_OUTPUT_FORMATS = [("json", 62), ("table", 38)]

_COMMANDS = [
    {
        "domain": "coretest",
        "platform": "testresult",
        "command": "coretool coretest testresult log download",
        "command_name": "download",
        "host": "coretestresult.cloudspider.rnd.huawei.com",
        "path": "/autoAnalyse/api/v1/getLoadLinkByCtrId/{id}",
        "id_flag": "test-result-id",
        "base_ms": 200,
        "weight": 22,
    },
    {
        "domain": "coretest",
        "platform": "testresult",
        "command": "coretool coretest testresult log list",
        "command_name": "list",
        "host": "coretestresult.cloudspider.rnd.huawei.com",
        "path": "/autoAnalyse/api/v1/listLogs",
        "id_flag": None,
        "base_ms": 160,
        "weight": 12,
    },
    {
        "domain": "coretest",
        "platform": "testresult",
        "command": "coretool coretest testresult report get",
        "command_name": "get",
        "host": "coretestresult.cloudspider.rnd.huawei.com",
        "path": "/autoAnalyse/api/v1/getReport/{id}",
        "id_flag": "test-result-id",
        "base_ms": 320,
        "weight": 10,
    },
    {
        "domain": "coretest",
        "platform": "testcase",
        "command": "coretool coretest testcase list",
        "command_name": "list",
        "host": "coretestcase.cloudspider.rnd.huawei.com",
        "path": "/api/v1/cases",
        "id_flag": None,
        "base_ms": 140,
        "weight": 9,
    },
    {
        "domain": "coretest",
        "platform": "testcase",
        "command": "coretool coretest testcase run",
        "command_name": "run",
        "host": "coretestcase.cloudspider.rnd.huawei.com",
        "path": "/api/v1/cases/{id}/run",
        "id_flag": "case-id",
        "base_ms": 1800,
        "weight": 6,
    },
    {
        "domain": "corecfg",
        "platform": "env",
        "command": "coretool corecfg env get",
        "command_name": "get",
        "host": "corecfgenv.cloudspider.rnd.huawei.com",
        "path": "/api/v1/env",
        "id_flag": None,
        "base_ms": 90,
        "weight": 8,
    },
    {
        "domain": "corecfg",
        "platform": "env",
        "command": "coretool corecfg env set",
        "command_name": "set",
        "host": "corecfgenv.cloudspider.rnd.huawei.com",
        "path": "/api/v1/env",
        "id_flag": None,
        "base_ms": 120,
        "weight": 4,
    },
    {
        "domain": "corelog",
        "platform": "query",
        "command": "coretool corelog query search",
        "command_name": "search",
        "host": "corelogquery.cloudspider.rnd.huawei.com",
        "path": "/api/v1/search",
        "id_flag": None,
        "base_ms": 480,
        "weight": 8,
    },
    {
        "domain": "corelog",
        "platform": "query",
        "command": "coretool corelog query download",
        "command_name": "download",
        "host": "corelogquery.cloudspider.rnd.huawei.com",
        "path": "/api/v1/download/{id}",
        "id_flag": "log-id",
        "base_ms": 900,
        "weight": 5,
    },
]

_DEPTS = [
    {
        "org_dept_code4": "CN00",
        "org_dept_name4": "云核心网产品线",
        "org_dept_code5": "CN01",
        "org_dept_name5": "控制面开发部",
        "org_dept_code6": "CN011",
        "org_dept_name6": "会话管理团队",
    },
    {
        "org_dept_code4": "CN00",
        "org_dept_name4": "云核心网产品线",
        "org_dept_code5": "CN02",
        "org_dept_name5": "用户面开发部",
        "org_dept_code6": "CN021",
        "org_dept_name6": "转发面团队",
    },
    {
        "org_dept_code4": "CN00",
        "org_dept_name4": "云核心网产品线",
        "org_dept_code5": "CN03",
        "org_dept_name5": "工具与效能部",
        "org_dept_code6": "CN031",
        "org_dept_name6": "研发工具团队",
    },
    {
        "org_dept_code4": "CN00",
        "org_dept_name4": "云核心网产品线",
        "org_dept_code5": "CN04",
        "org_dept_name5": "无线算法部",
        "org_dept_code6": "CN041",
        "org_dept_name6": "调度算法团队",
    },
    {
        "org_dept_code4": "CN00",
        "org_dept_name4": "云核心网产品线",
        "org_dept_code5": "CN05",
        "org_dept_name5": "测试使能部",
        "org_dept_code6": "CN051",
        "org_dept_name6": "自动化测试团队",
    },
    {
        "org_dept_code4": "CN00",
        "org_dept_name4": "云核心网产品线",
        "org_dept_code5": "CN06",
        "org_dept_name5": "架构设计部",
        "org_dept_code6": "CN061",
        "org_dept_name6": "平台架构团队",
    },
    {
        "org_dept_code4": "IT00",
        "org_dept_name4": "IT产品线",
        "org_dept_code5": "IT08",
        "org_dept_name5": "DevOps 平台部",
        "org_dept_code6": "IT081",
        "org_dept_name6": "流水线团队",
    },
    {
        "org_dept_code4": "IT00",
        "org_dept_name4": "IT产品线",
        "org_dept_code5": "IT09",
        "org_dept_name5": "云服务开发部",
        "org_dept_code6": "IT091",
        "org_dept_name6": "服务接入团队",
    },
    {
        "org_dept_code4": "IT00",
        "org_dept_name4": "IT产品线",
        "org_dept_code5": "IT10",
        "org_dept_name5": "安全与合规部",
        "org_dept_code6": "IT101",
        "org_dept_name6": "研发安全团队",
    },
]

_NAMES = [
    "张伟", "李娜", "王芳", "刘洋", "陈晨", "杨帆", "赵磊", "黄敏",
    "周杰", "吴昊", "徐静", "孙鹏", "马超", "朱婷", "胡明", "郭涛",
    "林峰", "何雨", "高远", "罗斌", "梁欢", "宋琳", "唐浩", "许晴",
    "钱进", "邓超", "韩雪", "魏明", "蒋芳", "冯磊", "曹颖", "彭博",
    "萧然", "潘婷", "程浩", "卢敏", "江晨", "沈悦", "姚磊", "崔宁",
    "钟华", "谭雪", "贺军", "龚丽", "樊伟", "蓝秋", "覃峰", "尹洁",
    "黎波", "邱敏", "侯杰", "邵倩",
]

_ERROR_CATALOG = [
    ("network", "NET_TIMEOUT", 35),
    ("network", "NET_CONN_RESET", 10),
    ("auth", "AUTH_EXPIRED", 20),
    ("auth", "AUTH_FORBIDDEN", 8),
    ("validation", "ARG_REQUIRED", 12),
    ("validation", "ARG_INVALID", 8),
    ("business", "BIZ_NOT_FOUND", 10),
    ("business", "BIZ_CONFLICT", 6),
    ("unknown", "UNKNOWN", 5),
]


def _weighted_choice(rng: random.Random, items):
    if isinstance(items[0], dict):
        weights = [item["weight"] for item in items]
        return rng.choices(items, weights=weights, k=1)[0]
    if len(items[0]) == 2:
        values, weights = zip(*items)
        return rng.choices(values, weights=weights, k=1)[0]
    payload = items
    weights = [item[-1] for item in payload]
    return rng.choices(payload, weights=weights, k=1)[0]


def _build_users() -> List[Dict[str, Any]]:
    users = []
    for index, name in enumerate(_NAMES):
        dept = _DEPTS[index % len(_DEPTS)]
        short_id = f"w{100000 + index}"
        users.append(
            {
                "user_id": short_id,
                "user_cn_name": name,
                "user_long_id": f"00{80000000 + index}",
                **dept,
            }
        )
    return users


def _pick_hour(rng: random.Random) -> int:
    return rng.choices(range(24), weights=[1] * 8 + [8] * 4 + [5] * 2 + [9] * 5 + [3] * 5, k=1)[0]


def _pick_result(rng: random.Random, command_name: str) -> str:
    failure_boost = 0.04 if command_name in {"run", "download", "set"} else 0.0
    roll = rng.random()
    if roll < 0.06 + failure_boost:
        return "failure"
    if roll < 0.09 + failure_boost:
        return "usage_error"
    if roll < 0.11:
        return "interrupted"
    return "success"


def _duration(rng: random.Random, command: Dict[str, Any], result: str) -> tuple[int, int]:
    duration = max(30, int(rng.lognormvariate(0, 0.45) * command["base_ms"]))
    if result != "success":
        duration = int(duration * rng.uniform(0.35, 0.9))
    api_share = rng.uniform(0.88, 0.99)
    api_duration = max(8, int(duration * api_share))
    return duration, api_duration


def _api_calls(command: Dict[str, Any], api_duration: int, result: str, resource_id: str) -> List[Dict[str, Any]]:
    path = command["path"].replace("{id}", resource_id)
    status = 200
    if result == "failure":
        status = 401 if command["command_name"] in {"get", "set"} else 502
    elif result == "usage_error":
        status = 400
    return [
        {
            "host": command["host"],
            "path": path,
            "method": "GET" if command["command_name"] != "set" else "POST",
            "attempt": 1,
            "durationMs": max(8, api_duration),
            "statusCode": status,
        }
    ]


def _reference_event(users: List[Dict[str, Any]]) -> Dict[str, Any]:
    """写入用户提供的真实样例，便于对照事件明细。"""
    return {
        "id": 1847,
        "event_id": "333b716f-9631-4786-8d29-b0d212106c7b",
        "event_time": datetime(2026, 8, 29, 17, 45, 47, 293172, tzinfo=TZ_SHANGHAI),
        "cli_version": "0.0.5",
        "domain": "coretest",
        "platform": "testresult",
        "command": "coretool coretest testresult log download",
        "command_name": "download",
        "duration_ms": 184,
        "api_duration_ms": 183,
        "api_calls": [
            {
                "host": "coretestresult.cloudspider.rnd.huawei.com",
                "path": "/autoAnalyse/api/v1/getLoadLinkByCtrId/336128648",
                "method": "GET",
                "attempt": 1,
                "durationMs": 183,
                "statusCode": 200,
            }
        ],
        "input_source": "windows",
        "output_format": "json",
        "result": "success",
        "exit_code": 0,
        "environment": "prod",
        "error_category": None,
        "error_code": None,
        "args_detail": {
            "flags": {"output": "json", "test-result-id": "336128648"},
            "positional": [],
        },
        **users[0],
    }


def generate_mock_events(days: int = 400) -> List[Dict[str, Any]]:
    rng = random.Random(42)
    users = _build_users()
    now = now_shanghai()
    events: List[Dict[str, Any]] = []
    event_pk = 1
    windows = []
    last_index = max(len(users) - 1, 1)
    for index, _user in enumerate(users):
        join_day = int(index / last_index * days * 0.72)
        if index % 6 == 0:
            leave_day = min(days + 1, join_day + 80 + (index % 70))
        else:
            leave_day = days + 1
        windows.append((join_day, leave_day))

    for day_offset in range(days, -1, -1):
        day = (now - timedelta(days=day_offset)).replace(hour=0, minute=0, second=0, microsecond=0)
        weekday = day.weekday()
        age = days - day_offset
        growth = 1 + 0.0028 * age
        base = 38 if weekday < 5 else 11
        count = int(base * growth * rng.uniform(0.86, 1.12))
        active = [users[index] for index, (join_day, leave_day) in enumerate(windows) if join_day <= age < leave_day]
        if not active:
            active = users

        for _ in range(count):
            command = _weighted_choice(rng, _COMMANDS)
            input_source = _weighted_choice(rng, _INPUT_SOURCES)
            hour = _pick_hour(rng)
            event_time = day.replace(hour=hour, minute=rng.randint(0, 59), second=rng.randint(0, 59))
            if event_time > now:
                continue

            result = _pick_result(rng, command["command_name"])
            duration_ms, api_duration_ms = _duration(rng, command, result)
            user = rng.choice(active)
            error_category = None
            error_code = None
            exit_code = 0
            if result == "failure":
                picked = _weighted_choice(rng, _ERROR_CATALOG)
                error_category, error_code = picked[0], picked[1]
                exit_code = 1
            elif result == "usage_error":
                error_category = "validation"
                error_code = rng.choice(["ARG_REQUIRED", "ARG_INVALID"])
                exit_code = 2
            elif result == "interrupted":
                exit_code = 130

            output_format = _weighted_choice(rng, _OUTPUT_FORMATS)
            resource_id = str(rng.randint(300000000, 399999999))
            flags: Dict[str, str] = {"output": output_format}
            if command["id_flag"]:
                flags[command["id_flag"]] = resource_id

            events.append(
                {
                    "id": event_pk,
                    "event_id": str(uuid.uuid4()),
                    "event_time": event_time,
                    "cli_version": _weighted_choice(rng, _CLI_VERSIONS),
                    "domain": command["domain"],
                    "platform": command["platform"],
                    "command": command["command"],
                    "command_name": command["command_name"],
                    "duration_ms": duration_ms,
                    "api_duration_ms": api_duration_ms,
                    "api_calls": _api_calls(command, api_duration_ms, result, resource_id),
                    "input_source": input_source,
                    "output_format": output_format,
                    "result": result,
                    "exit_code": exit_code,
                    "environment": _weighted_choice(rng, _ENVIRONMENTS),
                    "error_category": error_category,
                    "error_code": error_code,
                    "args_detail": {"flags": flags, "positional": []},
                    **user,
                }
            )
            event_pk += 1

    events.append(_reference_event(users))
    events.sort(key=lambda item: item["event_time"])
    return events


def get_mock_events() -> List[Dict[str, Any]]:
    global _EVENTS
    if _EVENTS:
        return _EVENTS
    with _LOCK:
        if not _EVENTS:
            _EVENTS = generate_mock_events()
    return _EVENTS
