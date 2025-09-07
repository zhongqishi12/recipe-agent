# graph.py
import os
from typing import TypedDict, List
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph

from nodes.chains import filter_chain
from state import RecipeGraphState, RecipeAppState, ParsedRecipe, UserInputPlan, FilterDecision
from tools.tools import scrape_xiachufang_recipe
from tools.douguo_scraper import DouguoRecipeScraper
from utils.llm_provider import llm
from langchain_core.output_parsers import JsonOutputParser, PydanticOutputParser
from datetime import datetime
from utils.recipe_format import RecipeFormatter


# --- 新增的初始节点函数 ---
def parse_input_node(state: RecipeGraphState):
    """
    使用LLM解析用户的原始输入，提取关键信息并形成规划。
    """
    print("--- 节点: 解析用户输入 ---")
    state.setdefault("messages", []).append({"role": "assistant", "content": "🤔 正在解析你的需求..."})

    parser = PydanticOutputParser(pydantic_object=UserInputPlan)

    prompt = ChatPromptTemplate.from_template(
        """你是一个任务规划AI。请解析用户的请求，并提取出关键信息。

        {format_instructions}

        用户请求如下:
        "{user_query}"
        """
    )

    chain = prompt | llm | parser

    plan = chain.invoke({
        "user_query": state['user_raw_query'],
        "format_instructions": parser.get_format_instructions()
    })

    # 将解析出的规划更新到State中
    state['search_keywords'] = plan.search_keywords
    state['user_ingredients'] = plan.user_ingredients
    state['recipe_count'] = plan.recipe_count
    state['requirements'] = plan.other_requirements

    print(f"  > 解析完成: 关键词={plan.search_keywords}, 食材={plan.user_ingredients}, 数量={plan.recipe_count}")
    return state


# 3. 定义图的节点
async def scrape_node(state: RecipeGraphState):
    print("--- 节点: 爬取内容 ---")
    state.setdefault("messages", []).append({"role": "assistant", "content": "🔍 正在搜索并爬取食谱，请稍候..."})
    # 使用 search_keywords 作为爬取关键字
    search_keywords = state.get('search_keywords', '')
    print(f"爬取关键字: {search_keywords}")
    max_recipes = state.get('recipe_count', 1)
    scrape_recipes = max_recipes * 5  # 爬取数量是需要数量的2倍，方便后续筛选

    # 使用豆果美食爬虫
    douguo_scraper = DouguoRecipeScraper()
    # 将搜索关键字转换为列表格式
    if isinstance(search_keywords, str):
        keywords_list = search_keywords.split()
    else:
        keywords_list = search_keywords

    scraped_content = await douguo_scraper.scrape_douguo(keywords_list, scrape_recipes)
    state['scraped_contents'] = scraped_content
    return state


def parse_recipes_node(state: RecipeGraphState):
    """解析爬取的食谱内容"""
    print("--- 节点: 解析食谱 ---")
    state.setdefault("messages", []).append({"role": "assistant", "content": "📝 正在解析爬取的食谱内容..."})
    scraped_contents = state['scraped_contents']
    print(f"解析 {len(scraped_contents)} 个爬取的食谱内容...")
    print(scraped_contents)
    parsed_recipes = []

    parser = JsonOutputParser(pydantic_object=ParsedRecipe)
    prompt = ChatPromptTemplate.from_template(
        """你是一个精通网页解析的AI助手。你的任务是从给定的HTML片段中提取菜谱信息。

        根据以下HTML内容，提取菜谱的标题、所有用料（包括名称和用量）以及详细的烹饪步骤。

        页面标题: {page_title}
        来源URL: {origin_url}

        {format_instructions}

        HTML内容如下:
        ```html
        {html_content}
        ```
        """
    )

    # 将Prompt、LLM和输出解析器连接起来
    chain = prompt | llm | parser

    for content in scraped_contents:
        try:
            # 调用我们创建好的解析链
            parsed_recipe = chain.invoke({
                "page_title": content['title'],
                "origin_url": content['url'],
                "format_instructions": parser.get_format_instructions()
            })
            # 确保origin_url被设置
            parsed_recipe['origin_url'] = content['url']
            parsed_recipes.append(parsed_recipe)
            print(f"  > 解析成功: {content['url']}")
            print(f"  > <UNK>: {content['title']}")
            print(f"  > <UNK>: {content['content']}")
        except Exception as e:
            print(f"  !! 解析失败: {content['url']}, 错误: {e}")
            # 即使某个页面解析失败，也继续处理下一个
            continue

    state['parsed_recipes'] = parsed_recipes
    return state


