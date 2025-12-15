"""并发查询协调器
支持批量查询、限流和超时控制
遵循 SOLID 原则
"""
import asyncio
from typing import List, TypeVar, Generic, Callable, Awaitable, Optional
from dataclasses import dataclass
from enum import Enum

T = TypeVar('T')
R = TypeVar('R')


class QueryStatus(Enum):
    """查询状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class QueryResult(Generic[T]):
    """查询结果封装
    
    提供统一的查询结果格式
    """
    query: str
    status: QueryStatus
    result: Optional[T] = None
    error: Optional[str] = None
    duration: float = 0.0


class RateLimiter:
    """速率限制器（单一职责原则）
    
    使用信号量实现并发控制
    """
    
    def __init__(self, max_concurrent: int = 10):
        """初始化速率限制器
        
        Args:
            max_concurrent: 最大并发查询数
        """
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def acquire(self):
        """获取执行许可"""
        await self.semaphore.acquire()
    
    def release(self):
        """释放执行许可"""
        self.semaphore.release()


class ConcurrentQueryCoordinator(Generic[T]):
    """并发查询协调器
    
    提供批量查询、限流、超时控制等功能
    遵循开闭原则：对扩展开放，对修改关闭
    """
    
    def __init__(
        self,
        query_func: Callable[[str], Awaitable[T]],
        max_concurrent: int = 10,
        timeout: float = 30.0
    ):
        """初始化协调器
        
        Args:
            query_func: 查询函数（接收查询参数，返回结果）
            max_concurrent: 最大并发数
            timeout: 单个查询超时时间(秒)
        """
        self.query_func = query_func
        self.rate_limiter = RateLimiter(max_concurrent)
        self.timeout = timeout
    
    async def _execute_single_query(self, query: str) -> QueryResult[T]:
        """执行单个查询（带限流和超时控制）
        
        Args:
            query: 查询参数
            
        Returns:
            QueryResult对象
        """
        import time
        start_time = time.time()
        
        try:
            # 获取执行许可（限流）
            await self.rate_limiter.acquire()
            
            try:
                # 执行查询（带超时）
                result = await asyncio.wait_for(
                    self.query_func(query),
                    timeout=self.timeout
                )
                
                duration = time.time() - start_time
                
                return QueryResult(
                    query=query,
                    status=QueryStatus.COMPLETED,
                    result=result,
                    duration=duration
                )
                
            except asyncio.TimeoutError:
                return QueryResult(
                    query=query,
                    status=QueryStatus.TIMEOUT,
                    error=f"查询超时 (>{self.timeout}秒)",
                    duration=time.time() - start_time
                )
            
            except Exception as e:
                return QueryResult(
                    query=query,
                    status=QueryStatus.FAILED,
                    error=str(e),
                    duration=time.time() - start_time
                )
            
            finally:
                # 释放执行许可
                self.rate_limiter.release()
        
        except Exception as e:
            return QueryResult(
                query=query,
                status=QueryStatus.FAILED,
                error=f"协调器错误: {str(e)}",
                duration=time.time() - start_time
            )
    
    async def execute_batch(self, queries: List[str]) -> List[QueryResult[T]]:
        """批量执行查询
        
        并发执行多个查询，自动进行限流和超时控制
        
        Args:
            queries: 查询参数列表
            
        Returns:
            QueryResult对象列表
            
        Example:
            >>> coordinator = ConcurrentQueryCoordinator(
            ...     query_func=dns_service.get_dns_info,
            ...     max_concurrent=5
            ... )
            >>> results = await coordinator.execute_batch([
            ...     "example.com",
            ...     "google.com",
            ...     "github.com"
            ... ])
            >>> for result in results:
            ...     print(f"{result.query}: {result.status}")
        """
        # 去重
        unique_queries = list(dict.fromkeys(queries))
        
        # 创建所有查询任务
        tasks = [
            self._execute_single_query(query)
            for query in unique_queries
        ]
        
        # 并发执行所有查询
        results = await asyncio.gather(*tasks, return_exceptions=False)
        
        return results
    
    async def execute_batch_with_progress(
        self,
        queries: List[str],
        progress_callback: Optional[Callable[[int, int], Awaitable[None]]] = None
    ) -> List[QueryResult[T]]:
        """批量执行查询（带进度回调）
        
        Args:
            queries: 查询参数列表
            progress_callback: 进度回调函数 (已完成数, 总数)
            
        Returns:
            QueryResult对象列表
        """
        unique_queries = list(dict.fromkeys(queries))
        total = len(unique_queries)
        completed = 0
        results = []
        
        async def execute_with_callback(query: str) -> QueryResult[T]:
            nonlocal completed
            result = await self._execute_single_query(query)
            completed += 1
            if progress_callback:
                await progress_callback(completed, total)
            return result
        
        tasks = [execute_with_callback(query) for query in unique_queries]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        
        return results


class QueryCoordinatorFactory:
    """查询协调器工厂（工厂模式）
    
    简化协调器的创建
    """
    
    @staticmethod
    def create_dns_coordinator(
        dns_service,
        max_concurrent: int = 10,
        timeout: float = 30.0
    ) -> ConcurrentQueryCoordinator:
        """创建DNS查询协调器"""
        return ConcurrentQueryCoordinator(
            query_func=dns_service.get_dns_info,
            max_concurrent=max_concurrent,
            timeout=timeout
        )
    
    @staticmethod
    def create_ip_coordinator(
        ip_service,
        max_concurrent: int = 20,
        timeout: float = 10.0
    ) -> ConcurrentQueryCoordinator:
        """创建IP查询协调器"""
        return ConcurrentQueryCoordinator(
            query_func=ip_service.get_ip_info,
            max_concurrent=max_concurrent,
            timeout=timeout
        )
    
    @staticmethod
    def create_web_search_coordinator(
        search_service,
        max_concurrent: int = 5,
        timeout: float = 60.0
    ) -> ConcurrentQueryCoordinator:
        """创建Web搜索协调器"""
        return ConcurrentQueryCoordinator(
            query_func=search_service.search,
            max_concurrent=max_concurrent,
            timeout=timeout
        )

