from fastmcp import FastMCP
from tools.find_ticker import find_and_describe
from tools.sheets_details import get_sheets_details
from tools.news import get_news
from tools.price_details import get_price
from tools.patterns import get_financial_data
from tools.technical_analysis import TechnicalAnalysis
from tools.fundamental_details import get_fundamental_metrics
from tools.sector_details import get_sector_metrics
from ollama import Client, ResponseError
import json


mcp = FastMCP("My MCP Server")
client = Client()

def summarize_stock_data(sections):

    selection_criteria = mcp._read_resource("status://details_for_selection_of_stock")

    
    # Enhanced system message for better financial analysis
    system_msg = (
        "You are a senior financial analyst with expertise in equity research and investment analysis. "
        "Your task is to provide comprehensive, professional financial summaries that combine data analysis with actionable insights. "
        "You must:\n"
        "- Present data in a clear, structured format with proper context\n"
        "- Identify key trends, strengths, and areas of concern\n"
        "- Use appropriate financial terminology and industry standards\n"
        "- Maintain objectivity while highlighting significant findings\n"
        "- Format numbers with proper units and currency symbols\n"
        "- Provide comparative context where relevant (industry benchmarks, historical performance)\n"
        "- Conclude with a balanced assessment and potential implications for investors"
        "You need to analyze the data and provide a summary of the stock based on the selection criteria."
        f"**SELECTION CRITERIA:**\n{selection_criteria}"
    )
    
    # Enhanced user message with structured analysis framework
    user_msg = (
        "Analyze the following stock data JSON and provide a comprehensive financial summary following this structure:\n\n"
        "**EXECUTIVE SUMMARY**\n"
        "- Brief overview of the company's current financial position\n"
        "- Key highlights and concerns in 2-3 sentences\n\n"
        "**DETAILED ANALYSIS**\n"
        "- Extract and present ALL numerical data with proper context\n"
        "- Group related metrics (profitability, liquidity, growth, valuation, etc.)\n"
        "- Identify the reporting currency and ensure consistency\n"
        "- Highlight significant trends, ratios, and performance indicators\n"
        "- Note any unusual or standout metrics\n\n"
        "**KEY INSIGHTS**\n"
        "- Financial strengths and competitive advantages\n"
        "- Areas of concern or potential risks\n"
        "- Performance relative to typical industry standards (if applicable)\n\n"
        "**INVESTMENT PERSPECTIVE**\n"
        "- What this data suggests about the company's financial health\n"
        "- Potential implications for different types of investors\n\n"
        "Ensure your analysis is data-driven, citing specific figures from the JSON. "
        "Present information in a way that both institutional and retail investors can understand and act upon.\n\n"
        f"**DATA TO ANALYZE:**\n{json.dumps(sections, indent=2)}"
    )

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


@mcp.tool(description="Get the price of a stock. This can be used to get the pricing details of a stock.")
def get_stock_price(ticker: str) -> str:
    price = get_price(ticker=ticker)
    price = price.model_dump_json(indent=2)
    summary = summarize_stock_data(price)
    return summary

@mcp.tool(description="Get the indicator data of a stock")
def get_stock_indicator_data(ticker: str) -> str:
    financial_data = get_financial_data(ticker=ticker)
    summary = summarize_stock_data(financial_data)
    return summary

@mcp.tool(description="Get Financial sheets Details of a stock. This can be used to get the financial details of a stock.")
def get_stock_financial_sheets(ticker: str) -> str:
    details = get_sheets_details(ticker=ticker)
    details = details.model_dump_json(indent=2)
    summary = summarize_stock_data(details)
    return summary

@mcp.tool(description="Get the news of a stock. This can be used to get the news of a stock. Used to predict market sentiment.")
def get_stock_news(ticker: str) -> str:
    news = get_news(ticker=ticker)
    news = news.model_dump_json(indent=2)
    summary = summarize_stock_data(news)
    return summary


