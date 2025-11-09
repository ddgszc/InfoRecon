import aiohttp
from typing import List
import re
from crawl4ai import AsyncWebCrawler,BrowserConfig,CrawlerRunConfig
from crawl4ai.content_filter_strategy import BM25ContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

async def trace_url_redirects(initial_url: str, max_depth: int = 3) -> List[str]:
    redirect_chain = []
    DEFAULT_HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    current_url = initial_url
    visited = set()

    async with aiohttp.ClientSession() as session:
        for _ in range(max_depth):
            if current_url in visited:
                break
            visited.add(current_url)
            
            try:
                async with session.get(current_url, allow_redirects=True, headers=DEFAULT_HEADERS,timeout=7) as response:
                    # 记录HTTP重定向链
                    history = (
                        [response.real_url]
                        if not response.history
                        else [r.real_url for r in response.history]
                        + [response.real_url]
                    )
                    redirect_chain.extend([str(url) for url in history])
                    
                    # 检查是否为JavaScript/meta重定向页面
                    html = await response.text()
                    js_redirect_url = _extract_js_redirect(html)
                    
                    if js_redirect_url:
                        current_url = js_redirect_url
                        continue
                    else:
                        break

            except (aiohttp.ClientError, TimeoutError) as e:
                print(f"Error occurred while fetching URL: {e}")
                if not redirect_chain:
                    return [initial_url]
                break

    return redirect_chain if redirect_chain else [initial_url]


def _extract_js_redirect(html: str) -> str:
    """提取仅用于重定向的JavaScript页面中的目标URL"""
    # 移除HTML中的空白字符以便分析
    compact_html = re.sub(r'\s+', ' ', html.strip())
    
    # 检查是否为简单重定向页面（内容少于1500字符且主要是脚本/meta标签）
    # 增加长度限制以支持带有长URL参数的重定向页面
    if len(compact_html) > 1500:
        return None
    
    # 提取window.location相关的重定向URL
    js_patterns = [
        r'window\.location\.replace\(["\']([^"\']+)["\']\)',
        r'window\.location\.href\s*=\s*["\']([^"\']+)["\']',
        r'window\.location\s*=\s*["\']([^"\']+)["\']'
    ]
    
    # 提取meta refresh重定向URL
    meta_pattern = r'<meta[^>]+http-equiv=["\']refresh["\'][^>]+url=([^"\'\s>]+)'
    
    for pattern in js_patterns + [meta_pattern]:
        match = re.search(pattern, compact_html, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None

def clean_baidu_search_result(raw_text):
    """
    清洗并提取百度搜索结果的核心内容。

    执行以下步骤:
    1. 移除"百度为您找到以下结果"之前的所有内容。
    2. 检查第一个 `###` 之前的内容是否包含"没有找到该URL。您可以直接访问"，
       如果包含则保留前面内容，否则只保留前三个 `###` 级别的结果。
    3. 移除末尾的"大家还在搜"及之后的所有内容。
    4. 对每个 ### 栏目，只保留内容到第一个有内容的中括号[]链接。

    参数:
    raw_text (str): 原始的、未经处理的网页文本。

    返回:
    str: 经过四步精细清洗后的文本。如果未找到有效内容，则返回空字符串。
    """

    marker = "时间不限所有网页和文件站点内检索\n百度为您找到以下结果"
    marker_start_index = raw_text.find(marker)

    if marker_start_index == -1:
        # 如果连头部标记都找不到，直接返回
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
            # 重新查找 ### 匹配项
            matches = list(re.finditer(r'(?m)^### ', content))

    content = re.sub(r'^###\s*\n', '### ', content, flags=re.MULTILINE)
    
    # 只保留前三个 ### 的内容
    if len(matches) > 3:
        cutoff_index = matches[3].start()
        content = content[:cutoff_index].strip()
        
    #移除 "大家还在搜" 及之后的内容
    footer_marker = "大家还在搜"
    footer_index = content.find(footer_marker)
    
    if footer_index != -1:
        content = content[:footer_index].strip()
    
    # 对每个 ### 栏目，只保留到第一个有内容的中括号[]
    # 将内容按 ### 分割
    sections = re.split(r'(^### .*$)', content, flags=re.MULTILINE)
    cleaned_sections = []
    
    for i, section in enumerate(sections):
        if section.startswith('### '):
            # 这是一个标题行
            cleaned_sections.append(section)
        elif section.strip():
            # 这是标题后的内容
            # 查找第一个包含内容的中括号 [xxx](yyy) 模式
            # 匹配从开始到第一个 [非空内容](链接) 的位置
            match = re.search(r'\[([^\]]+)\]\(([^\)]+)\)', section)
            if match:
                # 找到第一个有内容的链接，保留到这个链接结束的位置
                end_pos = match.end()
                # 找到这个链接后的第一个换行符
                newline_pos = section.find('\n', end_pos)
                if newline_pos != -1:
                    cleaned_sections.append(section[:newline_pos + 1])
                else:
                    cleaned_sections.append(section[:end_pos])
            else:
                # 如果没有找到链接，保留原内容
                cleaned_sections.append(section)
        else:
            # 空白部分
            cleaned_sections.append(section)
    
    content = ''.join(cleaned_sections).strip()
        
    return content

def extract_specific_urls(text: str) -> list:
    """
    使用正则表达式从文本中提取待指向网站的URL。
    
    Args:
        text: 待搜索的源文本字符串。
        
    Returns:
        一个包含所有匹配到的URL字符串的列表。
    """
    pattern = r"^###\s*\n?\[.*?\]\((.*?)\)"
    
    # re.MULTILINE (或 re.M) 标志让 ^ 能够匹配每一行的开头，而不仅仅是整个字符串的开头
    urls = re.findall(pattern, text, re.MULTILINE)
    
    return urls

async def get_baidu_search_results(query: str) -> str:
    # 1. 通过crawl4ai获取网页内容
    browser_conf=BrowserConfig(browser_mode="chromium",user_agent_mode="random",verbose=True,text_mode=True,headless=True)
    bm25_filter = BM25ContentFilter(
    user_query=query
    )
    md_generator=DefaultMarkdownGenerator(content_filter=bm25_filter,options={"ignore_images":True})
    crawler_config = CrawlerRunConfig(markdown_generator=md_generator)
    async with AsyncWebCrawler(config=browser_conf) as crawler:
        results = await crawler.arun(f"https://www.baidu.com/s?wd={query}",config=crawler_config)
    
    # 2. 经过清洗得到内容
    cleaned_content = clean_baidu_search_result(results.markdown)

    # 3. 提取匹配的链接
    extracted_urls = extract_specific_urls(cleaned_content)

    # 4. 跟踪每个URL的重定向并替换
    final_content = cleaned_content
    for original_url in extracted_urls:
        redirect_chain = await trace_url_redirects(original_url)
        final_url = redirect_chain[-1]  # 获取最后一个URL
        print(f"original_url: {original_url}, final_url: {final_url}")
        
        # 替换内容中的原始URL为最终URL
        final_content = final_content.replace(original_url, final_url)
    
    return final_content