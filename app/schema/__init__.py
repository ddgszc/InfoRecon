"""数据模型定义包

包含DNS和IP信息的数据结构定义
"""

from app.schema.dns_schema import (
    ARecord,
    AAAARecord,
    MXRecord,
    TXTRecord,
    NSRecord,
    DNSInfo
)

from app.schema.ip_schema import IPInfo

__all__ = [
    # DNS相关
    'ARecord',
    'AAAARecord',
    'MXRecord',
    'TXTRecord',
    'NSRecord',
    'DNSInfo',
    # IP相关
    'IPInfo',
]

