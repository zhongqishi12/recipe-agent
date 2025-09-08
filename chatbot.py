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
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "user_input" not in st.session_state:
        st.session_state["user_input"] = ""

    placeholder = st.empty()

    def submit_message():
        user_message = st.session_state["user_input"].strip()
        if user_message:
            st.session_state["messages"].append({"role": "user", "content": user_message})
            st.session_state["user_input"] = ""
            assistant_message = ""
            for response in chat_interface_stream(user_message):  # ✅ 改成 user_message
                assistant_message += response
                print(assistant_message)
                placeholder.markdown(f"**Assistant:** {assistant_message}")

            st.session_state["messages"].append({"role": "assistant", "content": assistant_message})

    st.text_input("You:", key="user_input", on_change=submit_message)

    for msg in st.session_state["messages"]:
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['content']}")


if __name__ == "__main__":
    main()
