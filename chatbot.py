# chatbot_gradio.py
import asyncio
from typing import Dict, Any
from dotenv import load_dotenv
import gradio as gr

# 加载环境变量
load_dotenv()
from nodes.graph import get_chat_app


async def run_recipe_graph_stream(query: str):
    inputs = {"user_raw_query": query}
    app = get_chat_app()
    async for state in app.astream(inputs):
        yield state.get("messages", [])


def chat_interface_stream(user_message, history):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def run_stream():
            async for messages in run_recipe_graph_stream(user_message):
                assistant_msgs = [m["content"] for m in messages if m.get("role") == "assistant"]
                if assistant_msgs:
                    # 把多条助手消息合并
                    yield "\n\n".join(assistant_msgs)

        # 用 iterator 驱动 async generator，而不是 asyncio.run
        agen = run_stream()
        while True:
            try:
                result = loop.run_until_complete(agen.__anext__())
                yield result
            except StopAsyncIteration:
                break

    except Exception as e:
        yield f"程序出现错误: {e}"


async def async_generator_to_list(async_gen):
    """将异步生成器转换为列表"""
    results = []
    async for item in async_gen:
        results.append(item)
    return results


def chat_interface(user_message, history):
    """
    非流式版本（备用）
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def get_final_result():
            final_messages = None
            async for messages in run_recipe_graph_stream(user_message):
                final_messages = messages
            return final_messages

        final_messages = loop.run_until_complete(get_final_result())

        if final_messages:
            # 提取所有助手消息
            assistant_messages = [
                msg["content"] for msg in final_messages
                if msg.get("role") == "assistant"
            ]
            return "\n\n".join(assistant_messages)
        else:
            return "抱歉，我没能生成食谱计划，可能在处理过程中遇到了问题。"

    except Exception as e:
        return f"程序出现错误: {e}"


if __name__ == "__main__":
    with gr.Blocks() as demo:
        gr.Markdown("## 🥪 智能食谱助手\n输入你的需求，AI 会帮你规划菜单！")
        chatbot = gr.Chatbot(height=500, type="messages")
        msg = gr.Textbox(placeholder="请输入你的食谱需求...")
        clear = gr.Button("清空对话")


        def respond_stream(user_message, chat_history):
            """流式响应函数"""
            # 添加用户消息
            chat_history.append({"role": "user", "content": user_message})

            # 添加空的助手消息，用于更新
            chat_history.append({"role": "assistant", "content": ""})

            # 流式更新助手消息
            for progress_text in chat_interface_stream(user_message, chat_history):
                chat_history[-1]["content"] = progress_text
                yield "", chat_history


        def respond_simple(user_message, chat_history):
            """简单响应函数"""
            reply = chat_interface(user_message, chat_history)
            chat_history.append({"role": "user", "content": user_message})
            chat_history.append({"role": "assistant", "content": reply})
            return "", chat_history


        # 使用流式版本
        msg.submit(respond_stream, [msg, chatbot], [msg, chatbot])
        clear.click(lambda: [], None, chatbot, queue=False)

    demo.launch(server_name="0.0.0.0", server_port=7860)