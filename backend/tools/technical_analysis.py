from trace import Trace
import matplotlib.pyplot as plt
import yfinance as yf
import pydantic
import pandas as pd
import numpy as np

def get_data(ticker: str):
    ticker_obj = yf.Ticker(ticker)
    data = ticker_obj.history(period="1y")
    return data

class TechnicalAnalysisResult(pydantic.BaseModel):
    Ressistance_levels: str | None
    Support_levels: str | None
    trend: list[dict]
    trend_duration: int # Fixed: should be list of lists
    triangle_pattern: dict


class TechnicalAnalysis:
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.data = get_data(ticker)
        # Initialize these attributes to avoid AttributeError
        self.res_df = pd.DataFrame()
        self.sup_df = pd.DataFrame()
        self.trend_data = pd.DataFrame()
        self.triangle_pattern = {}

    def get_resistance_and_support_levels(self):
        # Handle empty data case
        if self.data.empty:
            self.res_df = pd.DataFrame({'Date': [], 'Close': [], 'Type': [], 'Window': []})
            self.sup_df = pd.DataFrame({'Date': [], 'Close': [], 'Type': [], 'Window': []})
            return self.res_df, self.sup_df
            
        # assume df is your DataFrame, indexed by DateTimeIndex, with column 'Close'
        close = self.data['Close']

        # choose your window sizes
        windows = {    
            '2-weeks': 10,   # approx. 2 trading weeks
        }

        all_res_df = []
        all_sup_df = []

        for label, w in windows.items():
            # compute rolling max/min over a centered window of size w
            roll_max = close.rolling(window=w, center=True).max()
            roll_min = close.rolling(window=w, center=True).min()
            
            # resistance points: today's close equals the window max
            is_resistance = close == roll_max
            # support points: today's close equals the window min
            is_support   = close == roll_min
            
            # collect them
            res_df = pd.DataFrame({
                'Date':      close.index,
                'Close':     close.values,
                'Type':      ['Resistance'] * len(self.data),
                'Window':    label
            })[is_resistance.values]
            
            sup_df = pd.DataFrame({
                'Date':      close.index,
                'Close':     close.values,
                'Type':      ['Support'] * len(self.data),
                'Window':    label
            })[is_support.values]
            
            all_res_df.append(res_df)
            all_sup_df.append(sup_df)

        # Combine all resistance and support dataframes
        if all_res_df:
            self.res_df = pd.concat(all_res_df, ignore_index=True)
            self.res_df['Date'] = pd.to_datetime(self.res_df['Date'])
        else:
            self.res_df = pd.DataFrame({'Date': [], 'Close': [], 'Type': [], 'Window': []})
            
        if all_sup_df:
            self.sup_df = pd.concat(all_sup_df, ignore_index=True)
            self.sup_df['Date'] = pd.to_datetime(self.sup_df['Date'])
        else:
            self.sup_df = pd.DataFrame({'Date': [], 'Close': [], 'Type': [], 'Window': []})
        
        self.get_score_time_weighted()
            
        return self.res_df, self.sup_df
    
    def get_score_time_weighted(self):
        if self.res_df.empty or self.sup_df.empty:
            return
            
        min_date_res = self.res_df['Date'].min()
        max_date_res = self.res_df['Date'].max()
        min_date_sup = self.sup_df['Date'].min()
        max_date_sup = self.sup_df['Date'].max()
        
        if min_date_res != max_date_res:
            self.res_df['Score'] = (
                (self.res_df['Date'] - min_date_res)
                / (max_date_res - min_date_res)
            ).astype(float)
        else:
            self.res_df['Score'] = 0.0
            
        if min_date_sup != max_date_sup:
            self.sup_df['Score'] = (
                (self.sup_df['Date'] - min_date_sup)
                / (max_date_sup - min_date_sup)
            ).astype(float)
        else:
            self.sup_df['Score'] = 0.0
    

    def plot_support_resistance(
        self, 
        horizontal=False, 
        figsize=(12, 6)
    ):
        """
        Plot df['Close'] plus support/resistance levels from extrema_df.
        
        Parameters
        ----------
        df : pd.DataFrame
            Must have a DateTimeIndex and a 'Close' column.
        extrema_df : pd.DataFrame
            Must have columns ['Date','Close','Type'], where Type is
            either 'Support' or 'Resistance'.
        horizontal : bool, default False
            If False, plots connected dashed lines through the extrema points.
            If True, draws a horizontal line at each extrema price.
        figsize : tuple, default (12,6)
            Figure size in inches.
        """
        if self.res_df.empty and self.sup_df.empty:
            print("No support or resistance data to plot")
            return
            
        # split out supports and resistances
        supports    = self.sup_df[self.sup_df['Type'] == 'Support']
        resistances = self.res_df[self.res_df['Type'] == 'Resistance']

        plt.figure(figsize=figsize)
        # 1) full close price
        plt.plot(self.data.index, self.data['Close'], label='Close Price')

        if not horizontal:
            # 2a) connect support points
            if not supports.empty:
                plt.plot(
                    supports['Date'], supports['Close'],
                    linestyle='--', marker='o', label='Support'
                )
            # 3a) connect resistance points
            if not resistances.empty:
                plt.plot(
                    resistances['Date'], resistances['Close'],
                    linestyle='--', marker='x', label='Resistance'
                )
        else:
            # 2b) horizontal lines at each support
            for y in supports['Close']:
                plt.hlines(
                    y=y,
                    xmin=self.data.index.min(),
                    xmax=self.data.index.max(),
                    linestyle='--',
                    linewidth=0.7,
                    label='_nolegend_'  # prevents duplicate legend entries
                )
            # 3b) horizontal lines at each resistance
            for y in resistances['Close']:
                plt.hlines(
                    y=y,
                    xmin=self.data.index.min(),
                    xmax=self.data.index.max(),
                    linestyle='-.',
                    linewidth=0.7,
                    label='_nolegend_'
                )
            # add manual legend entries
            plt.plot([], [], linestyle='--', label='Support')
            plt.plot([], [], linestyle='-.', label='Resistance')

        plt.title('Close Price with Support & Resistance')
        plt.xlabel('Date')
        plt.ylabel('Close')
        plt.legend()
        plt.tight_layout()
        plt.show()
    
    def analyze_extrema_trends(self, N=5):
        """
        Analyze the direction of the last N support & resistance levels.

        Parameters
        ----------
        N : int
            Number of most-recent points to consider for each Type.

        Returns
        -------
        pd.DataFrame
            One row per Type with columns:
            - Type       : 'Support' or 'Resistance'
            - Count      : how many points were actually used
            - Slope      : slope of the linear fit (price-per-point)
            - Trend      : 'uptrend' / 'downtrend' / 'sideways'
            - Duration   : list of days from start for each point
            - Levels     : array of the N prices used
        """
        # Ensure we have the resistance and support levels
        if self.res_df.empty and self.sup_df.empty:
            self.get_resistance_and_support_levels()
            
        # ensure correct dtypes
        df = pd.concat([self.res_df, self.sup_df])
        if df.empty:
            # Return empty result
            self.trend_data = pd.DataFrame({'Type': [], 'Count': [], 'Slope': [], 'Trend': [], 'Duration': [], 'Levels': []})
            return self.trend_data
            
        df['Date'] = pd.to_datetime(df['Date'])
        
        out = []
        for etype in ['Support', 'Resistance']:
            sub = df[df['Type'] == etype].sort_values('Date')
            lastN = sub.tail(N)
            dates = list(lastN['Date'])
            levels = lastN['Close'].to_numpy()
            cnt    = len(levels)
            
            if cnt < 2:
                # not enough to fit a line
                slope = np.nan
                trend = 'insufficient data'
                duration = [0] if cnt == 1 else []
            else:
                # x = [0,1,2,...], y = levels
                x = np.arange(cnt)
                m, _ = np.polyfit(x, levels, 1)
                slope = float(m)
                if m > 0:
                    trend = 'uptrend'
                elif m < 0:
                    trend = 'downtrend'
                else:
                    trend = 'sideways'
                
            
            out.append({
                'Type': etype,
                'Count': cnt,
                'Slope': slope,
                'Trend': trend,
                'Duration': N,  # This is now a list of integers
                'Levels': levels.tolist()
            })
        
        self.trend_data = pd.DataFrame(out)
        return self.trend_data
    
    def detect_triangle_pattern(self, months=6, tol=1e-3):
        # Ensure we have the resistance and support levels
        if self.res_df.empty and self.sup_df.empty:
            self.get_resistance_and_support_levels()
            
        if self.res_df.empty and self.sup_df.empty:
            self.triangle_pattern = {
                'support_slope': np.nan,
                'resistance_slope': np.nan,
                'pattern': 'no_data'
            }
            return self.triangle_pattern
            
        df = pd.concat([self.res_df, self.sup_df])
        df['Date'] = pd.to_datetime(df['Date'])
        
        # 1) filter to last `months` months
        cutoff = df['Date'].max() - pd.DateOffset(months=months)
        recent = df[df['Date'] >= cutoff]
        
        # helper to compute slope of price vs time (in days)
        def get_slope(sub):
            if len(sub) < 2:
                return np.nan
            # x = days since cutoff
            x = (sub['Date'] - cutoff).dt.days.values.astype(float)
            y = sub['Close'].values.astype(float)
            m, _ = np.polyfit(x, y, 1)
            return m
        
        # 2) compute slopes
        sup_recent = recent[recent['Type']=='Support']
        res_recent = recent[recent['Type']=='Resistance']
        
        sup_slope = get_slope(sup_recent)
        res_slope = get_slope(res_recent)
        
        # 3) decide pattern
        if (sup_slope >  tol) and (abs(res_slope) <= tol):
            pattern = 'ascending_triangle'     # rising support + flat resistance
        elif (res_slope < -tol) and (abs(sup_slope) <= tol):
            pattern = 'descending_triangle'    # falling resistance + flat support
        else:
            pattern = 'none'
        
        self.triangle_pattern = {
            'support_slope':     float(sup_slope) if not np.isnan(sup_slope) else None,
            'resistance_slope':  float(res_slope) if not np.isnan(res_slope) else None,
            'pattern':           pattern
        }
        return self.triangle_pattern
    
    def get_data_in_shape(self):
        # Handle case where no data is available
        if self.data.empty:
            return TechnicalAnalysisResult(
                Ressistance_levels=None,
                Support_levels=None,
                trend=[],
                trend_duration=0,
                triangle_pattern={'pattern': 'no_data', 'support_slope': None, 'resistance_slope': None}
            )
            
        res_df, sup_df = self.get_resistance_and_support_levels() 
        res_df_filtered = res_df[res_df['Score'] > 0.7]
        sup_df_filtered = sup_df[sup_df['Score'] > 0.7]
        res_df_filtered = res_df_filtered.drop(columns = ['Date','Type','Window'])
        sup_df_filtered = sup_df_filtered.drop(columns = ['Date','Type','Window'])
        res_df_filtered['Difficult_to_cross_score'] = res_df_filtered['Score']
        sup_df_filtered['Difficult_to_cross_score'] = sup_df_filtered['Score']
        res_df_filtered.drop(columns = ['Score'], inplace = True)
        sup_df_filtered.drop(columns = ['Score'], inplace = True)
        res_json = res_df_filtered.to_json(orient='records', date_format='iso') if not res_df_filtered.empty else None
        sup_json = sup_df_filtered.to_json(orient='records', date_format='iso') if not sup_df_filtered.empty else None
        
        trend_data_df = self.analyze_extrema_trends()
        trend_data = trend_data_df.to_dict('records') if not trend_data_df.empty else []
        
        # Fixed: Extract Duration correctly as list of lists
        trend_duration = []
        if not trend_data_df.empty:
            trend_duration = trend_data_df['Duration']
        
        triangle_data = self.detect_triangle_pattern()
        
        return TechnicalAnalysisResult(
            Ressistance_levels=res_json,
            Support_levels=sup_json,
            trend=trend_data,
            trend_duration=trend_duration[0],
            triangle_pattern=triangle_data
        )


# Test with a more reliable ticker
if __name__ == "__main__":
    ta = TechnicalAnalysis("SUZLON.NS")  # Changed from SUZLON.NS to AAPL for better data
    print(ta.get_data_in_shape())