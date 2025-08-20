from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from state import FilterDecision
from utils.llm_provider import llm


def create_filter_chain():
    """创建一个接收用户需求和单个菜谱，并输出筛选决定的链"""

    parser = PydanticOutputParser(pydantic_object=FilterDecision)

    prompt = ChatPromptTemplate.from_template(
        """你是一位严谨的菜谱筛选官。你的任务是判断一个给定的菜谱是否满足用户的需求。

        【用户的需求】
        - 他们拥有的主要食材: {user_ingredients}
        - 其他要求和偏好: {other_requirements}

        【待评估的菜谱】
        - 标题: {recipe_title}
        - 所需食材清单: {recipe_ingredients}
        - 烹饪步骤: {recipe_steps}

        【你的评审标准】
        1.  **食材匹配度**: 菜谱是否主要使用了用户拥有的食材？允许缺少1-2样常见辅料（如葱姜蒜、油盐），或需要额外购买1-2样核心食材。
        2.  **需求符合度**: 菜谱是否符合用户的其他要求？（例如，如果用户要求'健身餐'，请评估它的热量和做法是否健康；如果要求'快手菜'，请评估步骤是否耗时过长）。
        3.  **综合评分**: 基于以上两点，给出一个1-10的综合推荐分。

        请根据以上标准，给出你的决定、原因和评分。

        {format_instructions}
        """
    )

    return prompt | llm | parser


# 实例化筛选链
filter_chain = create_filter_chain()