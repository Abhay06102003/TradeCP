from fastmcp import FastMCP
from tools.find_ticker import find_and_describe
from tools.sheets_details import get_sheets_details
from tools.news import get_news
from tools.price_details import get_price
from tools.patterns import get_financial_data
from ollama import Client, ResponseError
import json
import pydantic


client = Client()

def summarize_stock_data(sections):
    
    # 4. Build the system message to enforce schema compliance
    system_msg = (
        "You are a good Financial Analyst. You are given a JSON of stock data. You need to summarize the data in a professional way."
        "You need to extract the actual figures according to the key and values provided in the json."
    )
    
    # 5. Build the user message containing the raw sections
    user_msg = (
        "Here is the stock data as JSON. Read each section and Summarize as the Analyst would do."
        "Include all actual data and figures in the summary. Summary should give a brief information about company performance in a analytical way."
        "Summary should include all the details and the actual data that the below json provides and should be in detail and reflects the professionalism of a financial analyst."
        "Given data include some data in currency and other are ratios and some numerical data.You need to find the current currency in which the data is in according to the information provided. You are a good data extractor and summarizer."
        f"{json.dumps(sections, indent=2)}"
    )
    with open("user_msg.txt",'w') as f:
        f.write(user_msg)

    try:
        # 6. Call the model (non-streaming) :contentReference[oaicite:1]{index=1}
        response = client.chat(
            model="qwen3:4b",
            messages=[
                {"role": "system",  "content": system_msg},
                {"role": "user",    "content": user_msg},
            ],
            stream=False
        )
    except ResponseError as e:
        raise RuntimeError(f"LLM error {e.status_code}: {e.error}")

    # 7. Parse the returned JSON into our Pydantic model
    content = response.message.content
    
    # Remove any thinking content between <think> and </think> tags
    if content and '<think>' in content and '</think>' in content:
        start = content.find('<think>')
        end = content.find('</think>') + len('</think>')
        content = content[:start] + content[end:]
    
    if content is None:
        raise RuntimeError("No content returned from the model")
    return content

mcp = FastMCP("My MCP Server")

@mcp.tool(description="Get the price of a stock")
def get_stock_price(ticker: str) -> str:
    price = get_price(ticker=ticker)
    price = price.model_dump_json(indent=2)
    summary = summarize_stock_data(price)
    return summary

@mcp.tool(description="Get the Technical Analysis and Pattern analysis of a stock")
def get_stock_financial_data(ticker: str) -> str:
    financial_data = get_financial_data(ticker=ticker)
    summary = summarize_stock_data(financial_data)
    return summary

@mcp.tool(description="Get the details of a stock")
def get_stock_details(ticker: str) -> str:
    details = get_sheets_details(ticker=ticker)
    details = details.model_dump_json(indent=2)
    summary = summarize_stock_data(details)
    return summary

@mcp.tool(description="Get the news of a stock")
def get_stock_news(ticker: str) -> str:
    news = get_news(ticker=ticker)
    news = news.model_dump_json(indent=2)
    summary = summarize_stock_data(news)
    return summary

# @mcp.tool(description="Get the price of a stock")

@mcp.tool(description="Get Ticker from the name of the stock")
def get_ticker_from_name(name: str) -> dict:
    ticker = find_and_describe(company_name=name)
    return ticker

@mcp.resource("status://config")
def get_app_details():
    return "This app is currently in development. contact Abhay Chourasiya"

if __name__ == "__main__":
    mcp.run()
