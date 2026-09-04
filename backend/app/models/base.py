# Copyright 2026 Huawei Technologies Co., Ltd. All rights reserved
"""
SQLAlchemy Base。
"""
from sqlalchemy.orm import DeclarativeBase

__all__ = ["Base"]


class Base(DeclarativeBase):
    """ORM 基类。"""
