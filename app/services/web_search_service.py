import aiohttp
import re
from typing import List, Optional
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.content_filter_strategy import BM25ContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

from app.schema.web_search_schema import WebSearchInfo


class WebSearchService:
    """Web搜索服务
    
    提供基于百度搜索的网页搜索功能，支持URL重定向跟踪
    """
    
    def __init__(
        self,
        timeout: float = 7.0,
        max_redirect_depth: int = 3,
        headless: bool = True
    ):
        """初始化Web搜索服务
        
        Args:
            timeout: 请求超时时间(秒)
            max_redirect_depth: URL重定向最大跟踪深度
            headless: 是否使用无头浏览器模式
        """
        self.timeout = timeout
        self.max_redirect_depth = max_redirect_depth
        self.headless = headless
        self.default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def _trace_url_redirects(self, initial_url: str) -> List[str]:
        """跟踪URL重定向链
        
        跟踪HTTP重定向和JavaScript/meta标签重定向
        
        Args:
            initial_url: 初始URL
            
        Returns:
            重定向链URL列表
        """
        redirect_chain = []
        current_url = initial_url
        visited = set()

        async with aiohttp.ClientSession() as session:
            for _ in range(self.max_redirect_depth):
                if current_url in visited:
                    break
                visited.add(current_url)
                
                try:
                    async with session.get(
                        current_url,
                        allow_redirects=True,
                        headers=self.default_headers,
                        timeout=self.timeout
                    ) as response:
                        # 记录HTTP重定向链
                        history = (
                            [response.real_url]
                            if not response.history
                            else [r.real_url for r in response.history] + [response.real_url]
                        )
                        redirect_chain.extend([str(url) for url in history])
                        
                        # 检查JavaScript/meta重定向
                        html = await response.text()
                        js_redirect_url = self._extract_js_redirect(html)
                        
                        if js_redirect_url:
                            current_url = js_redirect_url
                            continue
                        else:
                            break

                except (aiohttp.ClientError, TimeoutError) as e:
                    print(f"URL跟踪错误: {e}")
                    if not redirect_chain:
                        return [initial_url]
                    break

        return redirect_chain if redirect_chain else [initial_url]

    def _extract_js_redirect(self, html: str) -> Optional[str]:
        """提取JavaScript/meta标签重定向URL
        
        Args:
            html: HTML内容
            
        Returns:
            重定向URL，如果没有则返回None
        """
        # 移除空白字符
        compact_html = re.sub(r'\s+', ' ', html.strip())
        
        # 只处理简单重定向页面（内容少于1500字符）
        if len(compact_html) > 1500:
            return None
        
        # JavaScript重定向模式
        js_patterns = [
            r'window\.location\.replace\(["\']([^"\']+)["\']\)',
            r'window\.location\.href\s*=\s*["\']([^"\']+)["\']',
            r'window\.location\s*=\s*["\']([^"\']+)["\']'
        ]
        
        # meta refresh重定向模式
        meta_pattern = r'<meta[^>]+http-equiv=["\']refresh["\'][^>]+url=([^"\'\s>]+)'
        
        for pattern in js_patterns + [meta_pattern]:
            match = re.search(pattern, compact_html, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None

    def _clean_baidu_search_result(self, raw_text: str) -> str:
        """清洗百度搜索结果
        
        执行以下步骤:
        1. 移除"百度为您找到以下结果"之前的内容
        2. 只保留前三个搜索结果
        3. 移除"大家还在搜"及之后的内容
        4. 对每个结果，只保留到第一个链接
        
        Args:
            raw_text: 原始搜索结果文本
            
        Returns:
            清洗后的文本
        """
        marker = "时间不限所有网页和文件站点内检索\n百度为您找到以下结果"
        marker_start_index = raw_text.find(marker)

        if marker_start_index == -1:
            return ""

        content = raw_text[marker_start_index + len(marker):].strip()

        matches = list(re.finditer(r'(?m)^### ', content))
        
        # 检查第一个 ### 之前的内容
        if matches:
            first_match_index = matches[0].start()
            content_before_first_match = content[:first_match_index]
            
            # 如果前面的内容不包含特定字符串，则从第一个 ### 开始
            if "没有找到该URL。您可以直接访问" not in content_before_first_match:
                content = content[first_match_index:]
                matches = list(re.finditer(r'(?m)^### ', content))

        content = re.sub(r'^###\s*\n', '### ', content, flags=re.MULTILINE)
        
        # 只保留前三个搜索结果
        if len(matches) > 3:
            cutoff_index = matches[3].start()
            content = content[:cutoff_index].strip()
            
        # 移除"大家还在搜"及之后的内容
        footer_marker = "大家还在搜"
        footer_index = content.find(footer_marker)
        
        if footer_index != -1:
            content = content[:footer_index].strip()
        
        # 对每个搜索结果，只保留到第一个链接
        sections = re.split(r'(^### .*$)', content, flags=re.MULTILINE)
        cleaned_sections = []
        
        for section in sections:
            if section.startswith('### '):
                cleaned_sections.append(section)
            elif section.strip():
                # 查找第一个链接
                match = re.search(r'\[([^\]]+)\]\(([^\)]+)\)', section)
                if match:
                    end_pos = match.end()
                    newline_pos = section.find('\n', end_pos)
                    if newline_pos != -1:
                        cleaned_sections.append(section[:newline_pos + 1])
                    else:
                        cleaned_sections.append(section[:end_pos])
                else:
                    cleaned_sections.append(section)
            else:
                cleaned_sections.append(section)
        
        content = ''.join(cleaned_sections).strip()
            
        return content

    def _extract_urls_from_content(self, text: str) -> List[str]:
        """从搜索结果中提取URL
        
        Args:
            text: 搜索结果文本
            
        Returns:
            URL列表
        """
        pattern = r"^###\s*\n?\[.*?\]\((.*?)\)"
        urls = re.findall(pattern, text, re.MULTILINE)
        return urls

    async def search(self, query: str) -> WebSearchInfo:
        """执行百度搜索
        
        Args:
            query: 搜索关键词
            
        Returns:
            WebSearchInfo对象，包含搜索结果
            
        Example:
            >>> service = WebSearchService()
            >>> result = await service.search("Python编程")
            >>> print(f"找到 {len(result.results)} 个结果")
        """
        try:
            # 配置浏览器和爬虫
            browser_conf = BrowserConfig(
                browser_mode="chromium",
                user_agent_mode="random",
                verbose=True,
                text_mode=True,
                headless=self.headless
            )
            
            bm25_filter = BM25ContentFilter(user_query=query)
            md_generator = DefaultMarkdownGenerator(
                content_filter=bm25_filter,
                options={"ignore_images": True}
            )
            crawler_config = CrawlerRunConfig(markdown_generator=md_generator)
            
            # 执行搜索
            async with AsyncWebCrawler(config=browser_conf) as crawler:
                results = await crawler.arun(
                    f"https://www.baidu.com/s?wd={query}",
                    config=crawler_config
                )
            
            # 清洗搜索结果
            cleaned_content = self._clean_baidu_search_result(results.markdown)

            # 提取URL
            extracted_urls = self._extract_urls_from_content(cleaned_content)

            # 跟踪重定向并替换URL
            final_content = cleaned_content
            for original_url in extracted_urls:
                redirect_chain = await self._trace_url_redirects(original_url)
                final_url = redirect_chain[-1]
                final_content = final_content.replace(original_url, final_url)
            
            # 构建返回结果
            return WebSearchInfo(
                query=query,
                search_result=final_content
            )
            
        except Exception as e:
            # 返回包含错误信息的结果
            return WebSearchInfo(
                query=query,
                error=str(e)
            )

