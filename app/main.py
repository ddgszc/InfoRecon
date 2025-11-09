"""FastAPI应用主入口"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api import dns_router, ip_router, web_search_router
from app.cache import cache_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时：建立Redis连接
    await cache_manager.connect()
    yield
    # 关闭时：关闭Redis连接
    await cache_manager.close()


app = FastAPI(
    title="InfoRecon API",
    description="信息侦察API - 提供DNS查询、IP查询和Web搜索功能",
    version="1.0.0",
    lifespan=lifespan
)

# 注册路由
app.include_router(dns_router.router)
app.include_router(ip_router.router)
app.include_router(web_search_router.router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "InfoRecon API",
        "docs": "/docs",
        "endpoints": {
            "dns": "/dns/{domain}",
            "ip": "/ip/{ip}",
            "search": "/search?q={query}"
        }
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok"}

