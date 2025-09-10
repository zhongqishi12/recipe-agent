from tools.dashscope_web_search import DashScopeWebSearchTool

async def deepsearch_node(state):
    print("--- 节点: DeepSearch 联网搜索 ---")
    search_tool = DashScopeWebSearchTool(strategy="turbo", forced=True)
    query = " ".join(state.get("search_keywords", []))

    result = search_tool.search(query)

    if "error" in result:
        state.setdefault("messages", []).append(
            {"role": "assistant", "content": f"⚠️ 搜索失败: {result['error']}"}
        )
        return state

    # 保存搜索结果和回答
    state["search_results"] = result["results"]
    state["search_answer"] = result["answer"]

    print(result["results"])
    print(result["answer"])

    # 提示用户搜索正在进行
    state.setdefault("messages", []).append(
        {"role": "assistant", "content": f"🔎 已从网上找到一些相关内容，正在分析中…"}
    )

    return state
