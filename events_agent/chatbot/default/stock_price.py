from typing import List
from tools.tool import BaseTool, Params
import yfinance as yf

class StockPrice(BaseTool):    
    @property
    def name(self) -> str:
        return "StockPrice"
    
    @property
    def description(self) -> str:
        return "Get stock prices from Yahoo Finance"
    
    @property
    def parameters(self) -> List[Params]:
        return [
            Params(
                name="symbol",
                type="string",
                description="Stock ticker symbol"
            )
        ]
    
    def execute(self, symbol: str) -> str:
        try:
            ticker = yf.Ticker(symbol)
            price = ticker.info.get("regularMarketPrice")
            name = ticker.info.get("shortName", symbol)

            return f"Price of {name} ({symbol}) is ${price:.2f}"

        except Exception as e:
            return f"Error: {str(e)}"
