import aiodns
import geoip2.database
from typing import Optional
from pathlib import Path

from app.schema.ip_schema import IPInfo


class IPService:
    """IP信息查询服务
    
    提供IP反查域名和地理位置查询功能
    """
    
    def __init__(self, geoip_db_path: Optional[str] = None, timeout: float = 5.0):
        """初始化IP服务
        
        Args:
            geoip_db_path: GeoLite2数据库文件路径，默认使用项目中的数据库
            timeout: DNS查询超时时间(秒)
        """
        self.timeout = timeout
        self.resolver = aiodns.DNSResolver(timeout=timeout)
        
        # 设置GeoIP数据库路径
        if geoip_db_path is None:
            # 默认使用项目中的GeoLite2-Country数据库
            project_root = Path(__file__).parent.parent.parent
            geoip_db_path = project_root / "data" / "GeoLite2-Country" / "GeoLite2-Country.mmdb"
        
        self.geoip_reader = geoip2.database.Reader(str(geoip_db_path))
    
    
    def _get_country(self, ip: str) -> Optional[str]:
        """获取IP地址对应的国家
        
        使用GeoIP2数据库查询IP地址所属国家
        
        Args:
            ip: 要查询的IP地址
            
        Returns:
            国家名称，如果查询失败返回None
        """
        try:
            response = self.geoip_reader.country(ip)
            # 优先返回中文名称，如果没有则返回英文名称
            country_name = response.country.names.get('zh-CN')
            if not country_name:
                country_name = response.country.name
            return country_name
        except Exception:
            # 如果查询失败（如私有IP、数据库中不存在等），返回None
            return None
    
    async def get_ip_info(self, ip: str) -> IPInfo:
        """获取IP的完整信息
        
        查询指定IP的反向DNS记录和地理位置信息
        
        Args:
            ip: 要查询的IP地址
            
        Returns:
            包含域名列表和国家信息的IPInfo对象
            
        Example:
            >>> service = IPService()
            >>> ip_info = await service.get_ip_info("8.8.8.8")
            >>> print(f"域名: {ip_info.domains}")
            >>> print(f"国家: {ip_info.country}")
        """
        # 清理IP地址
        ip = ip.strip()
        
        # 并发执行反向DNS查询和地理位置查询
        country = self._get_country(ip)
        
        return IPInfo(
            ip=ip,
            country=country
        )
    
    def __del__(self):
        """清理资源"""
        try:
            if hasattr(self, 'geoip_reader'):
                self.geoip_reader.close()
        except Exception:
            pass

