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

        # 获取所有食谱链接
        all_urls = await page.locator('.recipe a[href*="/recipe/"]').evaluate_all(
            'elements => elements.map(el => el.href)'
        )

        # Python中去重并取前5个
        unique_recipe_urls = list(dict.fromkeys(all_urls))[:5]

        for url in unique_recipe_urls:
            print(f"Scraping recipe from: {url}")

        # 关闭浏览器
        await browser.close()


asyncio.run(main())
