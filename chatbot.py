import streamlit as st
import asyncio
from dotenv import load_dotenv
load_dotenv()
from nodes.graph import get_chat_app

async def run_recipe_graph_stream(query: str):
    inputs = {"user_raw_query": query}
    app = get_chat_app()
    async for state in app.astream(inputs):
        yield state.get("messages", [])

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
    st.title("🍲 智能菜谱助手")
    st.write("欢迎使用智能菜谱助手！请输入您的问题或需求，我们将为您提供个性化的菜谱建议和烹饪指导。")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    def submit_message():
        user_message = st.session_state.user_input
        if user_message:
            st.session_state.messages.append({"role": "user", "content": user_message})
            st.session_state.user_input = ""
            with st.spinner("正在生成回复..."):
                for response in chat_interface_stream(user_message):
                    if response:
                        if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "assistant":
                            st.session_state.messages[-1]["content"] = response
                        else:
                            st.session_state.messages.append({"role": "assistant", "content": response})
                        st.experimental_rerun()

    user_input = st.text_input("请输入您的问题或需求：", key="user_input", on_change=submit_message)

    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"**用户:** {message['content']}")
        else:
            st.markdown(f"**助手:** {message['content']}")


if __name__ == "__main__":
    main()