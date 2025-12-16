"""MCP服务器主入口

基于FastMCP框架构建的MCP服务端，提供信息侦察工具集
"""

from contextlib import asynccontextmanager
from fastmcp import FastMCP

from .tools import register_tools, cleanup_services


@asynccontextmanager
async def lifespan(mcp_app: FastMCP):
    """MCP应用生命周期管理
    
    启动时初始化服务，关闭时清理资源
    """
    # 启动时：初始化服务（服务在tools模块中已初始化）
    yield
    
    # 关闭时：清理资源
    await cleanup_services()


# 创建MCP服务器实例
mcp_server = FastMCP(
    name="InfoRecon",
    instructions="""
InfoRecon - 信息侦察工具集

这是一个专业的信息侦察MCP服务器，提供以下功能：

## 核心功能

### 1. DNS查询
- `query_dns`: 查询域名的完整DNS信息（A、CNAME、MX、TXT、NS记录及WHOIS）
- `query_dns_by_type`: 查询特定类型的DNS记录
- `batch_query_dns`: 批量查询多个域名的DNS信息

### 2. IP地理位置查询
- `query_ip`: 查询IP地址的国家/地区信息
- `batch_query_ip`: 批量查询多个IP的地理位置

### 3. Web搜索
- `web_search`: 使用百度搜索引擎搜索关键词，返回前3条结果

### 4. URL分析
- `analyze_url`: 访问URL并获取网页内容，支持重定向追踪和JavaScript渲染

## 使用建议
- 批量查询时建议控制并发数，避免过载
- Web搜索和URL分析可能需要较长时间，请耐心等待
- 所有工具都支持异步执行，性能优异

## 技术特点
- 完全异步架构，高并发支持
- 智能缓存机制，提升查询速度
- 自动重定向追踪，获取真实URL
- 支持JavaScript渲染的动态网页
    """,
    version="2.0.0",
    lifespan=lifespan
)

# 注册所有工具
register_tools(mcp_server)

