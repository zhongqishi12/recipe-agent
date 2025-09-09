import streamlit as st
import asyncio
from dotenv import load_dotenv

load_dotenv()
from nodes.graph import get_chat_app


async def run_recipe_graph_stream(query: str):
    inputs = {"user_raw_query": query}
    app = get_chat_app()

    # 获取每个节点的Message输出
    async for event in app.astream(inputs, stream_mode="updates"):
        for node, values in event.items():
            if "messages" in values:
                yield values["messages"]


def chat_interface_stream(user_message):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def run_stream():
        async for messages in run_recipe_graph_stream(user_message):
            assistant_msgs = [m["content"] for m in messages if m.get("role") == "assistant"]
            if assistant_msgs:
                yield "\n\n".join(assistant_msgs)

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

    # 顶部功能区
    cols = st.columns([1, 1, 6])
    with cols[0]:
        if st.button("🧹 清空对话"):
            st.session_state["messages"] = []
            st.rerun()
    with cols[1]:
        st.write("")  # 占位

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
            for response in chat_interface_stream(user_message):
                final_text = response or ""
                # 覆盖显示（方案A），不会越叠越长
                placeholder.markdown(f"**助手（生成中）**：\n\n{final_text}")

        # 生成结束：把最终文本固化到历史里
        # 注意：graph.py 的 output_node 已经把 state["final_output"] 追加到了 state["messages"]
        # 但前端并不知道“最终一版”的纯文本，所以这里以最后一次覆盖文本为准，做一次固化即可
        if final_text:
            st.session_state["messages"].append({"role": "assistant", "content": final_text})

        # 清空临时占位
        placeholder.empty()

        # 触发一次重渲染以显示新历史
        st.rerun()

    # 输入区
    st.text_input("你：", key="user_input", on_change=submit_message, placeholder="例如：帮我来一份操作简单的三明治食谱～")




if __name__ == "__main__":
    main()
