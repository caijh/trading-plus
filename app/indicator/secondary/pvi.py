import pandas as pd
import pandas_ta as ta

from app.indicator.base import Indicator


class PVI(Indicator):
    def __init__(self, signal):
        """
        初始化 PVI 对象。

        参数:
        - signal: 指示信号类型，1代表买入信号，其他值代表卖出信号。
        """
        self.signal = signal
        self.label = 'PVI'
        self.weight = 1

    def match(self, stock, df: pd.DataFrame, trending, direction):
        """
        根据给定的数据判断是否满足 PVI 买入或卖出信号。

        参数:
        - stock: 股票信息，未在本函数中使用。
        - df: 包含股票数据的DataFrame，包括['close'（收盘价）和 'volume'（成交量）]列。
        - trending: 股票的整体趋势（例如：强势上涨或下跌）。
        - direction: 预期交易方向，'UP'代表看涨，'DOWN' 代表看跌。

        返回:
        - 如果满足买入或卖出信号则返回True，否则返回False。
        """
        if len(df) < 255:
            return False
        # 确保数据完整性
        if not all(col in df for col in ['close', 'volume']):
            return False

        # 计算 PVI 指标
        # pandas-ta 的 pvi() 函数返回一个包含 PVI 和 PVI_SMA 的 DataFrame
        pvi_df = ta.pvi(close=df['close'], volume=df['volume'])

        if pvi_df is None or pvi_df.empty:
            return False

        pvi_series = pvi_df['PVI']
        latest = pvi_series.iloc[-1]
        prev = pvi_series.iloc[-2]
        if self.signal == 1:
            return latest > prev
        elif self.signal == -1:
            return latest < prev
        return False
