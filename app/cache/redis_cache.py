"""Redis缓存管理器"""
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Any
from redis import asyncio as aioredis
from pydantic import BaseModel

from app.config import settings


class CacheManager:
    """Redis缓存管理器
    
    负责缓存的存储、查询和过期管理
    """
    
    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None
        self._cache_ttl = 7 * 24 * 60 * 60  # 7天，单位：秒
    
    async def connect(self):
        """建立Redis连接"""
        if not self._redis:
            self._redis = await aioredis.from_url(
                settings.redis.url,
                encoding="utf-8",
                decode_responses=True
            )
    
    async def close(self):
        """关闭Redis连接"""
        if self._redis:
            await self._redis.close()
            self._redis = None
    
    def _generate_cache_key(self, prefix: str, query: str) -> str:
        """生成缓存键
        
        Args:
            prefix: 缓存键前缀（如：dns, ip, search）
            query: 查询参数
            
        Returns:
            str: 缓存键
        """
        # 使用MD5生成查询参数的哈希值，确保键的唯一性和长度可控
        query_hash = hashlib.md5(query.lower().encode()).hexdigest()
        return f"inforecon:{prefix}:{query_hash}"
    
    async def get(self, prefix: str, query: str) -> Optional[dict]:
        """从缓存获取数据
        
        Args:
            prefix: 缓存键前缀
            query: 查询参数
            
        Returns:
            Optional[dict]: 缓存的数据，如果不存在或已过期则返回None
        """
        if not self._redis:
            await self.connect()
        
        cache_key = self._generate_cache_key(prefix, query)
        cached_data = await self._redis.get(cache_key)
        
        if not cached_data:
            return None
        
        try:
            data = json.loads(cached_data)
            # 检查缓存是否在7天内
            cached_time = datetime.fromisoformat(data.get("cached_at"))
            if datetime.now() - cached_time > timedelta(days=7):
                # 缓存已过期，删除并返回None
                await self._redis.delete(cache_key)
                return None
            
            return data.get("result")
        except (json.JSONDecodeError, ValueError, KeyError):
            # 缓存数据损坏，删除
            await self._redis.delete(cache_key)
            return None
    
    async def set(self, prefix: str, query: str, result: Any):
        """将数据存入缓存
        
        Args:
            prefix: 缓存键前缀
            query: 查询参数
            result: 要缓存的结果（支持Pydantic模型或字典）
        """
        if not self._redis:
            await self.connect()
        
        cache_key = self._generate_cache_key(prefix, query)
        
        # 如果result是Pydantic模型，转换为字典
        if isinstance(result, BaseModel):
            result_dict = result.model_dump(mode='json')
        else:
            result_dict = result
        
        cache_data = {
            "cached_at": datetime.now().isoformat(),
            "query": query,
            "result": result_dict
        }
        
        # 存储到Redis，设置TTL为7天
        await self._redis.setex(
            cache_key,
            self._cache_ttl,
            json.dumps(cache_data, ensure_ascii=False)
        )


# 全局缓存管理器实例
cache_manager = CacheManager()

