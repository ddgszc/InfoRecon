from app.services.web_serch import get_baidu_search_results,trace_url_redirects
import asyncio
from crawl4ai import AsyncWebCrawler,BrowserConfig,CrawlerRunConfig
from crawl4ai.content_filter_strategy import BM25ContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

async def main():
    browser_conf=BrowserConfig(browser_mode="chromium",user_agent_mode="random")
    bm25_filter = BM25ContentFilter(
    user_query="ceshi.com"
    )
    md_generator=DefaultMarkdownGenerator(content_filter=bm25_filter,options={"ignore_images":True})
    crawler_config = CrawlerRunConfig(markdown_generator=md_generator)
    async with AsyncWebCrawler(config=browser_conf) as crawler:
        results = await crawler.arun("https://www.baidu.com/s?wd=hytch.com",config=crawler_config)
    with open("result.md","w",encoding="utf-8") as f:
        f.write(results.markdown)
async def ceshi():
    results = await get_baidu_search_results("alibaba.com")
    with open("result.md","w",encoding="utf-8") as f:
        f.write(results) 

if __name__ == "__main__":
    asyncio.run(ceshi())