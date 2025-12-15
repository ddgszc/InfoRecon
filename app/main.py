"""FastAPI应用主入口"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api import dns_router, ip_router, web_search_router, batch_router
from app.cache import cache_manager
from app.services.async_whois_service import AsyncWhoisService
from app.services.ip_service import GeoIPReader


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时：建立Redis连接
    await cache_manager.connect()
    yield
    # 关闭时：清理所有资源
    await cache_manager.close()
    await AsyncWhoisService.shutdown()
    await GeoIPReader.shutdown()


app = FastAPI(
    title="InfoRecon API",
    description="信息侦察API - 提供DNS查询、IP查询、Web搜索和批量查询功能",
    version="2.0.0",
    lifespan=lifespan
)

# 注册路由
app.include_router(dns_router.router)
app.include_router(ip_router.router)
app.include_router(web_search_router.router)
app.include_router(batch_router.router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "InfoRecon API v2.0 - 完全异步架构",
        "docs": "/docs",
        "features": [
            "完全异步DNS查询",
            "线程池优化的WHOIS查询",
            "高并发批量查询支持",
            "Redis连接池缓存",
            "智能速率限制"
        ],
        "endpoints": {
            "dns": "/dns/{domain}",
            "ip": "/ip/{ip}",
            "search": "/search?q={query}",
            "batch_dns": "/batch/dns",
            "batch_ip": "/batch/ip",
            "batch_search": "/batch/search"
        }
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok"}

