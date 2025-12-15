"""批量查询API路由
展示系统的高并发处理能力
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List

from app.services.dns_service import DNSService
from app.services.ip_service import IPService
from app.services.web_search_service import WebSearchService
from app.services.concurrent_query_coordinator import (
    QueryCoordinatorFactory,
    QueryResult,
    QueryStatus
)
from app.schema.dns_schema import DNSInfo
from app.schema.ip_schema import IPInfo
from app.schema.web_search_schema import WebSearchInfo


router = APIRouter(prefix="/batch", tags=["批量查询"])

# 初始化服务
dns_service = DNSService()
ip_service = IPService()
web_search_service = WebSearchService()


class BatchDNSRequest(BaseModel):
    """批量DNS查询请求"""
    domains: List[str] = Field(..., description="域名列表", min_length=1, max_length=50)
    max_concurrent: int = Field(default=10, description="最大并发数", ge=1, le=20)
    timeout: float = Field(default=30.0, description="单个查询超时时间(秒)", ge=1, le=60)


class BatchIPRequest(BaseModel):
    """批量IP查询请求"""
    ips: List[str] = Field(..., description="IP地址列表", min_length=1, max_length=100)
    max_concurrent: int = Field(default=20, description="最大并发数", ge=1, le=50)
    timeout: float = Field(default=10.0, description="单个查询超时时间(秒)", ge=1, le=30)


class BatchSearchRequest(BaseModel):
    """批量搜索请求"""
    queries: List[str] = Field(..., description="搜索关键词列表", min_length=1, max_length=10)
    max_concurrent: int = Field(default=3, description="最大并发数", ge=1, le=5)
    timeout: float = Field(default=60.0, description="单个查询超时时间(秒)", ge=10, le=120)


class BatchDNSResponse(BaseModel):
    """批量DNS查询响应"""
    total: int = Field(description="总查询数")
    successful: int = Field(description="成功数")
    failed: int = Field(description="失败数")
    timeout: int = Field(description="超时数")
    results: List[QueryResult[DNSInfo]] = Field(description="查询结果列表")


class BatchIPResponse(BaseModel):
    """批量IP查询响应"""
    total: int = Field(description="总查询数")
    successful: int = Field(description="成功数")
    failed: int = Field(description="失败数")
    timeout: int = Field(description="超时数")
    results: List[QueryResult[IPInfo]] = Field(description="查询结果列表")


class BatchSearchResponse(BaseModel):
    """批量搜索响应"""
    total: int = Field(description="总查询数")
    successful: int = Field(description="成功数")
    failed: int = Field(description="失败数")
    timeout: int = Field(description="超时数")
    results: List[QueryResult[WebSearchInfo]] = Field(description="查询结果列表")


@router.post("/dns", response_model=BatchDNSResponse)
async def batch_dns_query(request: BatchDNSRequest):
    """批量DNS查询
    
    支持同时查询多个域名的DNS信息，自动进行并发控制和超时管理
    
    Args:
        request: 批量DNS查询请求
        
    Returns:
        批量查询结果
        
    Example:
        ```json
        {
            "domains": ["example.com", "google.com", "github.com"],
            "max_concurrent": 10,
            "timeout": 30.0
        }
        ```
    """
    try:
        # 创建DNS查询协调器
        coordinator = QueryCoordinatorFactory.create_dns_coordinator(
            dns_service,
            max_concurrent=request.max_concurrent,
            timeout=request.timeout
        )
        
        # 执行批量查询
        results = await coordinator.execute_batch(request.domains)
        
        # 统计结果
        successful = sum(1 for r in results if r.status == QueryStatus.COMPLETED)
        failed = sum(1 for r in results if r.status == QueryStatus.FAILED)
        timeout = sum(1 for r in results if r.status == QueryStatus.TIMEOUT)
        
        return BatchDNSResponse(
            total=len(results),
            successful=successful,
            failed=failed,
            timeout=timeout,
            results=results
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ip", response_model=BatchIPResponse)
async def batch_ip_query(request: BatchIPRequest):
    """批量IP查询
    
    支持同时查询多个IP的地理位置信息
    
    Args:
        request: 批量IP查询请求
        
    Returns:
        批量查询结果
    """
    try:
        coordinator = QueryCoordinatorFactory.create_ip_coordinator(
            ip_service,
            max_concurrent=request.max_concurrent,
            timeout=request.timeout
        )
        
        results = await coordinator.execute_batch(request.ips)
        
        successful = sum(1 for r in results if r.status == QueryStatus.COMPLETED)
        failed = sum(1 for r in results if r.status == QueryStatus.FAILED)
        timeout = sum(1 for r in results if r.status == QueryStatus.TIMEOUT)
        
        return BatchIPResponse(
            total=len(results),
            successful=successful,
            failed=failed,
            timeout=timeout,
            results=results
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=BatchSearchResponse)
async def batch_search_query(request: BatchSearchRequest):
    """批量Web搜索
    
    支持同时执行多个搜索查询
    
    Args:
        request: 批量搜索请求
        
    Returns:
        批量查询结果
    """
    try:
        coordinator = QueryCoordinatorFactory.create_web_search_coordinator(
            web_search_service,
            max_concurrent=request.max_concurrent,
            timeout=request.timeout
        )
        
        results = await coordinator.execute_batch(request.queries)
        
        successful = sum(1 for r in results if r.status == QueryStatus.COMPLETED)
        failed = sum(1 for r in results if r.status == QueryStatus.FAILED)
        timeout = sum(1 for r in results if r.status == QueryStatus.TIMEOUT)
        
        return BatchSearchResponse(
            total=len(results),
            successful=successful,
            failed=failed,
            timeout=timeout,
            results=results
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

