# CoreToolCLI 看板后端

技术栈与 honorHall 对齐：Python 3.9、Flask 3.0 + SQLAlchemy 2.0 + PyYAML。数据源为高斯数据库 `coreinfactory.cli_command_event`。

## 本地启动（样例数据）

默认 `config/config_test.yaml` 中 `use_mock: true`，无需连库。

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export FLASK_ENV=local
python wsgi.py
```

服务端口默认 `5002`。健康检查：`GET http://127.0.0.1:5002/cli_api/health/`

## 连接高斯数据库

1. 将 `use_mock` 改为 `false`，填写 `config/config_test.yaml` 或 `config_prod.yaml` 中的 `gaussdb` 连接信息。
2. 编码密码并写入 `.env`：

```bash
python -m scripts.encode_password
```

3. 启动：

```bash
export FLASK_ENV=local   # 或 prod
python wsgi.py
```

GaussDB / OpenGauss 使用 PostgreSQL 协议，驱动为 `psycopg2`。

## 接口

- `GET /cli_api/health/`
- `GET /cli_api/dashboard/overview`
- `GET /cli_api/dashboard/commands`
- `GET /cli_api/dashboard/users`
- `GET /cli_api/dashboard/departments`
- `GET /cli_api/dashboard/quality`
- `GET /cli_api/dashboard/events`
- `GET /cli_api/dashboard/filters`

公共筛选参数：`start`、`end`（ISO 8601）、`domain`、`platform`、`environment`、`result`、`command_name`、`user_id`、`input_source`、`keyword`。

部门下钻接口额外接收 `level`（4、5、6）、`dept4` 和 `dept5`；查询五级部门时必须传 `dept4`，查询六级部门时必须同时传 `dept4`、`dept5`。
