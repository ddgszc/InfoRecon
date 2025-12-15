"""IP信息查询服务
完全异步架构，支持高并发查询
"""
import asyncio
import geoip2.database
from typing import Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from app.schema.ip_schema import IPInfo


class GeoIPReader:
    """GeoIP数据库读取器（单一职责原则）
    
    使用线程池执行同步的GeoIP查询，避免阻塞事件循环
    """
    
    _executor: Optional[ThreadPoolExecutor] = None
    _reader: Optional[geoip2.database.Reader] = None
    _max_workers = 5
    
    @classmethod
    def initialize(cls, db_path: Optional[str] = None):
        """初始化GeoIP读取器"""
        if cls._reader is None:
            if db_path is None:
                # 默认使用项目中的GeoLite2-Country数据库
                project_root = Path(__file__).parent.parent.parent
                db_path = project_root / "data" / "GeoLite2-Country" / "GeoLite2-Country.mmdb"
            
            cls._reader = geoip2.database.Reader(str(db_path))
        
        if cls._executor is None:
            cls._executor = ThreadPoolExecutor(
                max_workers=cls._max_workers,
                thread_name_prefix="geoip"
            )
    
    @classmethod
    def _sync_query_country(cls, ip: str) -> Optional[str]:
        """同步查询国家信息（在线程池中执行）"""
        try:
            if cls._reader is None:
                return None
            
            response = cls._reader.country(ip)
            # 优先返回中文名称，否则返回英文名称
            return response.country.names.get('zh-CN') or response.country.name
        except Exception:
            return None
    
    @classmethod
    async def query_country(cls, ip: str) -> Optional[str]:
        """异步查询IP所属国家
        
        Args:
            ip: IP地址
            
        Returns:
            国家名称，失败返回None
        """
        if cls._executor is None:
            cls.initialize()
        
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                cls._executor,
                cls._sync_query_country,
                ip
            )
            return result
        except Exception:
            return None
    
    @classmethod
    async def shutdown(cls):
        """关闭资源"""
        if cls._executor:
            cls._executor.shutdown(wait=True)
            cls._executor = None
        
        if cls._reader:
            cls._reader.close()
            cls._reader = None


class IPService:
    """IP信息查询服务
    
    提供IP地理位置查询功能
    使用组合模式（组合优于依赖）
    """
    
    def __init__(self, geoip_db_path: Optional[str] = None):
        """初始化IP服务
        
        Args:
            geoip_db_path: GeoLite2数据库文件路径，默认使用项目中的数据库
        """
        # 初始化GeoIP读取器
        GeoIPReader.initialize(geoip_db_path)
    
    @staticmethod
    def _normalize_ip(ip: str) -> str:
        """规范化IP地址"""
        return ip.strip()
    
    async def get_ip_info(self, ip: str) -> IPInfo:
        """获取IP的完整信息
        
        查询指定IP的地理位置信息
        
        Args:
            ip: 要查询的IP地址
            
        Returns:
            包含国家信息的IPInfo对象
            
        Example:
            >>> service = IPService()
            >>> ip_info = await service.get_ip_info("8.8.8.8")
            >>> print(f"国家: {ip_info.country}")
        """
        # 规范化IP地址
        normalized_ip = self._normalize_ip(ip)
        
        # 查询地理位置
        country = await GeoIPReader.query_country(normalized_ip)
        
        return IPInfo(
            ip=normalized_ip,
            country=country
        )
    
    async def batch_get_ip_info(self, ips: list[str]) -> list[IPInfo]:
        """批量查询IP信息（支持高并发）
        
        Args:
            ips: IP地址列表
            
        Returns:
            IPInfo对象列表
        """
        tasks = [self.get_ip_info(ip) for ip in ips]
        return await asyncio.gather(*tasks, return_exceptions=False)
