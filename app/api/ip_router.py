"""IP查询API路由"""
from fastapi import APIRouter, HTTPException
from app.services.ip_service import IPService
from app.schema.ip_schema import IPInfo

router = APIRouter(prefix="/ip", tags=["IP"])
ip_service = IPService()


@router.get("/{ip}", response_model=IPInfo)
async def get_ip_info(ip: str):
    """查询IP地址信息
    
    Args:
        ip: 要查询的IP地址
        
    Returns:
        IPInfo: 包含IP地理位置等信息
    """
    try:
        result = await ip_service.get_ip_info(ip)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

