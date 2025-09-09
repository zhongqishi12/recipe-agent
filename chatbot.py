import streamlit as st
import asyncio
from dotenv import load_dotenv

load_dotenv()
from nodes.graph import get_chat_app


async def run_recipe_graph_stream(query: str):
    """
    逐事件产出 (text, is_final)
    - is_final=False：过程提示（来自各中间节点的 messages）
    - is_final=True ：最终结果（来自 output_node 的 final_output）
    """
    inputs = {"user_raw_query": query}
    app = get_chat_app()

    async for event in app.astream(inputs, stream_mode="updates"):
        for _, values in event.items():
            # ✅ 最终：output_node 会包含 final_output
            if "final_output" in values and values["final_output"]:
                yield values["final_output"], True
                continue

            # ✅ 过程：只拿“最新一条”助手提示，避免重复堆叠
            if "messages" in values and values["messages"]:
                assistants = [m["content"] for m in values["messages"] if m.get("role") == "assistant"]
                if assistants:
                    yield assistants[-1], False  # 只发出最新一条过程提示


def chat_interface_stream(user_message):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def run_stream():
        async for text, is_final in run_recipe_graph_stream(user_message):
            yield text, is_final

    agen = run_stream()
    while True:
        try:
            result = loop.run_until_complete(agen.__anext__())
            yield result
        except StopAsyncIteration:
            break


def main():
    st.set_page_config(page_title="智能菜谱助手", page_icon="🍲")

    # ---- 会话态初始化 ----
    if "messages" not in st.session_state:
        st.session_state["messages"] = []  # [{'role': 'user'|'assistant', 'content': '...'}, ...]
    if "user_input" not in st.session_state:
        st.session_state["user_input"] = ""

    st.title("🍲 智能菜谱助手")
    st.caption("输入你的需求，Agent 会实时显示“正在搜索/解析/筛选/润色”等进度，并给出最终推荐。")

    st.divider()

    # ---- 历史消息渲染（用户 + 助手，保持顺序）----
    for msg in st.session_state["messages"]:
        role = "你" if msg["role"] == "user" else "助手"
        if msg["role"] == "user":
            st.markdown(f"**{role}：** {msg['content']}")
        else:
            # 助手消息支持 markdown，便于展示加粗/列表
            st.markdown(f"**{role}：**\n\n{msg['content']}")

    # 流式占位符（只用于“生成中的临时显示”，结束后历史会持久存入 session_state）
    placeholder = st.empty()

    # ---- 发送逻辑 ----
    def submit_message():
        user_message = st.session_state["user_input"].strip()
        if not user_message:
            return

        # 记录用户消息
        st.session_state["messages"].append({"role": "user", "content": user_message})
        st.session_state["user_input"] = ""

        # 逐步流式展示助手文本（覆盖）
        final_text = ""
        with st.spinner("正在生成中…"):
            for text, is_final in chat_interface_stream(user_message):
                if is_final:
                    # 最终结果：保存，清空占位
                    final_text = text or ""
                    placeholder.empty()
                else:
                    # 过程提示：仅覆盖显示，不写入历史
                    placeholder.markdown(f"**助手（进度）**：\n\n{text or ''}")

        # 生成结束：把最终文本固化到历史里
        if final_text:
            st.session_state["messages"].append({"role": "assistant", "content": final_text})

        # 触发一次重渲染以显示新历史
        st.rerun()

    # 输入区
    st.text_input("你：", key="user_input", on_change=submit_message, placeholder="例如：帮我来一份操作简单的三明治食谱～")




if __name__ == "__main__":
    main()
