# Copyright 2026 Huawei Technologies Co., Ltd. All rights reserved
"""
CoreToolCLI 指令执行打点事件。
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

__all__ = ["CliCommandEvent"]


class CliCommandEvent(Base):
    """cli_command_event 表映射。"""

    __tablename__ = "cli_command_event"
    __table_args__ = {"schema": "coreinfactory"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    event_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    cli_version: Mapped[str] = mapped_column(String(32), nullable=False)
    domain: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    platform: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    command: Mapped[str] = mapped_column(String(256), nullable=False)
    command_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    duration_ms: Mapped[int] = mapped_column(BigInteger, nullable=False)
    api_duration_ms: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    api_calls: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSONB, nullable=True)
    input_source: Mapped[str] = mapped_column(String(32), nullable=False)
    output_format: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    result: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    exit_code: Mapped[int] = mapped_column(Integer, nullable=False)
    environment: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    error_category: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    args_detail: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_cn_name: Mapped[str] = mapped_column(String(128), nullable=False)
    user_long_id: Mapped[str] = mapped_column(String(256), nullable=False)
    org_dept_code4: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    org_dept_name4: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    org_dept_code5: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    org_dept_name5: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    org_dept_code6: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    org_dept_name6: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
