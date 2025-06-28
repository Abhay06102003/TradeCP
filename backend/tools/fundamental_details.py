import yfinance as yf
import pydantic
from typing import Any

class FundamentalDetails(pydantic.BaseModel):
    PE: float | Any | None
    EPS: float | Any
    ROE: float | Any
    ROA: float | Any
    PB: float | Any
    PS: float | Any
    
def get_fundamental_metrics(ticker_symbol: str) -> FundamentalDetails:
    """
    Fetch PE, EPS, ROE, ROA, PB and PS for a given stock using yfinance.

    Parameters
    ----------
    ticker_symbol : str
        e.g. "AAPL", "MSFT"

    Returns
    -------
    dict
        {
          "PE":  float or None,  # trailing P/E
          "EPS": float or None,  # trailing EPS
          "ROE": float or None,  # return on equity (as a decimal, e.g. 0.27)
          "ROA": float or None,  # return on assets
          "PB":  float or None,  # price / book
          "PS":  float or None   # price / sales (trailing 12m)
        }
    """
    tkr = yf.Ticker(ticker_symbol)
    info = tkr.info

    results = {
        "PE":  info.get("trailingPE"),
        "EPS": info.get("trailingEps"),
        "ROE": info.get("returnOnEquity"),
        "ROA": info.get("returnOnAssets"),
        "PB":  info.get("priceToBook"),
        "PS":  info.get("priceToSalesTrailing12Months"),
    }

    return FundamentalDetails(
        PE=results["PE"],
        EPS=results["EPS"],
        ROE=results["ROE"],
        ROA=results["ROA"],
        PB=results["PB"],
        PS=results["PS"]
    )
