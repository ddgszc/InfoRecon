"""MCP工具定义

将现有服务封装为MCP工具，遵循高内聚低耦合原则
"""

from typing import List, Dict, Any
from fastmcp import FastMCP

from app.services.dns_service import DNSService
from app.services.ip_service import IPService
from app.services.web_search_service import WebSearchService
from app.services.get_site import URLAnalyzer
from app.schema.dns_schema import DNSInfo
from app.schema.ip_schema import IPInfo
from app.schema.web_search_schema import WebSearchInfo


# 初始化服务层（复用现有服务）
dns_service = DNSService()
ip_service = IPService()
web_search_service = WebSearchService()
url_analyzer = URLAnalyzer()


def register_tools(mcp: FastMCP) -> None:
    """注册所有MCP工具
    
    Args:
        mcp: FastMCP服务器实例
    """
    
    # @mcp.tool()
    # async def query_dns(domain: str) -> Dict[str, Any]:
    #     """查询域名的DNS信息
        
    #     获取指定域名的完整DNS记录，包括A记录、CNAME、MX、TXT、NS记录和WHOIS信息。
        
    #     Args:
    #         domain: 要查询的域名，如 "example.com"
            
    #     Returns:
    #         包含DNS记录和WHOIS信息的字典
            
    #     Example:
    #         query_dns("google.com")
    #     """
    #     dns_info: DNSInfo = await dns_service.get_dns_info(domain)
    #     return dns_info.model_dump(exclude_none=True)
    
    
    # @mcp.tool()
    # async def query_ip(ip: str) -> Dict[str, Any]:
    #     """查询IP地址的地理位置信息
        
    #     获取指定IP地址的国家/地区信息。
        
    #     Args:
    #         ip: 要查询的IP地址，如 "8.8.8.8"
            
    #     Returns:
    #         包含IP地理位置信息的字典
            
    #     Example:
    #         query_ip("8.8.8.8")
    #     """
    #     ip_info: IPInfo = await ip_service.get_ip_info(ip)
    #     return ip_info.model_dump(exclude_none=True)
    
    
    # @mcp.tool()
    # async def web_search(query: str) -> Dict[str, Any]:
    #     """执行Web搜索
        
    #     使用百度搜索引擎搜索指定关键词，返回前3条搜索结果。
    #     自动跟踪URL重定向，返回真实的目标URL。
        
    #     Args:
    #         query: 搜索关键词
            
    #     Returns:
    #         包含搜索结果的字典
            
    #     Example:
    #         web_search("Python编程教程")
    #     """
    #     search_info: WebSearchInfo = await web_search_service.search(query)
    #     return search_info.model_dump(exclude_none=True)
    
    
    @mcp.tool()
    async def analyze_url(url: str) -> Dict[str, Any]:
        """分析URL并获取网页内容
        
        访问指定URL，追踪重定向链，提取网页标题和内容摘要。
        支持JavaScript渲染的动态网页。
        
        Args:
            url: 要分析的URL，需包含协议（如 https://example.com）
            
        Returns:
            包含URL分析结果的字典，包括：
            - url_content: URL页面内容（Markdown格式）
            - redirect_chain: URL重定向链路列表
            
        Example:
            analyze_url("https://www.example.com")
        """
        result = await url_analyzer.analyze_url(url)
        return result
    

async def cleanup_services():
    """清理服务资源"""
    from app.services.async_whois_service import AsyncWhoisService
    from app.services.ip_service import GeoIPReader
    
    await AsyncWhoisService.shutdown()
    await GeoIPReader.shutdown()
    
    if url_analyzer:
        await url_analyzer.close()

