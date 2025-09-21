from typing import List
from tools.tool import BaseTool, Params
import requests
from bs4 import BeautifulSoup
import urllib.parse
import os

class News(BaseTool):
    @property
    def name(self) -> str:
        return "News"

    @property
    def description(self) -> str:
        return "Get the latest News"

    @property
    def parameters(self) -> List[Params]:
        return [
            Params(
                name="query",
                type="string",
                description="The search query for News articles"
            )
        ]

    def execute(self, query: str) -> str:
        try:
            query = urllib.parse.quote_plus(query)
            url = f"https://news.google.com/rss/search?q={query}&hl=en-MY&gl=MY&ceid=MY:en"

            headers = {
                "User-Agent": os.getenv("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            }

            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                return f"Failed to fetch news: {response.status_code}"

            soup = BeautifulSoup(response.content, "xml")
            items = soup.find_all("item")[:5]

            result = f"News for '{query}':\n\n"
            for item in items:
                title = item.title.text
                link = item.link.text
                source = item.source.text if item.source else "Unknown Source"
                result += f"• {title} ({source})\n  {link}\n\n"

            return result.strip()

        except Exception as e:
            return f"Error: {str(e)}"
