# tools/deepsearch.py
import os
import requests

class DeepSearchTool:
    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY")  # 建议用 Serper
        self.endpoint = "https://google.serper.dev/search"

    def search_recipes(self, query: str, num_results: int = 5):
        """调用搜索引擎，返回食谱链接和摘要"""
        headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}
        payload = {"q": f"{query} 食谱 site:xiachufang.com OR site:allrecipes.com OR site:douguo.com"}
        resp = requests.post(self.endpoint, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for item in data.get("organic", [])[:num_results]:
            results.append({
                "title": item.get("title"),
                "url": item.get("link"),
                "snippet": item.get("snippet")
            })
        return results
