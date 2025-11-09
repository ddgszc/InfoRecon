"""数据模型定义包

包含DNS、IP和Web搜索信息的数据结构定义
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

from app.schema.web_search_schema import (
    WebSearchInfo
)

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
    # Web搜索相关
    'SearchResult',
    'WebSearchInfo',
]

