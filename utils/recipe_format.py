from typing import List, Dict


class RecipeFormatter:
    """食谱格式化工具类"""

    def format_recipes_to_markdown(self, recipes: List[Dict]) -> str:
        """将多个食谱格式化为Markdown文本"""
        if not recipes:
            return "暂无食谱信息。"

        formatted_recipes = [
            self._format_single_recipe(i, recipe)
            for i, recipe in enumerate(recipes)
        ]
        return "\n\n---\n\n".join(formatted_recipes)

    def _format_single_recipe(self, index: int, recipe_data: Dict) -> str:
        """格式化单个食谱为Markdown文本"""
        md_parts = [
            f"### {index + 1}. {recipe_data.get('title', '无标题食谱')}",
            "",
            "**- 用料清单 -**"
        ]

        md_parts.extend(self._format_ingredients(recipe_data.get('ingredients', [])))
        md_parts.append("")  # 空行
        md_parts.append("**- 烹饪步骤 -**")
        md_parts.extend(self._format_steps(recipe_data.get('steps', [])))

        if recipe_data.get('origin_url'):
            md_parts.append(f"\n> 来源: [{recipe_data['origin_url']}]({recipe_data['origin_url']})")

        return "\n".join(md_parts)

    def _format_ingredients(self, ingredients: List[Dict]) -> List[str]:
        """格式化食材列表"""
        if not ingredients:
            return ["* 未能解析出用料信息。"]
        return [f"* {ing.get('name', '')}: {ing.get('quantity', '')}" for ing in ingredients]

    def _format_steps(self, steps: List[str]) -> List[str]:
        """格式化烹饪步骤"""
        if not steps:
            return ["1. 未能解析出步骤信息。"]
        return [f"{idx + 1}. {step}" for idx, step in enumerate(steps)]