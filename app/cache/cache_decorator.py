"""缓存装饰器"""
import logging
import inspect
from functools import wraps
from typing import Callable, Any, get_type_hints
from fastapi import Request, Response
from pydantic import BaseModel

from app.cache.redis_cache import cache_manager

logger = logging.getLogger(__name__)


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
            # 提取 Response 对象
            response: Response = kwargs.get('response')
            if not response:
                for arg in args:
                    if isinstance(arg, Response):
                        response = arg
                        break
            
            # 提取查询参数
            query_param = None
            if args and not isinstance(args[0], (Request, Response)):
                query_param = str(args[0])
            else:
                query_param = kwargs.get('q') or kwargs.get('domain') or kwargs.get('ip')
                if query_param:
                    query_param = str(query_param)
            
            if not query_param:
                return await func(*args, **kwargs)
            
            # 尝试从缓存获取
            cached_result = await cache_manager.get(cache_prefix, query_param)
            if cached_result is not None:
                cache_key = cache_manager._generate_cache_key(cache_prefix, query_param)
                logger.info(f"Cache HIT: {cache_prefix}:{query_param}")
                
                if response:
                    response.headers["X-Cache-Status"] = "HIT"
                    response.headers["X-Cache-Key"] = cache_key
                
                # 使用类型注解将字典转换为 Pydantic 模型
                if return_type and inspect.isclass(return_type) and issubclass(return_type, BaseModel):
                    return return_type(**cached_result)
                return cached_result
            
            # 缓存未命中，执行原函数
            logger.info(f"Cache MISS: {cache_prefix}:{query_param}")
            result = await func(*args, **kwargs)
            
            if response:
                response.headers["X-Cache-Status"] = "MISS"
            
            # 存储成功的结果到缓存
            should_cache = True
            if isinstance(result, BaseModel):
                should_cache = not (hasattr(result, 'error') and result.error)
            elif isinstance(result, dict):
                should_cache = not result.get('error')
            
            if should_cache:
                await cache_manager.set(cache_prefix, query_param, result)
                logger.info(f"Cache STORED: {cache_prefix}:{query_param}")
            
            return result
        
        return wrapper
    return decorator

