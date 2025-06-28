# sector_info.py

import yfinance as yf
import pydantic

# Map human‐readable sector names → representative ETFs

class SectorMetrics(pydantic.BaseModel):

    sector: str
    period: str
    growth_pct: float
    trailingPE: float | None
    forwardPE: float | None
    dividendYield: float | None

def get_sector_metrics(sector_name: str,
                       period: str = '1mo') -> SectorMetrics:
    """
    Fetches:
      • growth_pct     – % price change over `period` (e.g. '1mo', '3mo', '1y')
      • trailingPE     – current trailing P/E
      • forwardPE      – current forward  P/E
      • dividendYield  – latest dividend yield (as a fraction, e.g. 0.018)
    for the ETF proxying your chosen sector.

    Args:
      sector_name: one of the keys in SECTOR_ETF_MAP
      period:       any yfinance‐supported string (e.g. '5d','1mo','6mo','1y','5y')

    Returns:
      {
        'sector':         str,
        'period':         str,
        'growth_pct':     float,
        'trailingPE':     float | None,
        'forwardPE':      float | None,
        'dividendYield':  float | None
      }
    """
    #avialable sectors

    SECTOR_ETF_MAP = {
        'Information Technology': 'XLK',
        'Health Care':             'XLV',
        'Financials':              'XLF',
        'Consumer Discretionary':  'XLY',
        'Communication Services':  'XLC',
        'Industrials':             'XLI',
        'Consumer Staples':        'XLP',
        'Utilities':               'XLU',
        'Energy':                  'XLE',
        'Real Estate':             'XLRE',
        'Materials':               'XLB'
    }
    etf = SECTOR_ETF_MAP.get(sector_name)
    if not etf:
        raise ValueError(f"Unknown sector: {sector_name!r}. "
                         f"Valid names: {list(SECTOR_ETF_MAP)}")

    tkr = yf.Ticker(etf)
    # historical close prices
    hist = tkr.history(period=period)
    if hist.empty:
        raise RuntimeError(f"No price data for {etf} over period {period!r}")

    start, end = hist['Close'].iloc[0], hist['Close'].iloc[-1]
    growth_pct = (end - start) / start * 100

    info = tkr.info
    return SectorMetrics(
        sector=sector_name,
        period=period,
        growth_pct=growth_pct,
        trailingPE=info.get('trailingPE'),
        forwardPE=info.get('forwardPE'),
        dividendYield=info.get('dividendYield'),
    )

if __name__ == '__main__':
    # quick test
    print(get_sector_metrics('Information Technology', period='1y'))
