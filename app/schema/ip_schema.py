from pydantic import BaseModel, Field
from typing import Optional


class IPInfo(BaseModel):
    """IP信息
    
    包含IP地址的反向DNS查询和地理位置信息
    """
    ip: str = Field(description="查询的IP地址")
    # IP查域名大多数时候不够准确，只能依靠被动DNS，quake，shadon等，暂时放弃
    # domains: list[str] = Field(default_factory=list, description="反查域名列表，最多5个")
    country: Optional[str] = Field(default=None, description="IP所属国家")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ip": "8.8.8.8",
                "domains": ["dns.google"],
                "country": "United States"
            }
        }

