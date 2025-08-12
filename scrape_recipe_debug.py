import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        # 打开下厨房首页
        await page.goto("https://www.xiachufang.com/")
        # 输入“鸡胸肉”并回车
        await page.fill('input[placeholder="搜索菜谱、食材"]', "鸡胸肉")
        await page.keyboard.press("Enter")
        await page.wait_for_load_state("networkidle")
        # 点击第一个“这应该是我吃过最好吃的鸡胸肉”链接
        await page.click('a:has-text("这应该是我吃过最好吃的鸡胸肉")')
        await page.wait_for_load_state("networkidle")
        # 可选：保存页面内容或截图
        await page.screenshot(path="chicken_recipe.png")
        # 关闭浏览器
        await browser.close()

asyncio.run(main())