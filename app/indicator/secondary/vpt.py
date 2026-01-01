import pandas as pd

from app.indicator.base import Indicator


def _vpt(df: pd.DataFrame) -> pd.Series:
    """
    计算VPT (Volume Price Trend) 指标。
    VPT = 前一日VPT + 今日成交量 * (今日收盘价 - 昨日收盘价) / 昨日收盘价
    """
    close = df['close']
    volume = df['volume']
    vpt_series = pd.Series(index=df.index, dtype='float64')
    vpt_series.iloc[0] = 0

    for i in range(1, len(df)):
        price_change_ratio = (close.iloc[i] - close.iloc[i - 1]) / close.iloc[i - 1]
        vpt_series.iloc[i] = vpt_series.iloc[i - 1] + volume.iloc[i] * price_change_ratio

    return vpt_series


class VPT(Indicator):

    def __init__(self, signal, window=5):
        """
        初始化 VPT 对象。

        参数:
        - signal: 指示信号类型，1代表买入信号，-1代表卖出信号。
        - window: 用于计算趋势的周期。
        """
        self.signal = signal
        self.label = 'VPT'
        self.weight = 1
        self.window = window

    def match(self, stock, df, trending, direction):
        """
        根据给定的数据判断是否满足 VPT 买入或卖出信号。

        参数:
        - stock: 股票信息。
        - df: 包含股票数据的 DataFrame。
        - trending: 股票价格趋势。
        - direction: 指示需要检测的信号方向，'UP'或'DOWN'。

        返回:
        - 如果满足信号则返回True，否则返回False。
        """
        # 检查数据是否足够计算 VPT
        if df is None or len(df) < self.window + 1:
            return False

        # 检查最新成交量
        latest_volume = float(df.iloc[-1]['volume'])
        if not latest_volume > 0:
            return False
        vpt_series = _vpt(df)
        cur_vpt = vpt_series.iloc[-1]
        prev_vpt = vpt_series.iloc[-2]
        # 判断买入信号 (signal == 1)
        if self.signal == 1:
            return cur_vpt > prev_vpt

        # 判断卖出信号 (signal == -1)
        elif self.signal == -1:
            return cur_vpt < prev_vpt

        return False
