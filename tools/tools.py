from typing import List

from langchain_core.tools import tool
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
# 推荐使用 playwright 来处理动态加载的网站
from playwright.sync_api import sync_playwright


@tool
async def scrape_xiachufang_recipe(search_keywords: List[str], search_limit: int = 2):
    """
    根据食材关键词，使用 Playwright 异步爬取下厨房网站，返回前 search_limit 个食谱详情内容。
    """

    # 1. 将关键词列表用空格连接成一个字符串
    search_query = " ".join(search_keywords)
    print(f"--- 工具: 收到关键词 '{search_keywords}', 拼接为 '{search_query}' 进行搜索 ---")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://www.xiachufang.com/")
        await page.fill('input[placeholder="搜索菜谱、食材"]', search_query)
        await page.keyboard.press("Enter")
        await page.wait_for_load_state("networkidle")
        # 扩大搜索范围，获取前 search_limit 个链接
        all_urls = await page.locator(f'.recipe a[href*="/recipe/"]').evaluate_all(
            f'elements => elements.slice(0, {search_limit}).map(el => el.href)'
        )
        unique_recipe_urls = list(dict.fromkeys(all_urls))[:search_limit]
        recipes_content = []
        for url in unique_recipe_urls:
            await page.goto(url)
            await page.wait_for_load_state("networkidle")
            print(f"正在爬取食谱: {url}")
            title = await page.locator('h1.page-title').inner_text()
            content = await page.locator('div.block.recipe-show').inner_html()
            print(content)
            recipes_content.append({
                'url': url,
                'content': content,
                'title': title
            })
        await browser.close()
    return recipes_content


