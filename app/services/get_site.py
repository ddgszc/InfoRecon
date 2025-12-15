import asyncio
import aiohttp
from typing import List, Dict
from urllib.parse import urlparse
import re
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai import CacheMode


class URLAnalyzer:
    def __init__(self):
        self.browser_conf = BrowserConfig(
            browser_mode="chromium",
            user_agent_mode="random",
            verbose=True,
            text_mode=True,
            headless=True)
        self.generator = DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(threshold=0.5, threshold_type="fixed"),
            content_source="cleaned_html",
            options={"ignore_images": True}
        )
        self.run_conf = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, markdown_generator=self.generator)
        self.crawler: AsyncWebCrawler = None

    @staticmethod
    def is_valid_url(url: str, check_tld: bool = True) -> bool:
        """
        校验输入是否为有效的URL链接
        
        Args:
            url (str): 要校验的URL字符串
            check_tld (bool): 是否检查顶级域名的有效性，默认为True
            
        Returns:
            bool: 如果是有效URL返回True，否则返回False
        """
        if not url or not isinstance(url, str):
            return False
        
        # 去除首尾空白字符
        url = url.strip()
        
        # 如果没有协议，添加默认协议进行校验
        test_url = url
        if not url.startswith(("http://", "https://")):
            test_url = f"https://{url}"
        
        try:
            result = urlparse(test_url)
            # 检查是否有scheme和netloc
            has_valid_scheme = result.scheme in ["http", "https"]
            has_netloc = bool(result.netloc)
            
            if not has_valid_scheme or not has_netloc:
                return False
            
            # 提取主机名（去除端口）
            hostname = result.netloc.split(':')[0]
            
            # 检查是否是IP地址
            ipv4_pattern = re.compile(
                r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
            )
            if ipv4_pattern.match(hostname):
                return True
            
            # 检查是否是localhost
            if hostname.lower() == 'localhost':
                return True
            
            # 检查域名格式
            # 域名必须至少有一个点，且符合域名命名规范
            if '.' not in hostname:
                return False
            
            # 域名格式校验：只允许字母、数字、连字符和点
            domain_char_pattern = re.compile(r'^[a-zA-Z0-9.-]+$')
            if not domain_char_pattern.match(hostname):
                return False
            
            # 分割域名各部分
            parts = hostname.split('.')
            
            # 每个部分都不能为空，不能以连字符开头或结尾
            for part in parts:
                if not part or part.startswith('-') or part.endswith('-'):
                    return False
                # 每个部分长度限制
                if len(part) > 63:
                    return False
            
            # 检查顶级域名（TLD）
            if check_tld:
                tld = parts[-1].lower()
                # 常见的顶级域名列表
                common_tlds = {
                    # 通用顶级域名
                    'com', 'org', 'net', 'edu', 'gov', 'mil', 'int',
                    'info', 'biz', 'name', 'pro', 'museum', 'coop', 'aero',
                    'cat', 'jobs', 'mobi', 'travel', 'tel', 'asia', 'xxx',
                    # 新通用顶级域名
                    'app', 'dev', 'web', 'site', 'online', 'store', 'tech',
                    'cloud', 'ai', 'io', 'co', 'me', 'tv', 'cc', 'ws',
                    # 国家/地区顶级域名（部分）
                    'cn', 'us', 'uk', 'jp', 'de', 'fr', 'au', 'ca', 'br',
                    'ru', 'in', 'kr', 'it', 'es', 'nl', 'pl', 'tw', 'hk',
                    'sg', 'th', 'my', 'id', 'ph', 'vn', 'nz', 'za', 'ar',
                    'mx', 'se', 'no', 'dk', 'fi', 'be', 'ch', 'at', 'cz',
                    'pt', 'gr', 'tr', 'il', 'ae', 'sa', 'eg', 'pk', 'bd',
                    'ng', 'ke', 'gh', 'tz', 'ug', 'zm', 'zw', 'ma', 'dz',
                }
                
                # TLD必须是2个字符以上的字母
                if len(tld) < 2 or not tld.isalpha():
                    return False
                
                # 检查是否在常见TLD列表中
                if tld not in common_tlds:
                    # 如果不在列表中，至少要求是2-6个字母（大多数TLD的长度范围）
                    if not (2 <= len(tld) <= 6 and tld.isalpha()):
                        return False
            
            return True
            
        except Exception:
            return False

    async def close(self):
        """在应用关闭时调用，关闭crawler，关闭浏览器。"""
        if self.crawler:
            print("Closing URLAnalyzer: Shutting down browser...")
            await self.crawler.__aexit__(None, None, None)
            self.crawler = None
            print("Browser shut down.")

    async def get_url_content(self, url: str) -> str:
        """
        获取URL页面内容
        
        Args:
            url (str): 要获取内容的URL
            
        Returns:
            str: URL页面的Markdown内容，如果失败返回错误信息
            
        Raises:
            ValueError: 如果URL格式无效
        """
        # 校验URL格式
        if not self.is_valid_url(url):
            raise ValueError(f"无效的URL格式: {url}")
        
        # 检查并补全URL协议
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"  # 默认使用https
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 404 or response.status >= 500:
                            # 如果https失败,尝试http
                            url = f"http://{url[8:]}"
            except Exception:
                # 如果https连接失败,尝试http
                url = f"http://{url[8:]}"


        try:
            # 复用 self.crawler 实例
            async with AsyncWebCrawler(config=self.browser_conf) as crawler:
                result = await crawler.arun(url=url, config=self.run_conf)
                cleaned_markdown = result.markdown.fit_markdown
            return cleaned_markdown
        except Exception as e:
            print(f"Error getting url content: {e}")
            return str(e)


    async def trace_url_redirects(self, initial_url: str) -> List[str]:
        """
        跟踪URL重定向链路
        
        Args:
            initial_url (str): 初始URL
            
        Returns:
            List[str]: 重定向链路列表
            
        Raises:
            ValueError: 如果URL格式无效
        """
        # 校验URL格式
        if not self.is_valid_url(initial_url):
            raise ValueError(f"无效的URL格式: {initial_url}")
        
        # 补全协议
        if not initial_url.startswith(("http://", "https://")):
            initial_url = f"https://{initial_url}"
        
        redirect_chain = []

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(initial_url, allow_redirects=True) as response:
                    history = (
                        [response.real_url]
                        if not response.history
                        else [r.real_url for r in response.history]
                        + [response.real_url]
                    )
                    redirect_chain = [str(url) for url in history]

            except aiohttp.ClientError as e:
                print(f"Error occurred while fetching URL: {e}")
                return [initial_url]

        return redirect_chain

    async def analyze_url(self, url: str) -> Dict:
        """
        分析URL并返回综合分析结果

        Args:
            url (str): 要分析的URL

        Returns:
            Dict: 包含URL分析结果的字典，包括：
                - url_content: URL页面内容
                - redirect_chain: URL重定向链路
                
        Raises:
            ValueError: 如果URL格式无效
        """
        # 校验URL格式
        if not self.is_valid_url(url):
            raise ValueError(f"无效的URL格式: {url}")
        
        content = await self.get_url_content(url)
        redirect_chain = await self.trace_url_redirects(url)

        return {"url_content": content, "redirect_chain": redirect_chain}


if __name__ == "__main__":
    import asyncio

    url = "http://hqnwz.cn/1/shouye.php?"
    analyzer = URLAnalyzer()
    asyncio.run(analyzer.initialize())
    result = asyncio.run(analyzer.analyze_url(url))
    asyncio.run(analyzer.close())
    print(result)
