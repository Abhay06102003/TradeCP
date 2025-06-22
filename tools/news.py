import sys
sys.path.append(".")
import yfinance as yf
import pydantic

class News(pydantic.BaseModel):
    news_summary: str

def get_news(ticker: str):
    ticker_obj = yf.Ticker(ticker)
    news = ticker_obj.get_news(count=20)
    summary = ""
    for news_item in news:
        content = news_item['content']
        summary += f"\nTitle:\n{content['title']}\nSummary:\n{content['summary']}\n\n"

    return News(news_summary=summary)
