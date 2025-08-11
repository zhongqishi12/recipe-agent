# app.py
from dotenv import load_dotenv

load_dotenv()

from langgraph.graph import StateGraph
from state import RecipeAppState, RecipeGraphState
from nodes.graph import scrape_node, generate_node

graph = StateGraph(RecipeGraphState)
graph.add_node("scrape", scrape_node)
graph.add_node("generate", generate_node)
graph.set_entry_point("scrape")
graph.add_edge("scrape", "generate")

recipe_graph = graph.compile()
result = recipe_graph.invoke({
    "ingredients": ["鸡肉", "蘑菇", "洋葱"],
    "requirements": "低脂肪，高蛋白，适合家庭晚餐",
    "target_url": "https://example.com/recipe-page"  # 替换为实际的食谱页面URL
})
print(result)

