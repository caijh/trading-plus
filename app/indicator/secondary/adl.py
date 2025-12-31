import pandas as pd
import pandas_ta as ta
from scipy.stats import linregress

from app.indicator.base import Indicator


def _calculate_trend(series: pd.Series, period: int = 5) -> float:
    """
    通过计算序列在指定周期内的线性回归斜率来判断趋势。
    斜率为正表示上涨趋势，为负表示下跌趋势。
    """
    if len(series) < period:
        return 0.0

    # 选取最近的周期数据
    data = series.iloc[-period:]
    x = range(period)
    slope, intercept, r_value, p_value, std_err = linregress(x, data)
    return slope


def _trend_confirmation_adl(df: pd.DataFrame, trend: str, period: int) -> bool:
    """
    判断 ADL 与价格走势是否同步。
    - 价格和 ADL 趋势都为正（上涨确认）
    - 价格和 ADL 趋势都为负（下跌确认）
    """
    adl_series = ta.ad(df['high'], df['low'], df['close'], df['volume'])
    price_series = df['close']

    # 计算价格和 ADL 的趋势斜率
    adl_slope = _calculate_trend(adl_series, period)
    price_slope = _calculate_trend(price_series, period)
    if trend == 'bullish':
        return adl_slope > 0 and price_slope > 0
    elif trend == 'bearish':
        return adl_slope < 0 and price_slope < 0
    return False


def _divergence_adl(df: pd.DataFrame, divergence: str, period: int) -> bool:
    """
    判断 ADL 与价格走势是否背离。

    参数:
    - signal_type: 'bullish'（看涨背离）或 'bearish'（看跌背离）。
    - period: 用于计算趋势的周期。
    """
    adl_series = ta.ad(df['high'], df['low'], df['close'], df['volume'])
    price_series = df['close']

    # 计算价格和 ADL 的趋势斜率
    adl_slope = _calculate_trend(adl_series, period)
    price_slope = _calculate_trend(price_series, period)

    if divergence == 'bullish':
        # 看涨底背离：价格下跌（斜率<0）但 ADL 上涨（斜率>0）
        return price_slope < 0 < adl_slope
    elif divergence == 'bearish':
        # 看跌顶背离：价格上涨（斜率>0）但 ADL 下跌（斜率<0）
        return price_slope > 0 > adl_slope

    return False


class ADL(Indicator):

    def __init__(self, signal, window=5):
        """
        初始化 ADL 对象。

        参数:
        - signal: 指示信号类型，1代表买入信号，-1代表卖出信号。
        - window: 用于计算趋势的周期。
        """
        self.signal = signal
        self.label = 'ADL'
        self.weight = 1
        self.window = window

    def match(self, stock, df, trending, direction):
        """
        根据给定的数据判断是否满足 ADL 买入或卖出信号。

        参数:
        - stock: 股票信息。
        - df: 包含股票数据的 DataFrame。
        - trending: 股票价格趋势。
        - direction: 指示需要检测的信号方向，'UP'或'DOWN'。

        返回:
        - 如果满足信号则返回True，否则返回False。
        """
        # 检查数据是否足够计算 ADL
        if df is None or len(df) < self.window + 1:
            return False

        # 检查最新成交量
        latest_volume = float(df.iloc[-1]['volume'])
        if not latest_volume > 0:
            return False

        # 判断买入信号 (signal == 1)
        if self.signal == 1:
            if direction == 'UP':
                # 上涨趋势确认：价格和 ADL 同步上涨
                return _trend_confirmation_adl(df, 'bullish', self.window)
            elif direction == 'DOWN':
                # 看涨底背离：价格下跌但 ADL 上涨
                return _divergence_adl(df, 'bullish', self.window)

        # 判断卖出信号 (signal == -1)
        elif self.signal == -1:
            if direction == 'UP':
                # 看跌顶背离：价格上涨但 ADL 下跌
                return _divergence_adl(df, 'bearish', self.window)
            elif direction == 'DOWN':
                # 下跌趋势确认：价格和 ADL 同步下跌
                return _trend_confirmation_adl(df, 'bearish', self.window)

        return False
