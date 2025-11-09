"""Web搜索API路由"""
from fastapi import APIRouter, HTTPException, Query, Response
from app.services.web_search_service import WebSearchService
from app.schema.web_search_schema import WebSearchInfo
from app.cache.cache_decorator import cached

router = APIRouter(prefix="/search", tags=["Web Search"])
web_search_service = WebSearchService()


@router.get("", response_model=WebSearchInfo)
@cached("search")
async def search(q: str = Query(..., description="搜索关键词"), response: Response = None):
    """执行Web搜索
    
    Args:
        q: 搜索关键词
        response: FastAPI响应对象（用于添加缓存状态头）
        
    Returns:
        WebSearchInfo: 包含搜索结果的信息
        
    响应头:
        X-Cache-Status: HIT (缓存命中) | MISS (缓存未命中)
        X-Cache-Key: 缓存键（仅在命中时）
    """
    try:
        result = await web_search_service.search(q)
        if result.error:
            raise HTTPException(status_code=400, detail=result.error)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

