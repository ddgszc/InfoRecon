"""URL分析API路由"""
from fastapi import APIRouter, Query, Response
from app.services.get_site import URLAnalyzer
from app.schema.url_schema import URLAnalysisInfo
from app.cache.cache_decorator import cached
from datetime import datetime

router = APIRouter(prefix="/url", tags=["URL Analysis"])

# 全局URLAnalyzer实例，将在应用启动时初始化
url_analyzer: URLAnalyzer = None


def get_url_analyzer() -> URLAnalyzer:
    """获取URLAnalyzer实例"""
    if url_analyzer is None:
        raise RuntimeError("URLAnalyzer未初始化")
    return url_analyzer


@router.get("/analyze", response_model=URLAnalysisInfo)
@cached("url_analysis")
async def analyze_url(
    url: str = Query(..., description="要分析的URL地址"),
    response: Response = None
):
    """分析URL页面内容和重定向链路
    
    Args:
        url: 要分析的URL地址（可以不带协议，默认使用https）
        response: FastAPI响应对象（用于添加缓存状态头）
        
    Returns:
        URLAnalysisInfo: 包含URL分析结果的信息，包括：
            - url_content: 网页内容（Markdown格式）
            - redirect_chain: 完整的重定向链路
        
    响应头:
        X-Cache-Status: HIT (缓存命中) | MISS (缓存未命中)
        X-Cache-Key: 缓存键（仅在命中时）
    """
    try:
        analyzer = get_url_analyzer()
        result = await analyzer.analyze_url(url)
        
        return URLAnalysisInfo(
            url=url,
            url_content=result["url_content"],
            redirect_chain=result["redirect_chain"],
            analysis_time=datetime.now()
        )
    except Exception as e:
        return URLAnalysisInfo(
            url=url,
            url_content="",
            redirect_chain=[],
            analysis_time=datetime.now(),
            error=str(e)
        )

