import dns.resolver
import whois
from typing import Optional
from datetime import datetime

from app.schema.dns_schema import (
    DNSInfo,
    ARecord,
    AAAARecord,
    CNAMERecord,
    MXRecord,
    TXTRecord,
    NSRecord,
    WhoisInfo
)


class DNSService:
    """DNS信息查询服务
    
    提供各类DNS记录的查询功能，包括A、AAAA、CNAME、MX、TXT、NS记录
    """
    
    def __init__(self, timeout: float = 5.0, nameservers: Optional[list] = None):
        """初始化DNS服务
        
        Args:
            timeout: DNS查询超时时间(秒)
            nameservers: 自定义DNS服务器列表，如 ['8.8.8.8', '8.8.4.4']
        """
        self.timeout = timeout
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = timeout
        self.resolver.lifetime = timeout
        
        if nameservers:
            self.resolver.nameservers = nameservers
    
    def _query_a_records(self, domain: str) -> list[ARecord]:
        """查询A记录 - IPv4地址记录
        
        A记录将域名映射到IPv4地址，是最常用的DNS记录类型
        
        Args:
            domain: 要查询的域名
            
        Returns:
            A记录列表
        """
        records = []
        try:
            answers = self.resolver.resolve(domain, 'A')
            for rdata in answers:
                records.append(ARecord(
                    ip=str(rdata),
                    ttl=answers.rrset.ttl
                ))
        except Exception:
            # 如果查询失败，返回空列表
            pass
        return records
    
    def _query_aaaa_records(self, domain: str) -> list[AAAARecord]:
        """查询AAAA记录 - IPv6地址记录
        
        AAAA记录将域名映射到IPv6地址，用于支持IPv6协议
        
        Args:
            domain: 要查询的域名
            
        Returns:
            AAAA记录列表
        """
        records = []
        try:
            answers = self.resolver.resolve(domain, 'AAAA')
            for rdata in answers:
                records.append(AAAARecord(
                    ip=str(rdata),
                    ttl=answers.rrset.ttl
                ))
        except Exception:
            pass
        return records
    
    def _query_mx_records(self, domain: str) -> list[MXRecord]:
        """查询MX记录 - 邮件交换记录
        
        MX记录指定接收电子邮件的邮件服务器
        priority值越小优先级越高，邮件服务器会优先尝试priority值小的服务器
        
        Args:
            domain: 要查询的域名
            
        Returns:
            MX记录列表
        """
        records = []
        try:
            answers = self.resolver.resolve(domain, 'MX')
            for rdata in answers:
                records.append(MXRecord(
                    priority=rdata.preference,
                    exchange=str(rdata.exchange).rstrip('.'),
                    ttl=answers.rrset.ttl
                ))
        except Exception:
            pass
        return records
    
    def _query_txt_records(self, domain: str) -> list[TXTRecord]:
        """查询TXT记录 - 文本记录
        
        只返回SPF记录（v=spf开头的TXT记录）
        SPF记录用于防止邮件伪造
        
        Args:
            domain: 要查询的域名
            
        Returns:
            TXT记录列表（仅包含SPF记录）
        """
        records = []
        try:
            answers = self.resolver.resolve(domain, 'TXT')
            for rdata in answers:
                # TXT记录可能包含多个字符串，需要合并
                text = ''.join([s.decode() if isinstance(s, bytes) else str(s) for s in rdata.strings])
                # 只保留SPF记录
                if text.startswith('v=spf'):
                    records.append(TXTRecord(
                        text=text,
                        ttl=answers.rrset.ttl
                    ))
        except Exception:
            pass
        return records
    
    def _query_ns_records(self, domain: str) -> list[NSRecord]:
        """查询NS记录 - 域名服务器记录
        
        NS记录指定该域名由哪台域名服务器进行解析
        一个域名通常有多个NS记录以提供冗余和负载均衡
        
        Args:
            domain: 要查询的域名
            
        Returns:
            NS记录列表
        """
        records = []
        try:
            answers = self.resolver.resolve(domain, 'NS')
            for rdata in answers:
                records.append(NSRecord(
                    nameserver=str(rdata).rstrip('.'),
                    ttl=answers.rrset.ttl
                ))
        except Exception:
            pass
        return records
    
    def _query_cname_records(self, domain: str) -> list[CNAMERecord]:
        """查询CNAME记录 - 别名记录
        
        CNAME记录将一个域名指向另一个域名，用于域名别名
        通常用于CDN、负载均衡等场景
        
        Args:
            domain: 要查询的域名
            
        Returns:
            CNAME记录列表
        """
        records = []
        try:
            answers = self.resolver.resolve(domain, 'CNAME')
            for rdata in answers:
                records.append(CNAMERecord(
                    target=str(rdata.target).rstrip('.'),
                    ttl=answers.rrset.ttl
                ))
        except Exception:
            pass
        return records
    
    def _query_whois_info(self, domain: str) -> Optional[WhoisInfo]:
        """查询WHOIS信息 - 域名注册信息
        
        查询域名的注册商、状态、注册时间、更新时间和到期时间等信息
        
        Args:
            domain: 要查询的域名
            
        Returns:
            WhoisInfo对象，如果查询失败返回None
        """
        try:
            w = whois.whois(domain)
            
            # 处理日期字段 - whois库可能返回单个日期或日期列表
            def get_first_date(date_value):
                if isinstance(date_value, list):
                    return date_value[0] if date_value else None
                return date_value
            
            # 处理状态字段 - 可能是字符串或列表
            status = w.status
            if isinstance(status, str):
                status = [status]
            elif status is None:
                status = []
            
            return WhoisInfo(
                registrar=w.registrar,
                status=status,
                creation_date=get_first_date(w.creation_date),
                updated_date=get_first_date(w.updated_date),
                expiration_date=get_first_date(w.expiration_date)
            )
        except Exception:
            # WHOIS查询失败时返回None
            return None
    
    async def get_dns_info(self, domain: str) -> DNSInfo:
        """获取域名的完整DNS信息
        
        查询指定域名的所有DNS记录，包括A、AAAA、CNAME、MX、TXT、NS记录
        
        Args:
            domain: 要查询的域名
            
        Returns:
            包含所有DNS记录的DNSInfo对象
            
        Example:
            >>> service = DNSService()
            >>> dns_info = service.get_dns_info("example.com")
            >>> print(f"A记录数量: {len(dns_info.a_records)}")
            >>> print(f"MX记录: {dns_info.mx_records}")
        """
        try:
            # 移除域名前后的空格和可能的协议前缀
            domain = domain.strip().lower()
            if domain.startswith('http://'):
                domain = domain[7:]
            elif domain.startswith('https://'):
                domain = domain[8:]
            
            # 移除路径部分
            if '/' in domain:
                domain = domain.split('/')[0]
            
            # 查询所有类型的DNS记录
            dns_info = DNSInfo(
                domain=domain,
                a_records=self._query_a_records(domain),
                # aaaa_records=self._query_aaaa_records(domain),
                cname_records=self._query_cname_records(domain),
                mx_records=self._query_mx_records(domain),
                txt_records=self._query_txt_records(domain),
                ns_records=self._query_ns_records(domain),
                whois_info=self._query_whois_info(domain)
            )
            
            return dns_info
            
        except Exception as e:
            # 如果发生错误，返回包含错误信息的DNSInfo对象
            return DNSInfo(
                domain=domain,
                query_time=datetime.now(),
                error=str(e)
            )
    
    def get_dns_info_by_type(self, domain: str, record_type: str) -> DNSInfo:
        """按指定类型查询DNS记录
        
        Args:
            domain: 要查询的域名
            record_type: 记录类型，可选值: 'A', 'AAAA', 'CNAME', 'MX', 'TXT', 'NS'
            
        Returns:
            只包含指定类型记录的DNSInfo对象
        """
        domain = domain.strip().lower()
        if domain.startswith('http://'):
            domain = domain[7:]
        elif domain.startswith('https://'):
            domain = domain[8:]
        if '/' in domain:
            domain = domain.split('/')[0]
        
        dns_info = DNSInfo(domain=domain, query_time=datetime.now())
        
        try:
            record_type = record_type.upper()
            if record_type == 'A':
                dns_info.a_records = self._query_a_records(domain)
            elif record_type == 'AAAA':
                dns_info.aaaa_records = self._query_aaaa_records(domain)
            elif record_type == 'CNAME':
                dns_info.cname_records = self._query_cname_records(domain)
            elif record_type == 'MX':
                dns_info.mx_records = self._query_mx_records(domain)
            elif record_type == 'TXT':
                dns_info.txt_records = self._query_txt_records(domain)
            elif record_type == 'NS':
                dns_info.ns_records = self._query_ns_records(domain)
            elif record_type == 'WHOIS':
                dns_info.whois_info = self._query_whois_info(domain)
            else:
                dns_info.error = f"不支持的记录类型: {record_type}"
        except Exception as e:
            dns_info.error = str(e)
        
        return dns_info