@mcp.tool(description="Get Ticker from the name of the stock. This can be used to get the ticker of a stock.",)
def get_ticker_from_name(name: str) -> dict:
    ticker = find_and_describe(company_name=name)
    return ticker

@mcp.tool(description="Get the Technical Analysis and Pattern analysis of a stock.This can be used to forecast the future price of the stock.")
def get_stock_technical_analysis(ticker: str) -> str:
    technical_analysis = TechnicalAnalysis(ticker=ticker)
    data = technical_analysis.get_data_in_shape()
    data = data.model_dump_json(indent=2)
    summary = summarize_stock_data(data)
    return summary

@mcp.tool(description="Get the fundamental details of a stock. This can be used to get the fundamental details of a stock.")
def get_stock_fundamental_details(ticker: str) -> str:
    fundamental_details = get_fundamental_metrics(ticker_symbol=ticker)
    fundamental_details = fundamental_details.model_dump_json(indent=2)
    summary = summarize_stock_data(fundamental_details)
    return summary

@mcp.tool(description="sector_name and time_period is the input.Get the sector metrics of a stock. Available sectors: 'Information Technology', 'Health Care', 'Financials', 'Consumer Discretionary', 'Communication Services', 'Industrials', 'Consumer Staples', 'Utilities', 'Energy', 'Real Estate', 'Materials'. Use exact sector names as listed.Time period available: '1mo', '3mo', '6mo', '1y', '5y'")
def get_stock_sector_metrics(sector_name: str, time_period: str = '1mo') -> str:
    sector_metrics = get_sector_metrics(sector_name=sector_name, period=time_period)
    sector_metrics = sector_metrics.model_dump_json(indent=2)
    summary = summarize_stock_data(sector_metrics)
    return summary

@mcp.resource("status://details_for_selection_of_stock",description="This is a stepwise approach and all the criteria need to be monitored to get to better decisions.")
def get_decision_criteria():
    decision_criteria = (
        "Universe – All U.S. large-caps (≥ $5 B market cap)\n"

"Liquidity & Size\n"
"• Avg. daily volume (3 mo) ≥ $20 M\n"
"• Market cap ≥ $5 B\n"

"Valuation\n"
"• P/E (trailing) < 25× – avoid overvaluation\n"
"• P/B < 3× – limit intangible risk\n"
"• P/S (TTM) < 3× – cap revenue multiple\n"

"Profitability\n"
"• EPS (trailing) > 0 – positive earnings\n"
"• ROE ≥ 15 % – strong equity returns\n"
"• ROA ≥ 8 % – efficient asset use\n"

"Growth & Quality\n"
"• EPS YoY growth ≥ 10 %\n"
"• Revenue YoY growth ≥ 8 %\n"
"• Debt/Equity ≤ 1.0\n"

"Composite Scoring\n"
"• Normalize each metric to 0–1\n"
"• Weights: 30 % valuation, 40 % profitability, 30 % growth\n"
"• Compute overall score & rank\n"

"Final Review – Analyst check for sector risks, one-off distortions\n"
    )
    return 

@mcp.resource("status://available_sectors", description="List of all available sectors for sector metrics analysis.")
def get_available_sectors():
    return """Available Sectors for Analysis:
    
• Information Technology (XLK)
• Health Care (XLV) 
• Financials (XLF)
• Consumer Discretionary (XLY)
• Communication Services (XLC)
• Industrials (XLI)
• Consumer Staples (XLP)
• Utilities (XLU)
• Energy (XLE)
• Real Estate (XLRE)
• Materials (XLB)

Note: Use the exact sector names as listed above. Each sector is tracked via its corresponding ETF for metrics calculation."""

@mcp.resource("status://config",description="This is the configuration of the app. It contains the details of the app.")
def get_app_details():
    return "This app is currently in development. contact Abhay Chourasiya"

if __name__ == "__main__":
    mcp.run()
    # print(get_stock_technical_analysis("SUZLON.NS"))

