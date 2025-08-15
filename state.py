# types/state.py
from typing import TypedDict, List
from pydantic import BaseModel, Field

class ScrapedContent(TypedDict):
    url: str  # 爬取的食谱页面URL
    content: str  # 爬取的食谱内容HTML


class RecipeGraphState(TypedDict):
    ingredients: List[str]
    requirements: str
    target_url: str
    scraped_recipes: List[dict]  # 爬虫节点输出的原始数据
    parsed_recipes: List[dict]  # 解析节点输出的结构化数据
    scraped_contents: List[ScrapedContent]  # 爬取的内容列表
    recipe: str
    max_recipes: int  # 爬取的最大食谱数量


class RecipeAppState(TypedDict):
    ingredients: List[str]  # 初始食材
    requirements: str  # 其他要求
    search_query: str  # 生成的搜索关键词
    scraped_urls: List[str]  # 爬取到的URL列表
    scraped_content: str  # 爬取并清洗后的核心内容
    final_recipe: str  # 最终生成的食谱
    error_message: str  # 错误信息
    retry_count: int  # 重试次数



# 3. (新增) 使用Pydantic定义我们希望LLM输出的数据结构
class Ingredient(BaseModel):
    name: str = Field(description="食材的名称")
    quantity: str = Field(description="食材的数量或用量")


class ParsedRecipe(BaseModel):
    title: str = Field(description="菜谱的标题")
    ingredients: List[Ingredient] = Field(description="菜谱所需食材的列表")
    steps: List[str] = Field(description="烹饪步骤的列表，每一步是一个字符串")