# 5. !!! 新增的核心智能节点：筛选食谱 !!!
def filter_recipes_node(state: RecipeGraphState):
    """(智能版) 使用LLM判断每个菜谱与用户需求的匹配度，并进行筛选"""
    print("--- 节点: 正在用LLM智能筛选食谱 ---")
    state.setdefault("messages", []).append({"role": "assistant", "content": "🤖 正在筛选符合你需求的食谱..."})
    user_ingredients = state['user_ingredients']
    other_requirements = state['requirements']
    scraped_contents = state['scraped_contents']
    expected_count = state.get('recipe_count', 1)  # 获取期望的食谱数量

    min_score = 6  # 只保留评分在7分及以上的菜谱
    recipe_scores = []  # 存储食谱和评分

    for recipe in scraped_contents:
        # 将菜谱的食材列表转换为简单字符串，方便输入
        recipe_ingredients_str = ", ".join([f"{ing['name']}({ing['quantity']})" for ing in recipe['ingredients']])

        print(f"> 正在评估菜谱 '{recipe['title']}'...")

        try:
            # 对每个菜谱调用LLM进行评审
            decision_result = filter_chain.invoke({
                "user_ingredients": ", ".join(user_ingredients),
                "other_requirements": other_requirements,
                "recipe_title": recipe['title'],
                "recipe_ingredients": recipe_ingredients_str,
                "recipe_steps": "\n".join(recipe['steps']),
                "format_instructions": PydanticOutputParser(pydantic_object=FilterDecision).get_format_instructions()
            })

            print(
                f"- LLM决策: {decision_result.decision}, 评分: {decision_result.score}, 原因: {decision_result.reasoning}"
            )

            # 根据LLM的决定和评分进行筛选
            if decision_result.decision and decision_result.score >= min_score:
                print("- ✅ 符合要求, 保留该食谱。")
                # 附加LLM的分析结果，供下一步或用户查看
                recipe_scores.append({
                    'recipe': recipe,
                    'score': decision_result.score,
                    'decision': decision_result.decision,
                    'reasoning': decision_result.reasoning
                })
            else:
                print("- ❌ 不符合要求, 舍弃该食谱。")

        except Exception as e:
            print(f"  !! LLM评估失败: {recipe['title']}, 错误: {e}")
            continue

    # 按评分从高到低排序
    recipe_scores.sort(key=lambda x: x['score'], reverse=True)

    # 取前N个最高评分的食谱
    selected_recipes = recipe_scores[:expected_count]

    print(f"\n--- 筛选结果 ---")
    print(f"候选食谱总数: {len(recipe_scores)}")
    print(f"最终选中: {len(selected_recipes)} 份")

    for i, item in enumerate(selected_recipes):
        print(f"{i + 1}. {item['recipe']['title']} - 评分: {item['score']}")

    # 只保存食谱数据到state
    state['filtered_recipes'] = [item['recipe'] for item in selected_recipes]
    return state


def generate_final_recipe_node(state: RecipeGraphState):
    """
    (新功能) 将解析后的结构化食谱数据，直接格式化为面向用户的Markdown文本。
    """
    print("--- 节点: 正在整理并格式化最终结果 ---")

    # 1. 检查是否有可用的解析后食谱
    if not state['filtered_recipes']:
        print(" !! 没有可用的解析后食谱，无法生成。")
        return state

    formatter = RecipeFormatter()
    state['final_recipe'] = formatter.format_recipes_to_markdown(state['filtered_recipes'])
    print("--- 节点: 最终结果已格式化完成！ ---")
    return state


