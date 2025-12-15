"""异步DNS解析器
遵循 SOLID 原则的 DNS 查询抽象层
"""
import aiodns
import asyncio
from typing import List, Optional, Protocol
from abc import ABC, abstractmethod

from app.schema.dns_schema import (
    ARecord,
    AAAARecord,
    CNAMERecord,
    MXRecord,
    TXTRecord,
    NSRecord
)


class DNSRecordQueryProtocol(Protocol):
    """DNS记录查询协议（接口隔离原则）"""
    
    async def query(self, domain: str) -> List:
        """查询DNS记录"""
        ...


class AsyncDNSResolverBase(ABC):
    """DNS解析器基类（开闭原则 + 依赖倒置原则）"""
    
    def __init__(self, timeout: float = 5.0, nameservers: Optional[List[str]] = None):
        self.timeout = timeout
        self.resolver = aiodns.DNSResolver(timeout=timeout)
        if nameservers:
            self.resolver.nameservers = nameservers
    
    @abstractmethod
    async def query(self, domain: str) -> List:
        """查询DNS记录的抽象方法"""
        pass
    
    async def safe_query(self, domain: str) -> List:
        """安全查询，失败返回空列表而非抛异常"""
        try:
            return await self.query(domain)
        except (aiodns.error.DNSError, asyncio.TimeoutError):
            return []


class ARecordResolver(AsyncDNSResolverBase):
    """A记录查询器（单一职责原则）"""
    
    async def query(self, domain: str) -> List[ARecord]:
        results = await self.resolver.query(domain, 'A')
        return [
            ARecord(ip=str(result.host), ttl=result.ttl)
            for result in results
        ]


class AAAARecordResolver(AsyncDNSResolverBase):
    """AAAA记录查询器（单一职责原则）"""
    
    async def query(self, domain: str) -> List[AAAARecord]:
        results = await self.resolver.query(domain, 'AAAA')
        return [
            AAAARecord(ip=str(result.host), ttl=result.ttl)
            for result in results
        ]


class CNAMERecordResolver(AsyncDNSResolverBase):
    """CNAME记录查询器（单一职责原则）"""
    
    async def query(self, domain: str) -> List[CNAMERecord]:
        results = await self.resolver.query(domain, 'CNAME')
        return [
            CNAMERecord(target=str(result.cname).rstrip('.'), ttl=result.ttl)
            for result in results
        ]


class MXRecordResolver(AsyncDNSResolverBase):
    """MX记录查询器（单一职责原则）"""
    
    async def query(self, domain: str) -> List[MXRecord]:
        results = await self.resolver.query(domain, 'MX')
        return [
            MXRecord(
                priority=result.priority,
                exchange=str(result.host).rstrip('.'),
                ttl=result.ttl
            )
            for result in results
        ]


class TXTRecordResolver(AsyncDNSResolverBase):
    """TXT记录查询器（单一职责原则）"""
    
    async def query(self, domain: str) -> List[TXTRecord]:
        results = await self.resolver.query(domain, 'TXT')
        records = []
        for result in results:
            # 合并多段文本
            text = ''.join(
                s.decode() if isinstance(s, bytes) else str(s)
                for s in result.text
            )
            # 只保留SPF记录
            if text.startswith('v=spf'):
                records.append(TXTRecord(text=text, ttl=result.ttl))
        return records


class NSRecordResolver(AsyncDNSResolverBase):
    """NS记录查询器（单一职责原则）"""
    
    async def query(self, domain: str) -> List[NSRecord]:
        results = await self.resolver.query(domain, 'NS')
        return [
            NSRecord(nameserver=str(result.host).rstrip('.'), ttl=result.ttl)
            for result in results
        ]


class DNSResolverFactory:
    """DNS解析器工厂（工厂模式 + 单例模式）"""
    
    _resolvers = {}
    
    @classmethod
    def get_resolver(
        cls,
        record_type: str,
        timeout: float = 5.0,
        nameservers: Optional[List[str]] = None
    ) -> AsyncDNSResolverBase:
        """获取指定类型的DNS解析器（复用实例，减少资源消耗）"""
        
        key = f"{record_type}_{timeout}_{nameservers}"
        
        if key not in cls._resolvers:
            resolver_map = {
                'A': ARecordResolver,
                'AAAA': AAAARecordResolver,
                'CNAME': CNAMERecordResolver,
                'MX': MXRecordResolver,
                'TXT': TXTRecordResolver,
                'NS': NSRecordResolver
            }
            
            resolver_class = resolver_map.get(record_type.upper())
            if not resolver_class:
                raise ValueError(f"不支持的DNS记录类型: {record_type}")
            
            cls._resolvers[key] = resolver_class(timeout, nameservers)
        
        return cls._resolvers[key]

