from langchain_core.tools import tool
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
# 推荐使用 playwright 来处理动态加载的网站
from playwright.sync_api import sync_playwright


@tool
async def scrape_xiachufang_recipe(ingredient: str, max_recipes: int = 5):
    """
    根据食材关键词，使用 Playwright 异步爬取下厨房网站，返回前 max_recipes 个食谱详情内容。
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://www.xiachufang.com/")
        await page.fill('input[placeholder="搜索菜谱、食材"]', ingredient)
        await page.keyboard.press("Enter")
        await page.wait_for_load_state("networkidle")
        all_urls = await page.locator('.recipe a[href*="/recipe/"]').evaluate_all(
            'elements => elements.map(el => el.href)'
        )
        unique_recipe_urls = list(dict.fromkeys(all_urls))[:max_recipes]
        recipes_content = []
        for url in unique_recipe_urls:
            await page.goto(url)
            await page.wait_for_load_state("networkidle")
            print(f"正在爬取食谱: {url}")
            content = await page.locator('div.block.recipe-show').inner_html()
            print(content)
            recipes_content.append({'url': url, 'content': content})
        await browser.close()
    return recipes_content
