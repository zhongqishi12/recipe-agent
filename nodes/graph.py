# graph.py
import os
from typing import TypedDict, List
from langchain_core.prompts import ChatPromptTemplate
from state import RecipeGraphState, RecipeAppState
from langchain_openai import ChatOpenAI  # 使用 LangChain 的 ChatOpenAI
from tools.tools import scrape_xiachufang_recipe

# 2. 初始化模型和工具
llm = ChatOpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen-plus"
)
# tools = [scrape_xiachufang_recipe]


# 3. 定义图的节点
def scrape_node(state: RecipeGraphState):
    """爬取目标网站内容的节点"""
    print("--- 节点: 爬取内容 ---")
    url = state['target_url']
    scraped_content = scrape_xiachufang_recipe.invoke(url)
    state['scraped_content'] = scraped_content
    return state


def generate_node(state: RecipeGraphState):
    """根据爬取的内容生成食谱的节点"""
    print("--- 节点: 生成食谱 ---")

    prompt_template = ChatPromptTemplate.from_template(
        """你是一位富有创意的厨师。请根据以下我从网上找到的参考资料，为我创作一份全新的食谱。

        我的要求是:
        - 主要食材: {ingredients}
        - 其他要求: {requirements}

        网上参考资料:
        ---
        {context}
        ---

        请为我提供一份包含以下部分的完整食谱:
        1. 一个吸引人的菜名。
        2. 详细的用料清单（可适当增加常见辅料）。
        3. 清晰的分步烹饪指南。
        """
    )

    chain = prompt_template | llm

    result = chain.invoke({
        "ingredients": ", ".join(state['ingredients']),
        "requirements": state['requirements'],
        "context": state['scraped_content']
    })

    state['final_recipe'] = result.content
    return state


def generate_query_node(state: RecipeAppState):
    print("节点: generate_query")
    # ... 根据食材和需求生成搜索关键词 ...
    state[
        'search_query'] = f"{' '.join(state['ingredients'])} {state['requirements']} recipe site:xiachufang.com OR site:tasty.co"
    state['retry_count'] = 0
    return state



def generate_recipe_node(state: RecipeAppState):
    print("节点: generate_recipe")
    # ... 构建Prompt，调用LLM生成食谱 ...
    prompt = f"根据以下爬取的食谱内容: {state['scraped_content']}, 为食材 {state['ingredients']} 创作一个新食谱。"
    # response = llm.invoke(prompt)
    # state['final_recipe'] = response.content
    state['final_recipe'] = "一份根据爬取内容生成的美味食谱..."
    return state


def handle_error_node(state: RecipeAppState):
    print("节点: handle_error")
    state['error_message'] = "多次尝试后无法获取有效食谱内容。"
    return state
