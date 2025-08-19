import pandas as pd
import pandas_ta as ta

from indicator.base import Indicator


def _pvi_divergence(pvi_series, divergence):
    """
    判断 PVI 的背离信号
    """
    # PVI 下降，表明在放量情况下股价下跌，是熊市信号
    latest = pvi_series.iloc[-1]
    prev = pvi_series.iloc[-2]
    if divergence == 'bullish':
        # 底背离：价格下跌但 PVI 上涨，暗示买盘力量增强
        return latest > prev
    elif divergence == 'bearish':
        # 顶背离：价格上涨但 PVI 下跌，暗示卖盘力量增强
        return latest < prev

    return False


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
        - direction: 预期交易方向，'UP'代表看涨，'DOWN'代表看跌。

        返回:
        - 如果满足买入或卖出信号则返回True，否则返回False。
        """
        # 确保数据完整性
        if not all(col in df for col in ['close', 'volume']):
            return False

        # 计算 PVI 指标
        # pandas-ta 的 pvi() 函数返回一个包含 PVI 和 PVI_SMA 的 DataFrame
        pvi_df = ta.pvi(close=df['close'], volume=df['volume'])
        pvi_series = pvi_df[f'PVI_{pvi_df.columns[0].split("_")[1]}']

        if pvi_series.empty:
            return False

        # 根据信号类型和方向判断
        if self.signal == 1:
            if direction == 'UP':
                # 看涨趋势确认: PVI 在上涨
                return Indicator.trend_confirmation(pvi_series, "bullish")
            elif direction == 'DOWN':
                # 看涨背离: 价格下跌但 PVI 上升（底部背离）
                return Indicator.divergence(pvi_series, divergence="bullish")
        elif self.signal == -1:
            if direction == 'UP':
                # 看跌背离: 价格上涨但 PVI 下跌（顶部背离）
                return Indicator.divergence(pvi_series, divergence="bearish")
            elif direction == 'DOWN':
                # 看跌趋势确认: PVI 在下跌
                return Indicator.trend_confirmation(pvi_series, "bearish")

        return False
