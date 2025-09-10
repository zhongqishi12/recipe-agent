# tools/dashscope_web_search.py
import os
from typing import List, Dict, Any, Optional

import dashscope
from http import HTTPStatus


class DashScopeWebSearchTool:
    """
    基于阿里云百炼 (DashScope) 的通义千问联网搜索工具。
    支持指定搜索策略 (turbo / max)，并可返回带来源信息的结果。
    """

    def __init__(self,
                 api_key: Optional[str] = None,
                 model: str = "qwen-plus",
                 strategy: str = "turbo",
                 forced: bool = False):
        """
        初始化 WebSearch 工具。

        :param api_key: API Key（默认从环境变量 DASHSCOPE_API_KEY 获取）
        :param model: 使用的模型，默认 "qwen-plus"
        :param strategy: 搜索策略，"turbo" 或 "max"
        :param forced: 是否强制联网搜索
        """
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("缺少 DASHSCOPE_API_KEY，请在环境变量中配置。")

        self.model = model
        self.strategy = strategy
        self.forced = forced

        dashscope.api_key = self.api_key

    def search(self, query: str) -> Dict[str, Any]:
        """
        执行一次联网搜索。

        :param query: 用户查询
        :return: 包含搜索结果和模型回答的字典
        """
        try:
            response = dashscope.Generation.call(
                model=self.model,
                messages=[{"role": "user", "content": query}],
                enable_search=True,
                search_options={
                    "forced_search": self.forced,
                    "enable_source": True,
                    "enable_citation": True,
                    "citation_format": "[ref_<number>]",
                    "search_strategy": self.strategy,
                },
                result_format="message",
            )

            if response.status_code != HTTPStatus.OK:
                return {
                    "error": f"调用失败: {response.code}, {response.message}",
                    "results": [],
                    "answer": None,
                }

            # 搜索来源
            search_info = getattr(response.output, "search_info", {})
            search_results = search_info.get("search_results", [])

            # 模型回答
            answer = response.output.choices[0].message.content

            return {
                "results": search_results,
                "answer": answer,
            }

        except Exception as e:
            return {"error": str(e), "results": [], "answer": None}
