# Copyright 2026 Huawei Technologies Co., Ltd. All rights reserved
"""
统一错误定义和处理。
"""
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

__all__ = ["APIError", "ValidationError", "NotFoundError", "DatabaseError"]


class APIError(Exception):
    """API 基础异常类。"""

    def __init__(self, message: str, status_code: int = 500, payload: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self) -> Dict[str, Any]:
        rv: Dict[str, Any] = dict(self.payload or {})
        rv["error"] = self.message
        return rv


class ValidationError(APIError):
    """参数验证错误。"""

    def __init__(self, message: str, payload: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, payload=payload)


class NotFoundError(APIError):
    """资源未找到错误。"""

    def __init__(self, message: str = "Resource not found", payload: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=404, payload=payload)


class DatabaseError(APIError):
    """数据库错误。"""

    def __init__(self, message: str = "Database operation failed", payload: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, payload=payload)
