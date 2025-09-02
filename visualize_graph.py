# app.py
from dotenv import load_dotenv

load_dotenv()
from nodes.graph import get_chat_app  # 从你的graph.py中导入已经编译好的app


def save_graph_image():
    """
    将LangGraph工作流可视化并保存为PNG图片。
    """
    try:
        app = get_chat_app()
        # 1. 获取图的可视化对象
        graph_image_bytes = app.get_graph().draw_png(layout="LR")

        # 2. 将图片数据写入文件
        with open("recipe_agent_workflow.png", "wb") as f:
            f.write(graph_image_bytes)

        print("✅ 成功！工作流可视化图片已保存为 'recipe_agent_workflow.png'")

    except Exception as e:
        print(f"❌ 生成图片失败，请确保已正确安装 pygraphviz 和其系统依赖。错误: {e}")


if __name__ == "__main__":
    save_graph_image()