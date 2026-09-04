# Copyright 2026 Huawei Technologies Co., Ltd. All rights reserved
"""
编码工具模块。
"""
import base64

__all__ = ["encode_password", "decode_value"]


def encode_password(password: str) -> str:
    """
    对密码进行编码。

    Args:
        password: 原始密码

    Returns:
        编码后的字符串
    """
    if not password:
        return ""
    encoded = base64.b64encode(password.encode("utf-8")).decode("utf-8")
    return encoded


def decode_value(value: str) -> str:
    """
    对编码值进行解码。

    Args:
        value: 编码的字符串

    Returns:
        解码后的字符串；若解码失败则返回原值
    """
    if not value:
        return ""
    try:
        decoded = base64.b64decode(value).decode("utf-8")
        return decoded
    except (ValueError, UnicodeDecodeError):
        return value
