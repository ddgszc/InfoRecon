"""FastAPI应用主入口"""
from fastapi import FastAPI
from app.api import dns_router, ip_router, web_search_router

app = FastAPI(
    title="InfoRecon API",
    description="信息侦察API - 提供DNS查询、IP查询和Web搜索功能",
    version="1.0.0"
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

