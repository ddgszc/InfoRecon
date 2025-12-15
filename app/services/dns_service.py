"""DNS信息查询服务
完全异步架构，支持高并发查询
遵循 SOLID、DRY、KISS 原则
"""
import asyncio
from typing import Optional, List

from app.schema.dns_schema import DNSInfo
from app.services.async_dns_resolver import DNSResolverFactory
from app.services.async_whois_service import AsyncWhoisService


class DomainNormalizer:
    """域名规范化工具（单一职责原则）"""
    
    @staticmethod
    def normalize(domain: str) -> str:
        """规范化域名
        
        - 去除前后空格
        - 转换为小写
        - 移除协议前缀（http://, https://）
        - 移除路径部分
        """
        domain = domain.strip().lower()
        
        # 移除协议前缀
        for prefix in ('https://', 'http://'):
            if domain.startswith(prefix):
                domain = domain[len(prefix):]
                break
        
        # 移除路径部分
        if '/' in domain:
            domain = domain.split('/')[0]
        
        return domain


class DNSService:
    """DNS信息查询服务
    
    提供完全异步的DNS记录查询功能
    使用组合而非继承（组合优于依赖原则）
    """
    
    def __init__(
        self,
        timeout: float = 5.0,
        nameservers: Optional[List[str]] = None,
        enable_whois: bool = True
    ):
        """初始化DNS服务
        
        Args:
            timeout: DNS查询超时时间(秒)
            nameservers: 自定义DNS服务器列表，如 ['8.8.8.8', '8.8.4.4']
            enable_whois: 是否启用WHOIS查询
        """
        self.timeout = timeout
        self.nameservers = nameservers
        self.enable_whois = enable_whois
        self.normalizer = DomainNormalizer()
    
    async def _query_all_records(self, domain: str) -> dict:
        """并发查询所有DNS记录（DRY原则 - 避免重复代码）
        
        Args:
            domain: 规范化后的域名
            
        Returns:
            包含所有DNS记录的字典
        """
        # 定义要查询的记录类型
        record_types = ['A', 'CNAME', 'MX', 'TXT', 'NS']
        
        # 创建所有查询任务
        tasks = {}
        for record_type in record_types:
            resolver = DNSResolverFactory.get_resolver(
                record_type,
                self.timeout,
                self.nameservers
            )
            tasks[record_type.lower()] = resolver.safe_query(domain)
        
        # 并发执行所有查询
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        # 将结果映射回字典
        return {
            f"{key}_records": value if not isinstance(value, Exception) else []
            for key, value in zip(tasks.keys(), results)
        }
    
    async def get_dns_info(self, domain: str) -> DNSInfo:
        """获取域名的完整DNS信息
        
        并发查询所有DNS记录和WHOIS信息，最大化性能
        
        Args:
            domain: 要查询的域名
            
        Returns:
            包含所有DNS记录的DNSInfo对象
            
        Example:
            >>> service = DNSService()
            >>> dns_info = await service.get_dns_info("example.com")
            >>> print(f"A记录数量: {len(dns_info.a_records)}")
        """
        try:
            # 规范化域名
            normalized_domain = self.normalizer.normalize(domain)
            
            # 创建并发任务列表
            tasks = [
                self._query_all_records(normalized_domain)
            ]
            
            # 如果启用WHOIS，添加WHOIS查询任务
            if self.enable_whois:
                tasks.append(AsyncWhoisService.query(normalized_domain))
            
            # 并发执行所有查询
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 提取DNS记录结果
            dns_records = results[0] if not isinstance(results[0], Exception) else {}
            
            # 提取WHOIS结果（如果启用）
            whois_info = None
            if self.enable_whois and len(results) > 1:
                whois_info = results[1] if not isinstance(results[1], Exception) else None
            
            # 构建DNSInfo对象
            return DNSInfo(
                domain=normalized_domain,
                a_records=dns_records.get('a_records', []),
                cname_records=dns_records.get('cname_records', []),
                mx_records=dns_records.get('mx_records', []),
                txt_records=dns_records.get('txt_records', []),
                ns_records=dns_records.get('ns_records', []),
                whois_info=whois_info
            )
            
        except Exception as e:
            # 返回包含错误信息的DNSInfo对象
            return DNSInfo(
                domain=domain,
                error=str(e)
            )
    
    async def get_dns_info_by_type(
        self,
        domain: str,
        record_type: str
    ) -> DNSInfo:
        """按指定类型查询DNS记录
        
        Args:
            domain: 要查询的域名
            record_type: 记录类型，可选值: 'A', 'AAAA', 'CNAME', 'MX', 'TXT', 'NS', 'WHOIS'
            
        Returns:
            只包含指定类型记录的DNSInfo对象
        """
        normalized_domain = self.normalizer.normalize(domain)
        dns_info = DNSInfo(domain=normalized_domain)
        
        try:
            record_type = record_type.upper()
            
            # WHOIS查询特殊处理
            if record_type == 'WHOIS':
                dns_info.whois_info = await AsyncWhoisService.query(normalized_domain)
                return dns_info
            
            # DNS记录查询
            resolver = DNSResolverFactory.get_resolver(
                record_type,
                self.timeout,
                self.nameservers
            )
            records = await resolver.safe_query(normalized_domain)
            
            # 根据类型设置对应的记录字段
            field_name = f"{record_type.lower()}_records"
            setattr(dns_info, field_name, records)
            
        except ValueError as e:
            dns_info.error = str(e)
        except Exception as e:
            dns_info.error = str(e)
        
        return dns_info
