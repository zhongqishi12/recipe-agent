from bs4 import BeautifulSoup
from typing import List, Dict

from playwright.async_api import async_playwright


class DouguoRecipeScraper:
    def __init__(self):
        self.base_url = "https://www.douguo.com"
        self.recipes_data = []
        # 定义状态文件的路径
        self.AUTH_STATE_PATH = "douguo_auth_state.json"

    @staticmethod
    def extract_ingredients(html_content: str) -> List[Dict[str, str]]:
        """
        从给定的菜谱HTML内容中，解析并提取所有食材及其用量。

        :param html_content: 包含食材表格的HTML字符串。
        :return: 一个字典列表，每个字典包含'name'和'quantity'。
                 例如: [{'name': '非即食全麦贝果', 'quantity': '2个'}, ...]
        """
        # 初始化BeautifulSoup
        soup = BeautifulSoup(html_content, 'lxml')

        # 初始化一个空列表来存放结果
        ingredients_list = []

        # 1. 首先定位到包含所有食材的大容器，也就是那个<table>
        #    它的 class 是 "retamr"
        ingredients_table = soup.select_one('table.retamr')

        # 2. 健壮性检查：如果没找到这个表格，就返回空列表
        if not ingredients_table:
            return ingredients_list

        # 3. 在表格内，找到所有的单元格<td>。因为每个食材都在一个<td>里。
        table_cells = ingredients_table.select('td')

        # 4. 遍历每一个单元格
        for cell in table_cells:
            # 5. 在每个单元格中，分别寻找食材名和用量的<span>标签
            name_span = cell.select_one('span.scname')
            quantity_span = cell.select_one('span.scnum')

            # 6. 关键步骤：只有当一个单元格同时包含食材名和用量时，我们才认为它是一个有效的食材条目
            if name_span and quantity_span:
                # 使用 .get_text(strip=True) 来获取纯文本，
                # strip=True可以去掉前后的多余空格。
                # 这个方法很棒，因为它能自动处理<span>里是否嵌套<a>标签的情况。
                name = name_span.get_text(strip=True)
                quantity = quantity_span.get_text(strip=True)
                print(f"<UNK>: {name}, {quantity}")

                # 7. 将提取到的信息存为一个字典，并添加到结果列表中
                ingredients_list.append({'name': name, 'quantity': quantity})

        return ingredients_list

    @staticmethod
    def extract_steps(html_content: str) -> List[str]:
        """
        从给定的菜谱HTML内容中，解析并提取所有的烹饪步骤。

        :param html_content: 包含烹饪步骤的HTML字符串。
        :return: 一个字符串列表，每个字符串是一个烹饪步骤。
        """
        # 初始化BeautifulSoup
        soup = BeautifulSoup(html_content, 'lxml')

        # 初始化一个空列表来存放结果
        steps_list = []

        # 1. 定位到包含所有步骤的大容器 <div class="step">
        # 2. 在容器中找到所有独立的步骤容器 <div class="stepcont clearfix">
        step_containers = soup.select('div.stepcont.clearfix')

        # 3. 遍历每一个步骤容器
        for container in step_containers:
            # 4. 在每个容器中，找到包含文本信息的 <div class="stepinfo">
            info_div = container.select_one('div.stepinfo')

            if info_div:
                # 5. 关键技巧：在提取文本之前，先找到并移除“步骤X”所在的<p>标签
                step_number_tag = info_div.find('p')
                if step_number_tag:
                    step_number_tag.decompose()  # decompose()会彻底移除标签及其内容

                # 6. 现在info_div里只剩下纯粹的步骤描述文本了，我们再来提取它
                step_text = info_div.get_text(strip=True)
                print(f"提取到的步骤文本: {step_text}")

                # 7. 确保提取到的文本不为空，然后添加到结果列表中
                if step_text:
                    steps_list.append(step_text)

        return steps_list

    def extract_recipe_urls(self, html_content: str, count: int) -> List[str]:
        """
        从给定的HTML内容中解析并提取指定数量的菜谱URL。

        :param html_content: 包含食谱列表的HTML字符串。
        :param count: 希望提取的URL数量。
        :return: 包含绝对URL的列表。
        """
        # 初始化BeautifulSoup，使用lxml解析器
        soup = BeautifulSoup(html_content, 'lxml')

        # 初始化一个空列表来存放找到的URL，以便后续去重和计数
        found_urls = []

        # 1. 定位到包含所有食谱的列表容器 <ul class="cook-list">
        # 2. 在容器中找到所有的食谱条目 <li>
        #    通过观察，每个食谱条目都是一个 <li class="clearfix">
        recipe_list_items = soup.select('ul.cook-list li.clearfix')

        # 3. 遍历每一个食谱条目
        for item in recipe_list_items:
            # 4. 在每个条目中，找到代表菜谱名称和链接的<a>标签
            #    最精确的定位是 class="cookname" 的<a>标签
            link_tag = item.select_one('a.cookname')

            # 5. 确保找到了链接标签并且它有'href'属性
            if link_tag and link_tag.get('href'):
                relative_url = link_tag.get('href')

                # 6. 拼接成完整的绝对URL
                absolute_url = self.base_url + relative_url

                # 7. 去重后添加到列表中
                if absolute_url not in found_urls:
                    found_urls.append(absolute_url)

        # 8. 根据用户指定的数量，返回列表的切片
        return found_urls[:count]

    async def scrape_douguo(self, search_keywords: List[str], search_limit: int = 2):
        """
        根据食材关键词，使用 Playwright 异步爬取豆果美食网站，返回前 search_limit 个食谱详情内容。
        """
        search_query = " ".join(search_keywords)
        print(f"--- 工具: 收到关键词 '{search_keywords}', 拼接为 '{search_query}' 进行搜索 ---")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            # !!! 核心改动: 从文件加载身份状态来创建浏览器上下文 !!!
            context = await browser.new_context(storage_state=self.AUTH_STATE_PATH)
            page = await context.new_page()
            await page.goto(self.base_url)
            await page.wait_for_timeout(3000)  # 强制等待3秒

            # 查找搜索框并输入关键词
            search_input = "#global_search_inpt"
            await page.fill(search_input, search_query)
            print(f"已输入搜索关键词: {search_query}")
            await page.wait_for_timeout(3000)  # 强制等待3秒

            # 点击搜索按钮
            search_button = "input[type='submit'].lib"
            await page.click(search_button)
            # await page.wait_for_load_state('networkidle')
            print("搜索已提交，等待结果加载...")
            await page.wait_for_timeout(5000)

            # 获取搜索结果页面的HTML内容
            html_content = await page.content()
            # 通过 extract_recipe_urls 获取所有食谱URL
            recipe_urls = self.extract_recipe_urls(html_content, search_limit)

            recipes_content = []
            for url in recipe_urls:
                await page.goto(url)
                print(f"正在爬取食谱: {url}")
                await page.wait_for_timeout(2000)
                # 获取标题和内容
                title = await page.locator('h1.title').inner_text()
                print(f"食谱标题: {title}")

                html_content = await page.content()
                ingredients = self.extract_ingredients(html_content)
                print(f"<UNK>: {len(ingredients)}")

                steps = self.extract_steps(html_content)

                recipes_content.append({
                    'url': url,
                    'title': title,
                    'ingredients': ingredients,
                    'steps': steps
                })
            await browser.close()
        return recipes_content
