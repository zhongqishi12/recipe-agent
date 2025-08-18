# app.py
from dotenv import load_dotenv

load_dotenv()

from langgraph.graph import StateGraph
from state import RecipeAppState, RecipeGraphState
from nodes.graph import scrape_node, generate_final_recipe_node, parse_recipes_node, save_to_markdown_node, \
    parse_input_node
import asyncio


async def main():
    workflow = StateGraph(RecipeGraphState)
    # 添加节点
    workflow.add_node("input_parser", parse_input_node)
    workflow.add_node("scraper", scrape_node)
    workflow.add_node("parser", parse_recipes_node)
    workflow.add_node("generator", generate_final_recipe_node)
    workflow.add_node("save_md", save_to_markdown_node)  # 新增保存为Markdown的节点

    workflow.set_entry_point("input_parser")

    # 添加边，定义流程
    workflow.add_edge("input_parser", "scraper")  # 理解之后再去爬
    workflow.add_edge("scraper", "parser")
    workflow.add_edge("parser", "generator")
    workflow.add_edge("generator", "save_md")  # 新增边，连接到保存节点

    recipe_graph = workflow.compile()
    # 只需要传入最原始的自然语言请求
    inputs = {
        "user_raw_query": "我希望获取2个三明治早餐食谱，主要食材包括生菜和鸡蛋，做法要简单点"
    }
    result = await recipe_graph.ainvoke(inputs)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())