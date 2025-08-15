# graph.py
import os
from typing import TypedDict, List
from langchain_core.prompts import ChatPromptTemplate
from state import RecipeGraphState, RecipeAppState, ParsedRecipe
from tools.tools import scrape_xiachufang_recipe
from utils.llm_provider import llm
from langchain_core.output_parsers import JsonOutputParser


# 3. 定义图的节点
async def scrape_node(state: RecipeGraphState):
    print("--- 节点: 爬取内容 ---")
    ingredient_list = state['ingredients']
    ingredient_str = ' '.join(ingredient_list)
    print(f"爬取食材: {ingredient_str}")
    scraped_content = await scrape_xiachufang_recipe.ainvoke({
        "ingredient": ingredient_str,
        "max_recipes": 1
    })
    state['scraped_contents'] = scraped_content
    return state

def parse_recipes_node(state: RecipeGraphState):
    """解析爬取的食谱内容"""
    print("--- 节点: 解析食谱 ---")
    scraped_contents = state['scraped_contents']
    print(f"解析 {len(scraped_contents)} 个爬取的食谱内容...")
    print(scraped_contents)
    parsed_recipes = []

    parser = JsonOutputParser(pydantic_object=ParsedRecipe)
    prompt = ChatPromptTemplate.from_template(
        """你是一个精通网页解析的AI助手。你的任务是从给定的HTML片段中提取菜谱信息。

        根据以下HTML内容，提取菜谱的标题、所有用料（包括名称和用量）以及详细的烹饪步骤。

        {format_instructions}

        HTML内容如下:
        ```html
        {html_content}
        ```
        """
    )

    # 将Prompt、LLM和输出解析器连接起来
    chain = prompt | llm | parser

    for content in scraped_contents:
        try:
            # 调用我们创建好的解析链
            parsed_recipe = chain.invoke({
                "html_content": content['content'],
                "format_instructions": parser.get_format_instructions()
            })
            parsed_recipes.append(parsed_recipe)
        except Exception as e:
            print(f"  !! 解析失败: {content['url']}, 错误: {e}")
            # 即使某个页面解析失败，也继续处理下一个
            continue

    state['parsed_recipes'] = parsed_recipes
    return state


def generate_final_recipe_node(state: RecipeGraphState):
    """
    (新功能) 将解析后的结构化食谱数据，直接格式化为面向用户的Markdown文本。
    """
    print("--- 节点: 正在整理并格式化最终结果 ---")

    # 1. 检查是否有可用的解析后食谱
    if not state['parsed_recipes']:
        print(" !! 没有可用的解析后食谱，无法生成。")
        state['final_recipe'] = "抱歉，未能从目标网页解析出有效的食谱信息。"
        return state

    # 2. 准备一个列表，用来存放每个食谱的Markdown格式字符串
    final_recipes_md = []

    # 3. 遍历所有解析成功的食谱，并为每一个生成Markdown文本
    for i, recipe_data in enumerate(state['parsed_recipes']):
        # recipe_data 的结构是: {'title': '...', 'ingredients': [...], 'steps': [...]}

        # 使用f-string构建Markdown字符串
        md_parts = []

        # 添加标题
        md_parts.append(f"### {i + 1}. {recipe_data.get('title', '无标题食谱')}")
        md_parts.append("")  # 空行

        # 添加用料清单
        md_parts.append("**- 用料清单 -**")
        ingredients = recipe_data.get('ingredients', [])
        if ingredients:
            for ing in ingredients:
                md_parts.append(f"* {ing.get('name', '')}: {ing.get('quantity', '')}")
        else:
            md_parts.append("* 未能解析出用料信息。")
        md_parts.append("")  # 空行

        # 添加烹饪步骤
        md_parts.append("**- 烹饪步骤 -**")
        steps = recipe_data.get('steps', [])
        if steps:
            for idx, step in enumerate(steps):
                md_parts.append(f"{idx + 1}. {step}")
        else:
            md_parts.append("1. 未能解析出步骤信息。")

        # 将当前食谱的所有Markdown部分合并成一个字符串
        final_recipes_md.append("\n".join(md_parts))

    # 4. 如果有多个食谱，用分隔线将它们隔开
    final_output = "\n\n---\n\n".join(final_recipes_md)

    state['final_recipe'] = final_output
    print("--- 节点: 最终结果已格式化完成！ ---")
    return state


def generate_query_node(state: RecipeAppState):
    print("节点: generate_query")
    # ... 根据食材和需求生成搜索关键词 ...
    state[
        'search_query'] = f"{' '.join(state['ingredients'])} {state['requirements']} recipe site:xiachufang.com OR site:tasty.co"
    state['retry_count'] = 0
    return state




def handle_error_node(state: RecipeAppState):
    print("节点: handle_error")
    state['error_message'] = "多次尝试后无法获取有效食谱内容。"
    return state
