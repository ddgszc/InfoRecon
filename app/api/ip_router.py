"""IP查询API路由"""
from fastapi import APIRouter, HTTPException, Response
from app.services.ip_service import IPService
from app.schema.ip_schema import IPInfo
from app.cache.cache_decorator import cached

router = APIRouter(prefix="/ip", tags=["IP"])
ip_service = IPService()


@router.get("/{ip}", response_model=IPInfo)
@cached("ip")
async def get_ip_info(ip: str, response: Response):
    """查询IP地址信息
    
    Args:
        ip: 要查询的IP地址
        response: FastAPI响应对象（用于添加缓存状态头）
        
    Returns:
        IPInfo: 包含IP地理位置等信息
        
    响应头:
        X-Cache-Status: HIT (缓存命中) | MISS (缓存未命中)
        X-Cache-Key: 缓存键（仅在命中时）
    """
    try:
        result = await ip_service.get_ip_info(ip)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

