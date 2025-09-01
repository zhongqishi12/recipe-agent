# chatbot.py
import asyncio
from typing import Dict, Any
from dotenv import load_dotenv
# 仅在主程序入口加载环境变量
load_dotenv()
from nodes.graph import get_chat_app



async def run_recipe_graph(query: str) -> Dict[str, Any]:
    """
    异步运行你的菜谱Agent，并处理流式输出，向用户展示思考过程。
    """
    # 准备输入
    inputs = {"user_raw_query": query}
    app = get_chat_app()

    # 使用 astream_events API (v0.2.0+) 来获取详细的事件流
    # 这能让我们知道哪个节点正在运行
    async for event in app.astream_events(inputs, version="v1"):
        kind = event["event"]

        if kind == "on_chain_start":
            # 一个新的节点（或链）开始运行时
            print(f"--- 🧠 Agent开始思考: 正在进入 '{event['name']}' 节点 ---")

        elif kind == "on_chain_end":
            # 一个节点（或链）结束运行时
            # 我们可以选择在这里打印该节点的输出，用于调试
            # print(event['data']['output'])
            print(f"--- ✅ '{event['name']}' 节点执行完毕 ---")

    # 流结束后，再次调用ainvoke可以方便地获取最终的、完整的状态
    final_state = await app.ainvoke(inputs)
    return final_state


async def main_chat_loop():
    """
    聊天机器人的主循环。
    """
    print("你好！我是你的智能食谱助手。")
    print("输入你的需求开始，或者输入 '退出' 来结束对话。")
    print("-" * 50)

    while True:
        try:
            user_input = input("🧑 你说: ")
        except (KeyboardInterrupt, EOFError):
            break

        if user_input.lower() in ["退出", "exit", "quit", "bye"]:
            print("🤖 好的，下次再见！")
            break

        if not user_input.strip():
            continue

        print("🤖 AI助手: 好的，我正在为你规划，请稍候...")
        final_result = await run_recipe_graph(user_input)

        print("\n" + "=" * 20 + " 最终结果 " + "=" * 20)
        # 假设最终结果在'final_output'或'final_recipe'字段，请根据你的State定义调整
        output_key = "final_output"  # 或者 'final_recipe'
        if final_result.get(output_key):
            print(final_result[output_key])
        else:
            print("抱歉，我没能生成食谱计划，可能在处理过程中遇到了问题。")
        print("=" * 52 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main_chat_loop())
    except Exception as e:
        print(f"程序出现未预料的错误: {e}")