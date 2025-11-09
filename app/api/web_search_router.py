"""Web搜索API路由"""
from fastapi import APIRouter, HTTPException, Query
from app.services.web_search_service import WebSearchService
from app.schema.web_search_schema import WebSearchInfo

router = APIRouter(prefix="/search", tags=["Web Search"])
web_search_service = WebSearchService()


@router.get("", response_model=WebSearchInfo)
async def search(q: str = Query(..., description="搜索关键词")):
    """执行Web搜索
    
    Args:
        q: 搜索关键词
        
    Returns:
        WebSearchInfo: 包含搜索结果的信息
    """
    try:
        result = await web_search_service.search(q)
        if result.error:
            raise HTTPException(status_code=400, detail=result.error)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

