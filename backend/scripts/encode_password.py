# Copyright 2026 Huawei Technologies Co., Ltd. All rights reserved
"""
密码编码工具。

用法：
    python -m scripts.encode_password
"""
import getpass
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.encoding import decode_value, encode_password

_ENV_FILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"
)


def _load_env_file() -> dict:
    env_vars = {}
    if os.path.exists(_ENV_FILE_PATH):
        try:
            with open(_ENV_FILE_PATH, "r", encoding="utf-8") as file_handle:
                for line in file_handle:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key.strip()] = value.strip()
        except (IOError, OSError):
            pass
    return env_vars


def _save_env_file(env_vars: dict) -> bool:
    try:
        with open(_ENV_FILE_PATH, "w", encoding="utf-8") as file_handle:
            for key, value in env_vars.items():
                file_handle.write(f"{key}={value}\n")
        return True
    except (IOError, OSError):
        return False


def main():
    print("\n" + "=" * 50)
    print("GaussDB 密码编码工具")
    print("=" * 50 + "\n")

    try:
        password = getpass.getpass("请输入密码: ")
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        return

    if not password:
        print("\n错误: 密码不能为空")
        return

    encoded = encode_password(password)
    decoded = decode_value(encoded)
    if decoded != password:
        print("\n错误: 编码验证失败")
        return

    env_vars = _load_env_file()
    env_vars["GAUSS_PASSWORD"] = encoded
    if _save_env_file(env_vars):
        print("\n" + "=" * 50)
        print("成功！已写入 .env 文件")
        print("=" * 50 + "\n")
    else:
        print("\n错误: 无法写入 .env 文件")


if __name__ == "__main__":
    main()
