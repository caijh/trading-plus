import pandas_ta as ta

from app.calculate.service import upping_trending, downing_trending
from app.indicator.base import Indicator


def _trend_confirmation(obv_series, trend, period=5):
    """
    判断 OBV 的趋势确认信号
    通过计算OBV在周期内的线性回归斜率来判断趋势，更具鲁棒性。
    """
    if trend == 'bullish':
        # 预期 OBV 上涨，斜率应为正
        return upping_trending(obv_series)
    elif trend == 'bearish':
        # 预期 OBV 下跌，斜率应为负
        return downing_trending(obv_series)

    return False


def _divergence(obv_series, divergence):
    """
    判断 OBV 的背离信号
    通过比较价格和OBV在周期内的变化来识别背离，简单且有效。
    """

    if divergence == 'bullish':
        # 底背离：价格下跌但OBV上涨，暗示买盘力量增强
        return upping_trending(obv_series)

    elif divergence == 'bearish':
        # 顶背离：价格上涨但OBV下跌，暗示卖盘力量增强
        return downing_trending(obv_series)

    return False


class OBV(Indicator):

    def __init__(self, signal):
        """
        初始化OBV对象。

        参数:
        - signal: 指示信号类型，1代表买入信号，其他值代表卖出信号。
        """
        self.signal = signal
        self.label = 'OBV'
        self.weight = 1

    def match(self, stock, df, trending, direction):
        """
        根据给定的数据判断是否满足OBV买入或卖出信号。

        参数:
        - stock: 股票信息，未在本函数中使用。
        - prices: 价格信息，未在本函数中使用。
        - df: 包含股票数据的DataFrame，包括['close'（收盘价）和 'volume'（成交量）]列。

        返回:
        - 如果满足买入或卖出信号则返回True，否则返回False。
        """
        # 获取最新价格信息
        price = df.iloc[-1]
        # 提取最新成交量并检查是否为正值
        latest_volume = float(price['volume'])
        if not latest_volume > 0:
            # 如果成交量为负，则不进行后续判断，返回False
            return False

        # 计算 OBV 指标
        obv_series = ta.obv(df['close'], df['volume'])
        # 判断买入信号
        if self.signal == 1:
            if direction == 'UP':
                # 上涨确认
                return _trend_confirmation(obv_series, trend='bullish')
            elif direction == 'DOWN':
                # 下跌背离
                return _divergence(obv_series, divergence='bullish')
        elif self.signal == -1:
            if direction == 'UP':
                # 上涨背离
                return _divergence(obv_series, divergence='bearish')
            elif direction == 'DOWN':
                # 下跌确认
                return _trend_confirmation(obv_series, trend='bearish')
        return False
