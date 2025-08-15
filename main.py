# app.py
from dotenv import load_dotenv

load_dotenv()

from langgraph.graph import StateGraph
from state import RecipeAppState, RecipeGraphState
from nodes.graph import scrape_node, generate_node, parse_recipes_node
import asyncio


async def main():
    workflow = StateGraph(RecipeGraphState)
    # 添加节点
    workflow.add_node("scraper", scrape_node)
    workflow.add_node("parser", parse_recipes_node)
    workflow.add_node("generator", generate_node)

    workflow.set_entry_point("scraper")
    # 添加边，定义流程
    workflow.add_edge("scraper", "parser")
    workflow.add_edge("parser", "generator")

    recipe_graph = workflow.compile()
    result = await recipe_graph.ainvoke({
        "ingredients": ["鸡肉", "蘑菇", "洋葱"],
        "requirements": "低脂肪，高蛋白，适合家庭晚餐",
        "max_recipes": 5
    })
    print(result)

if __name__ == "__main__":
    asyncio.run(main())