import requests
import time
from typing import List, Dict
import yfinance as yf


def search_tickers(query: str,
                   region: str = "",
                   lang:   str = "en",
                   max_retries: int = 5,
                   base_sleep:  float = 1.0
                  ) -> List[Dict]:
    """
    Query Yahoo Finance search with simple exponential backoff on HTTP 429.
    """
    url = "https://query2.finance.yahoo.com/v1/finance/search"
    params = {"q": query, "lang": lang, "region": region}
    headers = {"User-Agent": "MyApp/1.0"}  # mimic a real browser
    
    for attempt in range(1, max_retries + 1):
        resp = requests.get(url, params=params, headers=headers)
        if resp.status_code == 200:
            return resp.json().get("quotes", [])
        elif resp.status_code == 429:
            sleep_time = base_sleep * (2 ** (attempt - 1))
            print(f"Rate-limited: retrying in {sleep_time:.1f}s…")
            time.sleep(sleep_time)
        else:
            resp.raise_for_status()
    
    raise RuntimeError(f"Failed after {max_retries} retries due to rate limits.")


def find_and_describe(company_name: str):
    # 1. Lookup possible symbols
    candidates = search_tickers(company_name)
    if not candidates:
        raise ValueError(f"No tickers found for “{company_name}”")
    # 2. Pick the top match
    symbol = candidates[0]["symbol"]
    # 3. Fetch its info
    info = yf.Ticker(symbol).info
    return {
        "symbol":   symbol,
        "shortName": info.get("shortName"),
        "longName":  info.get("longName"),
        "sector":    info.get("sector"),
        "industry":  info.get("industry"),
        "website":   info.get("website"),
    }
    

