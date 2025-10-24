from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ARecord(BaseModel):
    """A记录 - IPv4地址记录
    
    将域名映射到IPv4地址，是最常用的DNS记录类型
    """
    ip: str = Field(description="IPv4地址")
    ttl: int = Field(description="生存时间(秒)")


class AAAARecord(BaseModel):
    """AAAA记录 - IPv6地址记录
    
    将域名映射到IPv6地址，用于支持IPv6协议
    """
    ip: str = Field(description="IPv6地址")
    ttl: int = Field(description="生存时间(秒)")


class MXRecord(BaseModel):
    """MX记录 - 邮件交换记录
    
    指定接收电子邮件的邮件服务器，priority值越小优先级越高
    """
    priority: int = Field(description="优先级，数值越小优先级越高")
    exchange: str = Field(description="邮件服务器地址")
    ttl: int = Field(description="生存时间(秒)")


class TXTRecord(BaseModel):
    """TXT记录 - 文本记录
    
    存储任意文本信息，常用于域名验证、SPF、DKIM等配置
    """
    text: str = Field(description="文本内容")
    ttl: int = Field(description="生存时间(秒)")


class NSRecord(BaseModel):
    """NS记录 - 域名服务器记录
    
    指定该域名由哪台域名服务器进行解析
    """
    nameserver: str = Field(description="域名服务器地址")
    ttl: int = Field(description="生存时间(秒)")


class CNAMERecord(BaseModel):
    """CNAME记录 - 别名记录
    
    将一个域名指向另一个域名，用于域名别名
    """
    target: str = Field(description="目标域名")
    ttl: int = Field(description="生存时间(秒)")


class WhoisInfo(BaseModel):
    """WHOIS信息
    
    包含域名的注册信息
    """
    registrar: Optional[str] = Field(default=None, description="注册商")
    status: Optional[List[str]] = Field(default=None, description="域名状态列表")
    creation_date: Optional[datetime] = Field(default=None, description="注册时间")
    updated_date: Optional[datetime] = Field(default=None, description="更新时间")
    expiration_date: Optional[datetime] = Field(default=None, description="到期时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "registrar": "GoDaddy.com, LLC",
                "status": ["clientTransferProhibited", "clientUpdateProhibited"],
                "creation_date": "2000-01-01T00:00:00",
                "updated_date": "2024-01-01T00:00:00",
                "expiration_date": "2025-12-31T23:59:59"
            }
        }


class DNSInfo(BaseModel):
    """DNS信息汇总
    
    包含域名的所有DNS记录信息和WHOIS注册信息
    """
    domain: str = Field(description="查询的域名")
    # query_time: datetime = Field(default_factory=datetime.now, description="查询时间")
    a_records: List[ARecord] = Field(default_factory=list, description="A记录列表")
    # aaaa_records: List[AAAARecord] = Field(default_factory=list, description="AAAA记录列表")
    cname_records: List[CNAMERecord] = Field(default_factory=list, description="CNAME记录列表")
    mx_records: List[MXRecord] = Field(default_factory=list, description="MX记录列表")
    txt_records: List[TXTRecord] = Field(default_factory=list, description="TXT记录列表")
    ns_records: List[NSRecord] = Field(default_factory=list, description="NS记录列表")
    whois_info: Optional[WhoisInfo] = Field(default=None, description="WHOIS注册信息")
    error: Optional[str] = Field(default=None, description="错误信息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "domain": "example.com",
                "query_time": "2025-10-24T10:00:00",
                "a_records": [
                    {"ip": "93.184.216.34", "ttl": 3600}
                ],
                "aaaa_records": [
                    {"ip": "2606:2800:220:1:248:1893:25c8:1946", "ttl": 3600}
                ],
                "cname_records": [
                    {"target": "example.cdn.com", "ttl": 3600}
                ],
                "mx_records": [
                    {"priority": 10, "exchange": "mail.example.com", "ttl": 3600}
                ],
                "txt_records": [
                    {"text": "v=spf1 include:_spf.example.com ~all", "ttl": 3600}
                ],
                "ns_records": [
                    {"nameserver": "ns1.example.com", "ttl": 3600}
                ]
            }
        }

