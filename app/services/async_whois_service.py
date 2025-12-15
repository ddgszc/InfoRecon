"""异步WHOIS查询服务
使用线程池执行同步WHOIS查询，避免阻塞事件循环
"""
import asyncio
import whois
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from app.schema.dns_schema import WhoisInfo


class AsyncWhoisService:
    """异步WHOIS查询服务（单一职责原则）"""
    
    # 类级别线程池，复用线程（单例模式）
    _executor: Optional[ThreadPoolExecutor] = None
    _max_workers = 5
    
    @classmethod
    def get_executor(cls) -> ThreadPoolExecutor:
        """获取线程池（延迟初始化）"""
        if cls._executor is None:
            cls._executor = ThreadPoolExecutor(
                max_workers=cls._max_workers,
                thread_name_prefix="whois"
            )
        return cls._executor
    
    @classmethod
    async def shutdown(cls):
        """关闭线程池"""
        if cls._executor:
            cls._executor.shutdown(wait=True)
            cls._executor = None
    
    @staticmethod
    def _sync_whois_query(domain: str) -> Optional[WhoisInfo]:
        """同步WHOIS查询（在线程池中执行）"""
        try:
            w = whois.whois(domain)
            
            # 提取第一个日期（处理列表或单值）
            def extract_first_date(date_value) -> Optional[datetime]:
                if isinstance(date_value, list):
                    return date_value[0] if date_value else None
                return date_value
            
            # 规范化状态列表
            status = w.status
            if isinstance(status, str):
                status = [status]
            elif status is None:
                status = []
            
            return WhoisInfo(
                registrar=w.registrar,
                status=status,
                creation_date=extract_first_date(w.creation_date),
                updated_date=extract_first_date(w.updated_date),
                expiration_date=extract_first_date(w.expiration_date)
            )
        except Exception:
            return None
    
    @classmethod
    async def query(cls, domain: str) -> Optional[WhoisInfo]:
        """异步WHOIS查询
        
        将同步WHOIS查询放到线程池中执行，避免阻塞事件循环
        
        Args:
            domain: 要查询的域名
            
        Returns:
            WhoisInfo对象，失败返回None
        """
        loop = asyncio.get_event_loop()
        executor = cls.get_executor()
        
        try:
            result = await loop.run_in_executor(
                executor,
                cls._sync_whois_query,
                domain
            )
            return result
        except Exception:
            return None

