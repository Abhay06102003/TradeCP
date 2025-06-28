import pandas as pd
import numpy as np
from scipy.fft import fft
import yfinance as yf
import json
class FinancialAnalyzer:
    """
    A class for computing financial indicators, technical analysis signals,
    candlestick-pattern detection, Fourier-based pattern extraction,
    and trend determination. Outputs structured feature data suitable for LLM ingestion,
    with configurable JSON orientation and sampling to reduce payload size.
    """
    def __init__(self, df: pd.DataFrame):
        """
        Initialize with OHLCV DataFrame indexed by datetime.
        Expected columns: ['Open','High','Low','Close','Volume']
        """
        self.df = df.copy()
        self.features = pd.DataFrame(index=self.df.index)

    def sma(self, window: int = 14) -> pd.Series:
        return self.df['Close'].rolling(window).mean()

    def ema(self, window: int = 14) -> pd.Series:
        return self.df['Close'].ewm(span=window, adjust=False).mean()

    def rsi(self, window: int = 14) -> pd.Series:
        delta = self.df['Close'].diff()
        up = delta.clip(lower=0)
        down = -delta.clip(upper=0)
        ma_up = up.ewm(span=window, adjust=False).mean()
        ma_down = down.ewm(span=window, adjust=False).mean()
        rs = ma_up / ma_down
        return 100 - (100 / (1 + rs))

    def macd(self, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        ema_fast = self.ema(fast)
        ema_slow = self.ema(slow)
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        hist = macd_line - signal_line
        return pd.DataFrame({'MACD': macd_line, 'Signal': signal_line, 'Hist': hist}, index=self.df.index)

    def bollinger_bands(self, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
        ma = self.sma(window)
        std = self.df['Close'].rolling(window).std()
        upper = ma + num_std * std
        lower = ma - num_std * std
        return pd.DataFrame({'BB_upper': upper, 'BB_middle': ma, 'BB_lower': lower}, index=self.df.index)

    def detect_candlestick_patterns(self) -> pd.DataFrame:
        o, c, h, l = self.df['Open'], self.df['Close'], self.df['High'], self.df['Low']
        patterns = {
            'Doji': np.isclose(o, c, atol=(h - l) * 0.1),
            'Hammer': (abs(c - o) < (h - l) * 0.3) & ((np.minimum(o, c) - l) > abs(c - o) * 2)
        }
        prev_o, prev_c = o.shift(1), c.shift(1)
        patterns['Bullish_Engulfing'] = (c > o) & (prev_c < prev_o) & ((c - o) > (prev_o - prev_c))
        patterns['Bearish_Engulfing'] = (c < o) & (prev_c > prev_o) & ((o - c) > (prev_c - prev_o))
        return pd.DataFrame(patterns, index=self.df.index)

    def fourier_patterns(self, n_components: int = 5) -> pd.DataFrame:
        close = self.df['Close'].ffill().values
        freq = fft(close)
        filt = np.zeros_like(freq)
        idxs = np.argsort(np.abs(freq))[-n_components:]
        filt[idxs] = freq[idxs]
        recon = np.fft.ifft(filt).real
        return pd.DataFrame({'FFT_trend': recon}, index=self.df.index)

    def determine_trend(self) -> pd.Series:
        ema50 = self.ema(50)
        ema200 = self.ema(200)
        return pd.Series(np.where(ema50 > ema200, 'uptrend', 'downtrend'), index=self.df.index)

    def generate_features(self) -> pd.DataFrame:
        """
        Compute all indicators and patterns, consolidate into features DataFrame.
        """
        df_feat = pd.DataFrame(index=self.df.index)
        df_feat['SMA_14'] = self.sma(14)
        df_feat['EMA_14'] = self.ema(14)
        df_feat['RSI_14'] = self.rsi(14)
        df_feat = pd.concat([df_feat, self.macd(), self.bollinger_bands(),
                              self.detect_candlestick_patterns(), self.fourier_patterns()], axis=1)
        df_feat['Trend'] = self.determine_trend()
        return df_feat.dropna()

    def to_jsons(self,
                sample_interval = None,
                last_n = None,
                orient: str = 'records') -> dict:
        """
        Export features as JSON-serializable dict for LLM input.
        - orient: pass to DataFrame.to_dict (e.g., 'split','list','records').
        - sample_interval: include every k-th row to downsample.
        - last_n: include only the last N rows.
        """
        df = self.generate_features()
        if last_n:
            df = df.tail(last_n)
        if sample_interval:
            df = df.iloc[::sample_interval]
        return df.reset_index().to_json(orient=orient,date_format="iso")

def get_financial_data(ticker: str) -> str:
    df = yf.Ticker(ticker).history(period="1y")
    fe = FinancialAnalyzer(df)
    feats = fe.generate_features()
    feats = fe.to_jsons(sample_interval=10)
    feats = json.dumps(feats)
    return feats

# print(get_financial_data("SUZLON.NS"))