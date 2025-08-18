# types/state.py
from typing import TypedDict, List
from pydantic import BaseModel, Field


class Ingredient(BaseModel):
    name: str = Field(description="食材的名称")
    quantity: str = Field(description="食材的数量或用量")


class ScrapedContent(TypedDict):
    url: str  # 爬取的食谱页面URL
    title: str  # 爬取的食谱标题
    ingredients: List[Ingredient]  # 食材列表
    steps: List[str]


class ParsedRecipe(BaseModel):
    title: str = Field(description="菜谱的标题")
    ingredients: List[Ingredient] = Field(description="菜谱所需食材的列表")
    steps: List[str] = Field(description="烹饪步骤的列表，每一步是一个字符串")
    origin_url: str = Field(description="菜谱的来源URL")


class FilterDecision(BaseModel):
    """用于描述LLM对单个菜谱的筛选决定"""
    decision: bool = Field(description="如果菜谱符合用户需求，则为 True，否则为 False")
    reasoning: str = Field(description="做出该决定的简要原因，例如'食材匹配度高且符合健身需求'")
    score: int = Field(description="根据匹配度给出的1-10分的评分")


# --- 用于解析用户输入的Pydantic模型 ---
class UserInputPlan(BaseModel):
    search_keywords: List[str] = Field(description="适合用于搜索引擎的菜谱或菜系关键词，例如 '三明治', '早餐', '川菜'")
    user_ingredients: List[str] = Field(description="用户明确提到的已有食材列表，例如 '生菜', '鸡蛋'")
    recipe_count: int = Field(description="用户希望生成的食谱数量", default=1)
    other_requirements: str = Field(description="用户的其他偏好或要求，例如 '低脂', '素食', '儿童餐'")


class RecipeGraphState(TypedDict):
    # --- 输入与规划阶段 ---
    user_raw_query: str  # 用户最原始的自然语言输入
    search_keywords: List[str]  # 从用户输入中提取出的搜索关键词 (如: "三明治", "早餐")
    user_ingredients: List[str]  # 从用户输入中提取出的明确食材 (如: "生菜", "鸡蛋")
    recipe_count: int  # 用户希望获取的食谱数量 (如: 2)
    requirements: str  # 用户的其他要求 (如: "低脂肪", "适合儿童")

    # --- 爬虫阶段 ---
    target_url: str
    scraped_recipes: List[dict]  # 爬虫节点输出的原始数据
    scraped_contents: List[ScrapedContent]  # 爬取的内容列表
    parsed_recipes: List[ParsedRecipe]  # 解析节点输出的结构化数据

    # --- 生成阶段 ---
    final_recipe: str  # Markdown格式的菜谱，包括所有的
    output_file_path: str


class RecipeAppState(TypedDict):
    ingredients: List[str]  # 初始食材
    requirements: str  # 其他要求
    search_query: str  # 生成的搜索关键词
    scraped_urls: List[str]  # 爬取到的URL列表
    scraped_content: str  # 爬取并清洗后的核心内容
    final_recipe: str  # 最终生成的食谱
    error_message: str  # 错误信息
    retry_count: int  # 重试次数
