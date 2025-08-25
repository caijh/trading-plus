import pandas as pd
import pandas_ta as ta

from indicator.base import Indicator


def _nvi_trend_confirmation(nvi_series, trend):
    """
    判断 NVI 的趋势确认信号
    """
    # NVI 上升，表明在缩量情况下股价上涨，是牛市信号
    latest = nvi_series.iloc[-1]
    prev = nvi_series.iloc[-2]
    if trend == "bullish":
        return latest > prev
    elif trend == "bearish":
        return latest < prev

    return False


def _nvi_divergence(nvi_series, divergence):
    """
    判断 NVI 的背离信号
    """
    # NVI 下降，表明在缩量情况下股价下跌，是熊市信号
    latest = nvi_series.iloc[-1]
    prev = nvi_series.iloc[-2]
    if divergence == 'bullish':
        # 底背离：价格下跌但NVI上涨，暗示买盘力量增强
        return latest > prev
    elif divergence == 'bearish':
        # 顶背离：价格上涨但NVI下跌，暗示卖盘力量增强
        return latest < prev

    return False


class NVI(Indicator):
    def __init__(self, signal):
        """
        初始化 NVI 对象。

        参数:
        - signal: 指示信号类型，1代表买入信号，其他值代表卖出信号。
        """
        self.signal = signal
        self.label = 'NVI'
        self.weight = 1

    def match(self, stock, df: pd.DataFrame, trending, direction):
        """
        根据给定的数据判断是否满足 NVI 买入或卖出信号。

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

        # 计算 NVI 指标，这里只使用 NVI 序列本身
        # pandas-ta 的 nvi() 函数返回一个包含 NVI 和 NVI_SMA 的 DataFrame
        nvi_series = ta.nvi(close=df['close'], volume=df['volume'])
        nvi_sma_series = ta.sma(nvi_series, length=10)

        if nvi_series.empty:
            return False
        last_nvi = nvi_series.iloc[-1]
        last_nvi_sma = nvi_sma_series.iloc[-1]
        # 根据信号类型和方向判断
        if self.signal == 1:
            # 获取最新的 NVI 和 NVI_SMA 值

            if direction == 'UP':
                # 看涨趋势确认: NVI 在上涨
                return last_nvi > last_nvi_sma and _nvi_trend_confirmation(nvi_series, "bullish")
            elif direction == 'DOWN':
                # 看涨背离: 价格下跌但 NVI 上升（底部背离）
                return last_nvi > last_nvi_sma and _nvi_divergence(nvi_series, divergence="bullish")
        elif self.signal == -1:
            if direction == 'UP':
                # 看跌背离: 价格上涨但 NVI 下跌（顶部背离）
                return last_nvi < last_nvi_sma and _nvi_divergence(nvi_series, divergence="bearish")
            elif direction == 'DOWN':
                # 看跌趋势确认: NVI 在下跌
                return last_nvi < last_nvi_sma and _nvi_trend_confirmation(nvi_series, "bearish")

        return False