def output_node(state: RecipeGraphState):
    """
    使用LLM对最终的输出进行润色和自然语言组织
    """
    print("--- 节点: Output Node（润色结果） ---")
    state.setdefault("messages", []).append({"role": "assistant", "content": "✨ 正在润色推荐结果..."})

    prompt = ChatPromptTemplate.from_template(
        """请你把下面的食谱推荐结果整理成更自然的对话回复。
        保持友好、简洁，让用户觉得是和一个厨艺助手在聊天。

        下面是生成的食谱：
        {final_recipe}
        """
    )

    chain = prompt | llm
    refined_output = chain.invoke({"final_recipe": state["final_recipe"]})
    state["final_output"] = refined_output.content
    return state


def generate_query_node(state: RecipeAppState):
    print("节点: generate_query")
    # ... 根据食材和需求生成搜索关键词 ...
    state[
        'search_query'] = f"{' '.join(state['ingredients'])} {state['requirements']} recipe site:xiachufang.com OR site:tasty.co"
    state['retry_count'] = 0
    return state


def save_to_markdown_node(state: RecipeGraphState):
    """将所有食谱保存到一个Markdown文件"""
    print("--- 节点: 保存为Markdown文件 ---")

    if not state.get('final_recipe'):
        print(" !! 没有可用的最终食谱内容，无法保存。")
        state['output_file_path'] = ""
        return state

    try:
        # 创建输出目录
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)

        # 使用搜索关键字生成文件名，取前2个关键词
        keywords = state.get('search_keywords', '')
        if isinstance(keywords, list):
            keywords_str = "_".join(keywords[:2])
        else:
            keywords_str = "_".join(str(keywords).split()[:2])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        recipe_count = len(state.get('filtered_recipes', []))
        filename = f"recipes_{keywords_str}_{recipe_count}份_{timestamp}.md"
        file_path = os.path.join(output_dir, filename)

        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            # 文件头部信息
            f.write(f"# 食谱搜索结果\n\n")
            # 使用 user_ingredients 字段
            f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")

            # 添加目录
            if recipe_count > 1:
                f.write("## 目录\n\n")
                for i, recipe in enumerate(state.get('filtered_recipes', [])):
                    title = recipe.get('title', f'食谱{i + 1}')
                    f.write(f"{i + 1}. [{title}](#{i + 1}-{title.replace(' ', '-').lower()})\n")
                f.write("\n---\n\n")

            # 食谱内容
            f.write(state['final_recipe'])

        state['output_file_path'] = file_path
        print(f"--- {recipe_count}份食谱已保存到: {file_path} ---")

    except Exception as e:
        print(f" !! 保存文件失败: {e}")
        state['output_file_path'] = ""

    return state


def get_chat_app():
    # 1. 初始化图
    workflow = StateGraph(RecipeGraphState)

    # 2. 添加所有需要的节点
    workflow.add_node("input_parser", parse_input_node)
    workflow.add_node("scraper", scrape_node)
    workflow.add_node("parser", parse_recipes_node)  # <--- 关键：添加解析节点
    workflow.add_node("filter", filter_recipes_node)
    workflow.add_node("generator", generate_final_recipe_node)
    workflow.add_node("output", output_node)
    #workflow.add_node("save_md", save_to_markdown_node)

    # 3. 设置入口点
    workflow.set_entry_point("input_parser")

    # 4. 定义正确的数据流转边
    workflow.add_edge("input_parser", "scraper")
    workflow.add_edge("scraper", "parser")  # <--- 关键：先爬取，再解析
    workflow.add_edge("parser", "filter")  # <--- 关键：用解析后的数据去筛选
    workflow.add_edge("filter", "generator")
    workflow.add_edge("generator", "output")
    #workflow.add_edge("generator", "save_md")
    # 如果 save_md 是最后一步，可以让它指向 END
    # workflow.add_edge("save_md", END) # 示例

    # 5. 编译图，并命名为 app 以便导出
    app = workflow.compile()
    return app
