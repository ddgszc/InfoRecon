# InfoRecon

信息侦察API服务，提供DNS查询、IP地理位置查询和Web搜索功能。

## 功能

- **DNS查询**: 查询域名的A、AAAA、MX、NS、TXT等记录
- **IP查询**: 查询IP地址的地理位置信息
- **Web搜索**: 执行网页搜索并返回结果
- **Redis缓存**: 自动缓存查询结果，提升响应速度

## 环境要求

- Python >= 3.13
- Redis

## 快速开始

### 1. 启动Redis

```bash
docker-compose up -d
```

### 2. 安装依赖

```bash
uv sync
```

### 3. 配置

复制配置文件并修改Redis密码：

```bash
cp config.toml.example config.toml
# 编辑 config.toml，修改Redis密码与docker-compose.yml保持一致
```

### 4. 运行服务

```bash
uv run uvicorn app.main:app --reload
```

服务启动在 `http://localhost:8000`

## API接口

### DNS查询
```
GET /dns/{domain}
```

### IP查询
```
GET /ip/{ip}
```

### Web搜索
```
GET /search?q={query}
```

## API文档

启动服务后访问：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 项目结构

```
InfoRecon/
├── app/
│   ├── api/              # API路由
│   ├── cache/            # 缓存模块
│   ├── schema/           # 数据模型
│   ├── services/         # 业务逻辑
│   ├── config.py         # 配置管理
│   └── main.py           # 应用入口
├── config.toml           # 配置文件
├── docker-compose.yml    # Redis容器配置
└── pyproject.toml        # 项目依赖
```

