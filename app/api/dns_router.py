"""DNS查询API路由"""
from fastapi import APIRouter, HTTPException, Response
from app.services.dns_service import DNSService
from app.schema.dns_schema import DNSInfo
from app.cache.cache_decorator import cached

router = APIRouter(prefix="/dns", tags=["DNS"])
dns_service = DNSService()


@router.get("/{domain}", response_model=DNSInfo)
@cached("dns")
async def get_dns_info(domain: str, response: Response):
    """查询域名的DNS信息
    
    Args:
        domain: 要查询的域名
        response: FastAPI响应对象（用于添加缓存状态头）
        
    Returns:
        DNSInfo: 包含所有DNS记录的信息
        
    响应头:
        X-Cache-Status: HIT (缓存命中) | MISS (缓存未命中)
        X-Cache-Key: 缓存键（仅在命中时）
    """
    try:
        result = await dns_service.get_dns_info(domain)
        if result.error:
            raise HTTPException(status_code=400, detail=result.error)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

