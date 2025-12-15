"""缓存装饰器
优化版本：更清晰的逻辑和更好的类型安全
遵循 SOLID、DRY、KISS 原则
"""
import logging
import inspect
from functools import wraps
from typing import Callable, Any, get_type_hints, Optional
from fastapi import Request, Response
from pydantic import BaseModel

from app.cache.redis_cache import cache_manager, CacheKeyGenerator

logger = logging.getLogger(__name__)


class QueryParamExtractor:
    """查询参数提取器（单一职责原则）"""
    
    @staticmethod
    def extract(args: tuple, kwargs: dict) -> Optional[str]:
        """从函数参数中提取查询参数
        
        Args:
            args: 位置参数
            kwargs: 关键字参数
            
        Returns:
            查询参数字符串，未找到返回None
        """
        # 从位置参数提取
        if args and not isinstance(args[0], (Request, Response)):
            return str(args[0])
        
        # 从关键字参数提取
        for key in ('q', 'domain', 'ip', 'query'):
            if key in kwargs and kwargs[key]:
                return str(kwargs[key])
        
        return None


class ResponseHeaderManager:
    """响应头管理器（单一职责原则）"""
    
    @staticmethod
    def set_cache_hit(response: Optional[Response], cache_key: str):
        """设置缓存命中响应头"""
        if response:
            response.headers["X-Cache-Status"] = "HIT"
            response.headers["X-Cache-Key"] = cache_key
    
    @staticmethod
    def set_cache_miss(response: Optional[Response]):
        """设置缓存未命中响应头"""
        if response:
            response.headers["X-Cache-Status"] = "MISS"


class ResultValidator:
    """结果验证器（单一职责原则）"""
    
    @staticmethod
    def should_cache(result: Any) -> bool:
        """判断结果是否应该缓存
        
        Args:
            result: 查询结果
            
        Returns:
            是否应该缓存
        """
        # Pydantic模型检查
        if isinstance(result, BaseModel):
            return not (hasattr(result, 'error') and result.error)
        
        # 字典检查
        if isinstance(result, dict):
            return not result.get('error')
        
        return True


def cached(cache_prefix: str):
    """缓存装饰器
    
    用于API端点的缓存功能，自动处理缓存的读取和存储
    并在响应头中添加缓存命中标识
    
    Args:
        cache_prefix: 缓存键前缀（如：dns, ip, search）
        
    Usage:
        @cached("dns")
        async def get_dns_info(domain: str, response: Response):
            ...
    
    响应头:
        X-Cache-Status: HIT | MISS
        X-Cache-Key: 缓存键（仅在命中时）
    """
    def decorator(func: Callable) -> Callable:
        # 获取函数返回类型注解
        type_hints = get_type_hints(func)
        return_type = type_hints.get('return')
        
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # 提取响应对象
            response: Optional[Response] = kwargs.get('response')
            if not response:
                response = next((arg for arg in args if isinstance(arg, Response)), None)
            
            # 提取查询参数
            query_param = QueryParamExtractor.extract(args, kwargs)
            if not query_param:
                return await func(*args, **kwargs)
            
            # 尝试从缓存获取
            cached_result = await cache_manager.get(cache_prefix, query_param)
            
            if cached_result is not None:
                # 缓存命中
                cache_key = CacheKeyGenerator.generate(cache_prefix, query_param)
                logger.info(f"Cache HIT: {cache_prefix}:{query_param}")
                
                ResponseHeaderManager.set_cache_hit(response, cache_key)
                
                # 转换为正确的类型
                if return_type and inspect.isclass(return_type) and issubclass(return_type, BaseModel):
                    return return_type(**cached_result)
                return cached_result
            
            # 缓存未命中，执行原函数
            logger.info(f"Cache MISS: {cache_prefix}:{query_param}")
            result = await func(*args, **kwargs)
            
            ResponseHeaderManager.set_cache_miss(response)
            
            # 存储成功的结果到缓存
            if ResultValidator.should_cache(result):
                await cache_manager.set(cache_prefix, query_param, result)
                logger.info(f"Cache STORED: {cache_prefix}:{query_param}")
            
            return result
        
        return wrapper
    return decorator

