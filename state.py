# types/state.py
from typing import TypedDict, List


class RecipeGraphState(TypedDict):
    ingredients: List[str]
    requirements: str
    target_url: str
    scraped_content: str
    recipe: str


class RecipeAppState(TypedDict):
    ingredients: List[str]  # 初始食材
    requirements: str  # 其他要求
    search_query: str  # 生成的搜索关键词
    scraped_urls: List[str]  # 爬取到的URL列表
    scraped_content: str  # 爬取并清洗后的核心内容
    final_recipe: str  # 最终生成的食谱
    error_message: str  # 错误信息
    retry_count: int  # 重试次数
