# CoreToolCLI 看板后端

技术栈与 honorHall 对齐：Python 3.9、Flask 3.0 + PyYAML。数据源为 openGauss 数据库 `coreinfactory.cli_command_event`。

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

后端使用纯 Python 的 `py-opengauss==1.3.11` 原生 PG-API，不经过
SQLAlchemy 或 `py_opengauss.driver.dbapi20`。该方案不依赖系统 `libpq`，
Windows 无需安装或配置 `libpq.dll`。

依赖随 `requirements.txt` 安装，也可单独安装并验证：

```bash
pip install py-opengauss==1.3.11
python -c "import py_opengauss; from importlib.metadata import version; print(version('py-opengauss'))"
```

应用按现有配置构造单地址连接，例如配置为：

```yaml
gaussdb:
  host: 127.0.0.1
  port: 5432
  user: root
  database: postgres
  schema: coreinfactory
  sslmode: disable
```

对应连接形式为
`py_opengauss.open("opengauss://root:<URL 编码密码>@127.0.0.1:5432/postgres?[sslmode]=disable")`。
用户名和密码由应用自动做 URL 编码；密码仍从 `GAUSS_PASSWORD` 读取和解码，
不要将明文密码写入 YAML。

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
