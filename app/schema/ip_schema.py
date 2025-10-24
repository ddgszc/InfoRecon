from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class GeoLocation(BaseModel):
    """地理位置信息"""
    country: Optional[str] = Field(default=None, description="国家")
    country_code: Optional[str] = Field(default=None, description="国家代码")
    region: Optional[str] = Field(default=None, description="地区/省份")
    region_code: Optional[str] = Field(default=None, description="地区代码")
    city: Optional[str] = Field(default=None, description="城市")
    zip_code: Optional[str] = Field(default=None, description="邮政编码")
    latitude: Optional[float] = Field(default=None, description="纬度")
    longitude: Optional[float] = Field(default=None, description="经度")
    timezone: Optional[str] = Field(default=None, description="时区")
    isp: Optional[str] = Field(default=None, description="互联网服务提供商")
    org: Optional[str] = Field(default=None, description="组织名称")
    as_number: Optional[str] = Field(default=None, description="AS号码")


class ASNInfo(BaseModel):
    """自治系统信息
    
    ASN (Autonomous System Number) 是分配给自治系统的唯一标识符
    用于BGP路由和互联网流量管理
    """
    asn: Optional[str] = Field(default=None, description="自治系统号")
    name: Optional[str] = Field(default=None, description="AS名称")
    organization: Optional[str] = Field(default=None, description="组织名称")
    isp: Optional[str] = Field(default=None, description="互联网服务提供商")


class IPInfo(BaseModel):
    """IP地址信息汇总
    
    包含IP地址的详细信息，包括地理位置、ASN、ISP等
    """
    ip: str = Field(description="IP地址")
    query_time: datetime = Field(default_factory=datetime.now, description="查询时间")
    ip_version: Optional[int] = Field(default=None, description="IP版本 (4或6)")
    is_private: bool = Field(default=False, description="是否为私有IP地址")
    reverse_dns: Optional[str] = Field(default=None, description="反向DNS主机名")
    geo_location: Optional[GeoLocation] = Field(default=None, description="地理位置信息")
    asn_info: Optional[ASNInfo] = Field(default=None, description="ASN信息")
    error: Optional[str] = Field(default=None, description="错误信息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ip": "8.8.8.8",
                "query_time": "2025-10-24T10:00:00",
                "ip_version": 4,
                "hostname": "dns.google",
                "geo_location": {
                    "country": "United States",
                    "country_code": "US",
                    "region": "California",
                    "city": "Mountain View",
                    "latitude": 37.386,
                    "longitude": -122.0838,
                    "timezone": "America/Los_Angeles"
                },
                "asn_info": {
                    "asn": "AS15169",
                    "org": "Google LLC",
                    "isp": "Google LLC"
                },
                "is_proxy": False,
                "is_hosting": True
            }
        }

