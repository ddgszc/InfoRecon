import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

from email import policy
from email.parser import BytesParser

async def main(html:str):
  # Default crawl run configuration

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="raw://"+html,
        )
        print(result.markdown)  # Print clean markdown content




def read_eml_body_html(eml_file_path: str) -> str:
    """读取EML文件并提取HTML body内容
    
    Args:
        eml_file_path: EML文件路径
        
    Returns:
        HTML body内容，如果没有HTML部分则返回纯文本内容
    """
    with open(eml_file_path, 'rb') as f:
        msg = BytesParser(policy=policy.default).parse(f)
    
    # 优先获取HTML内容
    html_body = None
    text_body = None
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == 'text/html':
                html_body = part.get_content()
            elif content_type == 'text/plain' and text_body is None:
                text_body = part.get_content()
    else:
        content_type = msg.get_content_type()
        if content_type == 'text/html':
            html_body = msg.get_content()
        elif content_type == 'text/plain':
            text_body = msg.get_content()
    
    # 返回HTML内容，如果没有则返回纯文本
    return html_body if html_body else (text_body or "")

def read_eml_body_text(eml_file_path: str) -> str:
    """读取EML文件并提取纯文本body内容
    
    Args:
        eml_file_path: EML文件路径
        
    Returns:
        纯文本body内容，如果没有则返回空字符串
    """
    with open(eml_file_path, 'rb') as f:
        msg = BytesParser(policy=policy.default).parse(f)
    
    text_body = None
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == 'text/plain':
                text_body = part.get_content()
                break
    else:
        content_type = msg.get_content_type()
        if content_type == 'text/plain':
            text_body = msg.get_content()
    
    return text_body or ""


# 使用示例
# html_content = read_eml_body_html("装饰工程.eml")
# print(html_content)
if __name__ == "__main__":
    html_content = read_eml_body_html("聘任书.eml")
    print(html_content)
    asyncio.run(main(html_content))
