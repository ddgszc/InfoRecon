"""Redis缓存管理器
优化版本：支持连接池、批量操作和管道
遵循 SOLID、DRY、KISS 原则
"""
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Any, List, Dict
from redis import asyncio as aioredis
from pydantic import BaseModel

from app.config import settings


class CacheKeyGenerator:
    """缓存键生成器（单一职责原则）"""
    
    @staticmethod
    def generate(prefix: str, query: str) -> str:
        """生成缓存键
        
        Args:
            prefix: 缓存键前缀（如：dns, ip, search）
            query: 查询参数
            
        Returns:
            缓存键
        """
        query_hash = hashlib.md5(query.lower().encode()).hexdigest()
        return f"inforecon:{prefix}:{query_hash}"


class CacheSerializer:
    """缓存序列化器（单一职责原则）"""
    
    @staticmethod
    def serialize(result: Any, query: str) -> str:
        """序列化缓存数据
        
        Args:
            result: 要缓存的结果（支持Pydantic模型或字典）
            query: 查询参数
            
        Returns:
            JSON字符串
        """
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
        
        return json.dumps(cache_data, ensure_ascii=False)
    
    @staticmethod
    def deserialize(cached_data: str, max_age_days: int = 15) -> Optional[dict]:
        """反序列化缓存数据
        
        Args:
            cached_data: 缓存的JSON字符串
            max_age_days: 最大缓存天数
            
        Returns:
            缓存的结果字典，如果过期或损坏返回None
        """
        try:
            data = json.loads(cached_data)
            
            # 检查缓存是否过期
            cached_time = datetime.fromisoformat(data.get("cached_at"))
            if datetime.now() - cached_time > timedelta(days=max_age_days):
                return None
            
            return data.get("result")
        except (json.JSONDecodeError, ValueError, KeyError):
            return None


class CacheManager:
    """Redis缓存管理器
    
    负责缓存的存储、查询、批量操作和过期管理
    使用连接池提升性能
    """
    
    def __init__(
        self,
        cache_ttl: int = 7 * 24 * 60 * 60,  # 7天，单位：秒
        max_connections: int = 50
    ):
        """初始化缓存管理器
        
        Args:
            cache_ttl: 缓存过期时间(秒)
            max_connections: 最大连接数
        """
        self._redis: Optional[aioredis.Redis] = None
        self._cache_ttl = cache_ttl
        self._max_connections = max_connections
        self._key_generator = CacheKeyGenerator()
        self._serializer = CacheSerializer()
    
    async def connect(self):
        """建立Redis连接（使用连接池）"""
        if not self._redis:
            self._redis = await aioredis.from_url(
                settings.redis.url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=self._max_connections
            )
    
    async def close(self):
        """关闭Redis连接"""
        if self._redis:
            await self._redis.close()
            self._redis = None
    
    async def get(self, prefix: str, query: str) -> Optional[dict]:
        """从缓存获取数据
        
        Args:
            prefix: 缓存键前缀
            query: 查询参数
            
        Returns:
            缓存的数据，如果不存在或已过期则返回None
        """
        if not self._redis:
            await self.connect()
        
        cache_key = self._key_generator.generate(prefix, query)
        cached_data = await self._redis.get(cache_key)
        
        if not cached_data:
            return None
        
        result = self._serializer.deserialize(cached_data)
        
        # 如果数据已过期或损坏，删除缓存
        if result is None:
            await self._redis.delete(cache_key)
        
        return result
    
    async def set(self, prefix: str, query: str, result: Any):
        """将数据存入缓存
        
        Args:
            prefix: 缓存键前缀
            query: 查询参数
            result: 要缓存的结果（支持Pydantic模型或字典）
        """
        if not self._redis:
            await self.connect()
        
        cache_key = self._key_generator.generate(prefix, query)
        cache_data = self._serializer.serialize(result, query)
        
        # 存储到Redis，设置TTL
        await self._redis.setex(
            cache_key,
            self._cache_ttl,
            cache_data
        )
    
    async def batch_get(
        self,
        prefix: str,
        queries: List[str]
    ) -> Dict[str, Optional[dict]]:
        """批量获取缓存数据（使用管道优化）
        
        Args:
            prefix: 缓存键前缀
            queries: 查询参数列表
            
        Returns:
            字典：{查询参数: 缓存结果}
        """
        if not self._redis:
            await self.connect()
        
        # 生成所有缓存键
        cache_keys = [
            self._key_generator.generate(prefix, query)
            for query in queries
        ]
        
        # 使用管道批量获取
        pipeline = self._redis.pipeline()
        for key in cache_keys:
            pipeline.get(key)
        
        cached_values = await pipeline.execute()
        
        # 解析结果
        results = {}
        keys_to_delete = []
        
        for query, cached_data, cache_key in zip(queries, cached_values, cache_keys):
            if cached_data:
                result = self._serializer.deserialize(cached_data)
                if result is None:
                    keys_to_delete.append(cache_key)
                results[query] = result
            else:
                results[query] = None
        
        # 删除过期或损坏的缓存
        if keys_to_delete:
            await self._redis.delete(*keys_to_delete)
        
        return results
    
    async def batch_set(
        self,
        prefix: str,
        data: Dict[str, Any]
    ):
        """批量存储缓存数据（使用管道优化）
        
        Args:
            prefix: 缓存键前缀
            data: 字典：{查询参数: 结果}
        """
        if not self._redis:
            await self.connect()
        
        # 使用管道批量存储
        pipeline = self._redis.pipeline()
        
        for query, result in data.items():
            cache_key = self._key_generator.generate(prefix, query)
            cache_data = self._serializer.serialize(result, query)
            pipeline.setex(cache_key, self._cache_ttl, cache_data)
        
        await pipeline.execute()
    
    async def delete(self, prefix: str, query: str) -> bool:
        """删除缓存
        
        Args:
            prefix: 缓存键前缀
            query: 查询参数
            
        Returns:
            是否删除成功
        """
        if not self._redis:
            await self.connect()
        
        cache_key = self._key_generator.generate(prefix, query)
        result = await self._redis.delete(cache_key)
        return result > 0
    
    async def exists(self, prefix: str, query: str) -> bool:
        """检查缓存是否存在
        
        Args:
            prefix: 缓存键前缀
            query: 查询参数
            
        Returns:
            是否存在
        """
        if not self._redis:
            await self.connect()
        
        cache_key = self._key_generator.generate(prefix, query)
        return await self._redis.exists(cache_key) > 0
    
    async def get_ttl(self, prefix: str, query: str) -> int:
        """获取缓存剩余过期时间
        
        Args:
            prefix: 缓存键前缀
            query: 查询参数
            
        Returns:
            剩余秒数，-1表示永久，-2表示不存在
        """
        if not self._redis:
            await self.connect()
        
        cache_key = self._key_generator.generate(prefix, query)
        return await self._redis.ttl(cache_key)


# 全局缓存管理器实例
cache_manager = CacheManager()
