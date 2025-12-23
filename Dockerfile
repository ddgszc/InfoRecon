# --- 第一阶段：构建阶段 (Build Stage) ---

# 使用官方推荐的完整路径，并选择 slim 版本减少基础开销
FROM ghcr.io/astral-sh/uv:python3.13-bookworm AS builder

# 设置构建环境变量
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    # 指定 uv 缓存目录，方便后续挂载
    UV_CACHE_DIR=/root/.cache/uv \
    UV_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/

WORKDIR /app

# 1. 安装构建依赖（如果你的 Python 包需要编译 C 扩展，保留 build-essential）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 2. 仅复制依赖描述文件
COPY pyproject.toml ./

# 3. 同步依赖 (利用缓存挂载)
# --mount=type=cache 会在构建时挂载缓存，大幅提升二次构建速度
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev || \
    uv sync --no-install-project --no-dev

# --- 第二阶段：运行时阶段 (Runtime Stage) ---
FROM python:3.13-slim-bookworm

WORKDIR /app

# 设置运行时环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # 将虚拟环境 bin 加入 PATH，使容器内可以直接运行 python
    PATH="/app/.venv/bin:$PATH"

# 安装运行时必要的系统库 (包括 Playwright 需要的依赖)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    wget \
    gnupg \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 创建非 root 用户
RUN useradd -m -u 1000 appuser

# 4. 从构建阶段复制虚拟环境
# 保持目录结构一致
COPY --from=builder /app/.venv /app/.venv

# 5. 复制项目代码并直接设置权限 (防止镜像体积翻倍)
COPY --chown=appuser:appuser . .

# 切换到非 root 用户
USER appuser

# 安装 Playwright 浏览器 (作为 appuser 用户)
RUN playwright install chromium

# 暴露端口 (元数据)
EXPOSE 8000 33668

# 6. 设置默认启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

