import ipaddress
import socket
import requests
from typing import Optional
from datetime import datetime

from app.schema.ip_schema import IPInfo, GeoLocation, ASNInfo


class IPService:
    """IP信息查询服务
    
    提供IP地址的详细信息查询，包括地理位置、ASN信息、反向DNS等
    """
    
    def __init__(self, timeout: float = 5.0, api_key: Optional[str] = None):
        """初始化IP服务
        
        Args:
            timeout: 请求超时时间(秒)
            api_key: IP地理位置API密钥(可选，某些服务需要)
        """
        self.timeout = timeout
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'InfoRecon/1.0'
        })
    
    def _validate_ip(self, ip: str) -> bool:
        """验证IP地址格式是否正确
        
        Args:
            ip: IP地址字符串
            
        Returns:
            是否为有效的IP地址
        """
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def _get_ip_version(self, ip: str) -> Optional[int]:
        """获取IP地址版本
        
        Args:
            ip: IP地址字符串
            
        Returns:
            4表示IPv4，6表示IPv6，None表示无效IP
        """
        try:
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.version
        except ValueError:
            return None
    
    def _is_private_ip(self, ip: str) -> bool:
        """判断是否为私有IP地址
        
        私有IP地址范围：
        - IPv4: 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
        - IPv6: fc00::/7
        
        Args:
            ip: IP地址字符串
            
        Returns:
            是否为私有IP
        """
        try:
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.is_private
        except ValueError:
            return False
    
    def _get_reverse_dns(self, ip: str) -> Optional[str]:
        """获取反向DNS解析结果
        
        通过IP地址反向查询对应的域名
        
        Args:
            ip: IP地址字符串
            
        Returns:
            域名或None
        """
        try:
            hostname, _, _ = socket.gethostbyaddr(ip)
            return hostname
        except (socket.herror, socket.gaierror, socket.timeout):
            return None
    
    def _get_geo_location_from_ipapi(self, ip: str) -> Optional[GeoLocation]:
        """从ip-api.com获取地理位置信息
        
        使用免费的ip-api.com服务获取IP地理位置
        注意：免费版有请求限制(45次/分钟)
        
        Args:
            ip: IP地址字符串
            
        Returns:
            GeoLocation对象或None
        """
        try:
            url = f"http://ip-api.com/json/{ip}"
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 'success':
                return GeoLocation(
                    country=data.get('country'),
                    country_code=data.get('countryCode'),
                    region=data.get('regionName'),
                    region_code=data.get('region'),
                    city=data.get('city'),
                    zip_code=data.get('zip'),
                    latitude=data.get('lat'),
                    longitude=data.get('lon'),
                    timezone=data.get('timezone'),
                    isp=data.get('isp'),
                    org=data.get('org'),
                    as_number=data.get('as')
                )
        except Exception:
            pass
        return None
    
    def _get_asn_info(self, ip: str) -> Optional[ASNInfo]:
        """获取ASN(自治系统号)信息
        
        ASN用于标识互联网上的自治系统，通常对应一个ISP或大型组织
        
        Args:
            ip: IP地址字符串
            
        Returns:
            ASNInfo对象或None
        """
        try:
            # 使用ip-api.com获取ASN信息
            url = f"http://ip-api.com/json/{ip}?fields=status,as,isp,org"
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 'success':
                as_info = data.get('as', '')
                asn = None
                asn_name = None
                
                # 解析AS信息，格式通常为 "AS15169 Google LLC"
                if as_info:
                    parts = as_info.split(' ', 1)
                    if parts[0].startswith('AS'):
                        asn = parts[0][2:]  # 移除"AS"前缀
                        asn_name = parts[1] if len(parts) > 1 else None
                
                return ASNInfo(
                    asn=asn,
                    name=asn_name,
                    organization=data.get('org'),
                    isp=data.get('isp')
                )
        except Exception:
            pass
        return None
    
    def get_ip_info(self, ip: str) -> IPInfo:
        """获取IP地址的完整信息
        
        查询指定IP地址的详细信息，包括：
        - 基本信息：IP版本、是否私有IP
        - 反向DNS解析
        - 地理位置信息
        - ASN信息
        
        Args:
            ip: 要查询的IP地址
            
        Returns:
            包含所有信息的IPInfo对象
            
        Example:
            >>> service = IPService()
            >>> ip_info = service.get_ip_info("8.8.8.8")
            >>> print(f"国家: {ip_info.geo_location.country}")
            >>> print(f"ISP: {ip_info.asn_info.isp}")
        """
        try:
            # 验证IP地址
            ip = ip.strip()
            if not self._validate_ip(ip):
                return IPInfo(
                    ip=ip,
                    query_time=datetime.now(),
                    error="无效的IP地址格式"
                )
            
            # 获取基本信息
            ip_version = self._get_ip_version(ip)
            is_private = self._is_private_ip(ip)
            reverse_dns = self._get_reverse_dns(ip)
            
            # 对于私有IP，不查询地理位置和ASN信息
            geo_location = None
            asn_info = None
            
            if not is_private:
                geo_location = self._get_geo_location_from_ipapi(ip)
                asn_info = self._get_asn_info(ip)
            
            return IPInfo(
                ip=ip,
                query_time=datetime.now(),
                ip_version=ip_version,
                is_private=is_private,
                reverse_dns=reverse_dns,
                geo_location=geo_location,
                asn_info=asn_info
            )
            
        except Exception as e:
            return IPInfo(
                ip=ip,
                query_time=datetime.now(),
                error=str(e)
            )
    
    def get_my_ip(self) -> Optional[str]:
        """获取本机的公网IP地址
        
        Returns:
            公网IP地址字符串或None
        """
        try:
            response = self.session.get('https://api.ipify.org', timeout=self.timeout)
            response.raise_for_status()
            return response.text.strip()
        except Exception:
            # 尝试备用服务
            try:
                response = self.session.get('https://ifconfig.me/ip', timeout=self.timeout)
                response.raise_for_status()
                return response.text.strip()
            except Exception:
                return None
    
    def batch_get_ip_info(self, ips: list[str]) -> list[IPInfo]:
        """批量查询IP信息
        
        Args:
            ips: IP地址列表
            
        Returns:
            IPInfo对象列表
        """
        results = []
        for ip in ips:
            results.append(self.get_ip_info(ip))
        return results

