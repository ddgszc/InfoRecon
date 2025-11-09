import asyncio
from playwright.async_api import async_playwright


async def visit_baidu():
    """使用 Playwright 访问百度搜索"""
    async with async_playwright() as p:
        # 启动浏览器，添加反爬虫参数
        browser = await p.chromium.launch(
            headless=False,  # 非无头模式
            args=[
                '--disable-blink-features=AutomationControlled',  # 禁用自动化控制特征
                '--no-sandbox',
                '--disable-dev-shm-usage',
            ]
        )
        
        # 创建浏览器上下文，设置真实的 User-Agent 和其他参数
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
            # 添加常见的浏览器权限
            permissions=['geolocation'],
        )
        
        # 创建新页面
        page = await context.new_page()
        
        # 隐藏 webdriver 特征
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // 添加 Chrome 对象
            window.chrome = {
                runtime: {}
            };
            
            // 修改 permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
        # 先访问百度首页，建立 cookies
        print("正在访问百度首页...")
        await page.goto("https://www.baidu.com", wait_until="networkidle")
        await asyncio.sleep(2)  # 等待一下，模拟真实用户行为
        
        # 然后访问搜索页面
        search_url = "https://www.baidu.com/s?wd=site:hytch.com"
        print(f"正在访问搜索页面: {search_url}")
        await page.goto(search_url, wait_until="networkidle")
        
        # 等待页面加载完成
        await asyncio.sleep(2)
        
        # 获取页面标题
        title = await page.title()
        print(f"页面标题: {title}")
        
        # 获取当前 URL
        current_url = page.url
        print(f"当前 URL: {current_url}")
        
        # 检查是否有验证码
        captcha_element = await page.query_selector('.vcode-spin')
        if captcha_element or '验证' in title:
            print("⚠️  检测到验证码页面，请手动完成验证...")
            print("验证完成后，浏览器将继续保持打开状态")
        
        # 等待一段时间以便观察或手动处理验证码
        print("浏览器将保持打开状态 60 秒，按 Ctrl+C 可以关闭...")
        await asyncio.sleep(60)
        
        # 关闭浏览器
        await browser.close()
        print("浏览器已关闭")


if __name__ == "__main__":
    asyncio.run(visit_baidu())

