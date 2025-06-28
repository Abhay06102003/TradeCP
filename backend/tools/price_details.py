import yfinance as yf
import pydantic
import pandas as pd
from typing import Any

class Price(pydantic.BaseModel):
    company_information: dict[Any, Any]
    current_price: float | Any
    historical_prices: list[dict[Any, Any]]
    earnings_history: dict[Any, Any] | pd.DataFrame
    estimates: dict[Any, Any] | pd.DataFrame
    
    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

def get_price(ticker: str):
    ticker_obj = yf.Ticker(ticker)
    company_information = ticker_obj.info
    current_price = ticker_obj.get_analyst_price_targets()
    historical_prices = ticker_obj.history()
    historical_prices = historical_prices.to_dict(orient="records")
    earnings_history = ticker_obj.get_earnings_history(as_dict=True)
    estimates = ticker_obj.get_earnings_estimate(as_dict=True)
    return Price(
        company_information=company_information,
        current_price=current_price['current'],
        historical_prices=historical_prices,
        earnings_history=earnings_history,
        estimates=estimates
    )

if __name__ == "__main__":
    print(get_price("AAPL"))