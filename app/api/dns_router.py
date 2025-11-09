"""DNS查询API路由"""
from fastapi import APIRouter, HTTPException
from app.services.dns_service import DNSService
from app.schema.dns_schema import DNSInfo

router = APIRouter(prefix="/dns", tags=["DNS"])
dns_service = DNSService()


@router.get("/{domain}", response_model=DNSInfo)
async def get_dns_info(domain: str):
    """查询域名的DNS信息
    
    Args:
        domain: 要查询的域名
        
    Returns:
        DNSInfo: 包含所有DNS记录的信息
    """
    try:
        result = await dns_service.get_dns_info(domain)
        if result.error:
            raise HTTPException(status_code=400, detail=result.error)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

