#!/usr/bin/env python3
"""MCP服务器启动脚本

默认使用HTTP流式传输模式，监听 0.0.0.0:33668

使用方法：
  python mcp_run.py                    # HTTP模式，默认 0.0.0.0:33668
  python mcp_run.py --port 9000        # HTTP模式，自定义端口
  python mcp_run.py --stdio            # STDIO模式（本地客户端）
"""

import argparse
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.mcp import mcp_server


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="InfoRecon MCP服务器 - 默认HTTP流式传输模式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                        # HTTP模式，监听 0.0.0.0:33668
  %(prog)s --port 9000            # HTTP模式，自定义端口 9000
  %(prog)s --host 127.0.0.1       # HTTP模式，只监听本地
  %(prog)s --stdio                # STDIO模式（用于本地客户端）
        """
    )
    
    parser.add_argument(
        "--stdio",
        action="store_true",
        help="使用STDIO传输模式（默认使用HTTP）"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="HTTP服务器监听地址（默认: 0.0.0.0）"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=33668,
        help="HTTP服务器端口（默认: 33668）"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="日志级别（默认: INFO）"
    )
    
    args = parser.parse_args()
    
    # 根据参数选择传输模式
    if args.stdio:
        print("🚀 启动InfoRecon MCP服务器 (STDIO模式)", file=sys.stderr)
        print("📝 日志级别: {}".format(args.log_level), file=sys.stderr)
        print("等待客户端连接...", file=sys.stderr)
        print(file=sys.stderr)
        
        mcp_server.run(
            transport="stdio",
            log_level=args.log_level
        )
    else:
        print(f"🚀 启动InfoRecon MCP服务器 (HTTP流式传输模式)")
        print(f"📍 监听地址: http://{args.host}:{args.port}")
        print(f"📝 日志级别: {args.log_level}")
        print(f"🔗 MCP端点: http://{args.host}:{args.port}/mcp/v1")
        print(f"📖 使用Ctrl+C停止服务器")
        print()
        
        mcp_server.run(
            transport="streamable-http",
            host=args.host,
            port=args.port,
            log_level=args.log_level
        )


if __name__ == "__main__":
    main()

